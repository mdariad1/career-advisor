"""
Job sync cycle — JobDataPool API → NLP skill normalisation → jobs_snapshot upsert.

Steps per cycle (chapter3.tex Module 5):
  1. For each industry in career taxonomy, GET /v1/jobs from JobDataPool
  2. Pass skill strings through NLP Service /classify for thematic normalisation
  3. Upsert normalised records into jobs_snapshot keyed on job_id
  4. Mark listings older than job_stale_days days as stale
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, UTC, timedelta

import httpx

from .config import settings
from .database import jobs_snapshot_col

logger = logging.getLogger(__name__)

# Industry slugs that map to our career taxonomy (mirrors seed.py CAREER_ARCHETYPES career_ids)
_INDUSTRIES = [
    "software_engineer",
    "data_scientist",
    "ux_designer",
    "product_manager",
    "mechanical_engineer",
    "financial_analyst",
    "biomedical_researcher",
    "educator",
]

_JOBDATAPOOL_BASE = "https://api.jobdatapool.com/v1"
_PAGE_SIZE = 50
_MAX_PAGES = 5          # cap at 250 jobs per industry per cycle
_SKILL_BATCH = 10       # max skills to join per NLP classify call


# ── JobDataPool API ───────────────────────────────────────────────────────────

async def _fetch_jobs_for_industry(
    client: httpx.AsyncClient,
    industry: str,
    country_code: str,
) -> list[dict]:
    """Fetch up to _MAX_PAGES pages of jobs for one industry from JobDataPool."""
    jobs: list[dict] = []
    for page in range(1, _MAX_PAGES + 1):
        try:
            resp = await client.get(
                f"{_JOBDATAPOOL_BASE}/jobs",
                params={
                    "country": country_code,
                    "category": industry,
                    "page": page,
                    "per_page": _PAGE_SIZE,
                },
                headers={"Authorization": f"Bearer {settings.jobdatapool_api_key}"},
                timeout=15.0,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("JobDataPool HTTP %s for industry=%s page=%d", exc.response.status_code, industry, page)
            break
        except httpx.RequestError as exc:
            logger.warning("JobDataPool request error for industry=%s page=%d: %s", industry, page, exc)
            break

        data = resp.json()
        # API may return a bare list or a dict with a "jobs" / "data" key
        if isinstance(data, list):
            page_jobs = data
        else:
            page_jobs = data.get("jobs") or data.get("data") or []
        jobs.extend(page_jobs)

        # Stop if we got fewer results than page size (last page)
        if len(page_jobs) < _PAGE_SIZE:
            break

    logger.info("Fetched %d jobs for industry=%s", len(jobs), industry)
    return jobs


# ── NLP skill normalisation ───────────────────────────────────────────────────

async def _normalise_skills(
    client: httpx.AsyncClient,
    raw_skills: list[str],
) -> list[str]:
    """
    Map a list of raw skill strings to thematic labels via NLP /embed + /classify.
    Returns a deduplicated list of thematic labels (e.g. ["technical", "analytical"]).
    Falls back to empty list if the NLP service is unavailable.
    """
    if not raw_skills:
        return []

    # Join up to _SKILL_BATCH skills as a single sentence for classification
    text = ", ".join(raw_skills[:_SKILL_BATCH])

    try:
        # Step 1: embed
        embed_resp = await client.post(
            f"{settings.nlp_service_url}/embed/",
            json={"text": text},
            timeout=10.0,
        )
        embed_resp.raise_for_status()
        embedding = embed_resp.json()["embedding"]

        # Step 2: classify
        cls_resp = await client.post(
            f"{settings.nlp_service_url}/classify/",
            json={"embedding": embedding},
            timeout=10.0,
        )
        cls_resp.raise_for_status()
        return cls_resp.json().get("labels", [])

    except Exception as exc:
        logger.debug("NLP normalisation unavailable (%s) — skills left unclassified", exc)
        return []


# ── MongoDB upsert ────────────────────────────────────────────────────────────

def _parse_salary(job: dict) -> str | None:
    """Build a human-readable salary string from JobDataPool salary fields."""
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    currency = job.get("currency", "")
    if salary_min and salary_max:
        return f"{currency}{salary_min:,} – {currency}{salary_max:,}"
    if salary_min:
        return f"From {currency}{salary_min:,}"
    return job.get("salary_range")  # some APIs return a pre-formatted string


async def _upsert_job(col, job: dict, industry: str, nlp_labels: list[str], now: datetime) -> None:
    """Upsert a single job document into jobs_snapshot."""
    job_id: str = str(job.get("id") or job.get("job_id") or "")
    if not job_id:
        return

    raw_skills: list[str] = job.get("skills") or []

    doc = {
        "job_id": job_id,
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "industry": industry,
        "country_code": job.get("country") or job.get("country_code") or "",
        "salary_range": _parse_salary(job),
        "skills": nlp_labels,
        "raw_skills": raw_skills,
        "is_stale": False,
        "synced_at": now,
    }

    await col.update_one(
        {"job_id": job_id},
        {"$set": doc},
        upsert=True,
    )


# ── Staleness sweep ───────────────────────────────────────────────────────────

async def _mark_stale(col, cutoff: datetime) -> int:
    """Mark all listings not updated since `cutoff` as stale. Returns affected count."""
    result = await col.update_many(
        {"synced_at": {"$lt": cutoff}, "is_stale": False},
        {"$set": {"is_stale": True}},
    )
    return result.modified_count


# ── Main sync cycle ───────────────────────────────────────────────────────────

async def run_sync_cycle() -> None:
    """Full sync cycle: fetch → normalise → upsert → mark stale."""
    logger.info("Job sync cycle started — country=%s", settings.target_country_code)
    now = datetime.now(UTC)
    col = jobs_snapshot_col()
    total_upserted = 0

    async with httpx.AsyncClient() as http:
        for industry in _INDUSTRIES:
            # Rate-limit: pause between industry queries
            if total_upserted > 0:
                await asyncio.sleep(settings.inter_query_delay_seconds)

            jobs = await _fetch_jobs_for_industry(http, industry, settings.target_country_code)

            for job in jobs:
                raw_skills: list[str] = job.get("skills") or []
                nlp_labels = await _normalise_skills(http, raw_skills)
                await _upsert_job(col, job, industry, nlp_labels, now)
                total_upserted += 1

    # Mark listings not refreshed this cycle as stale
    cutoff = now - timedelta(days=settings.job_stale_days)
    stale_count = await _mark_stale(col, cutoff)

    logger.info(
        "Job sync cycle complete — upserted=%d stale_marked=%d",
        total_upserted,
        stale_count,
    )
