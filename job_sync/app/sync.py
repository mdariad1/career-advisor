"""
Job sync cycle — Adzuna API → NLP skill normalisation → jobs_snapshot upsert.

Steps per cycle:
  1. For each career archetype, GET /v1/api/jobs/{country}/search/{page} from Adzuna
  2. Pass skill strings through NLP Service /classify for thematic normalisation
  3. Upsert normalised records into jobs_snapshot keyed on job_id
  4. Mark listings older than job_stale_days days as stale
"""
from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime, UTC, timedelta

import httpx

from .config import settings
from .database import jobs_snapshot_col

logger = logging.getLogger(__name__)

_ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"
_PAGE_SIZE = 50
_MAX_PAGES = 1          # 1 page × 50 results per archetype — keeps 20-country daily budget ≤ 160 req
_SKILL_BATCH = 10

# Currency symbol keyed by Adzuna country code (lowercase)
_CURRENCY = {
    "gb": "£", "us": "$", "au": "A$", "ca": "CA$", "nz": "NZ$",
    "de": "€", "fr": "€", "nl": "€", "be": "€", "es": "€",
    "it": "€", "at": "€", "ch": "CHF", "sg": "S$", "za": "R",
    "in": "₹", "br": "R$", "mx": "MX$", "pl": "zł", "ru": "₽",
}

# Maps each career archetype to the best-fit Adzuna category tag + search keyword.
# Adzuna category tags: https://api.adzuna.com/v1/api/jobs/{country}/categories
_CAREER_QUERIES: list[dict] = [
    {"career_id": "software_engineer",    "category": "it-jobs",                   "what": "software engineer"},
    {"career_id": "data_scientist",       "category": "it-jobs",                   "what": "data scientist"},
    {"career_id": "ux_designer",          "category": "creative-design-jobs",      "what": "UX designer"},
    {"career_id": "product_manager",      "category": "it-jobs",                   "what": "product manager"},
    {"career_id": "mechanical_engineer",  "category": "engineering-jobs",          "what": "mechanical engineer"},
    {"career_id": "financial_analyst",    "category": "accounting-finance-jobs",   "what": "financial analyst"},
    {"career_id": "biomedical_researcher","category": "scientific-research-jobs",  "what": "biomedical researcher"},
    {"career_id": "educator",             "category": "teaching-jobs",             "what": "teacher"},
]


# ── Adzuna API ────────────────────────────────────────────────────────────────

async def _fetch_jobs_for_archetype(
    client: httpx.AsyncClient,
    career: dict,
    country: str,
) -> list[dict]:
    """Fetch up to _MAX_PAGES pages of Adzuna jobs for one career archetype."""
    jobs: list[dict] = []
    for page in range(1, _MAX_PAGES + 1):
        try:
            resp = await client.get(
                f"{_ADZUNA_BASE}/{country}/search/{page}",
                params={
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "results_per_page": _PAGE_SIZE,
                    "what": career["what"],
                    "category": career["category"],
                    "content-type": "application/json",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Adzuna HTTP %s for career_id=%s page=%d",
                exc.response.status_code, career["career_id"], page,
            )
            break
        except httpx.RequestError as exc:
            logger.warning(
                "Adzuna request error for career_id=%s page=%d: %s",
                career["career_id"], page, exc,
            )
            break

        page_jobs: list[dict] = resp.json().get("results", [])
        jobs.extend(page_jobs)

        if len(page_jobs) < _PAGE_SIZE:
            break   # last page

    logger.info("Fetched %d jobs for career_id=%s", len(jobs), career["career_id"])
    return jobs


# ── NLP skill normalisation ───────────────────────────────────────────────────

async def _normalise_skills(
    client: httpx.AsyncClient,
    raw_skills: list[str],
) -> list[str]:
    """Classify raw skill strings to thematic labels via NLP /embed + /classify.

    Falls back to an empty list if the NLP service is unavailable.
    """
    if not raw_skills:
        return []

    text = ", ".join(raw_skills[:_SKILL_BATCH])
    try:
        embed_resp = await client.post(
            f"{settings.nlp_service_url}/embed/",
            json={"text": text},
            timeout=10.0,
        )
        embed_resp.raise_for_status()
        cls_resp = await client.post(
            f"{settings.nlp_service_url}/classify/",
            json={"embedding": embed_resp.json()["embedding"]},
            timeout=10.0,
        )
        cls_resp.raise_for_status()
        return cls_resp.json().get("labels", [])
    except Exception as exc:
        logger.debug("NLP normalisation unavailable (%s) — skills left unclassified", exc)
        return []


# ── MongoDB upsert ────────────────────────────────────────────────────────────

def _parse_salary(salary_min, salary_max, currency: str) -> str | None:
    """Build a human-readable salary string from Adzuna's numeric salary fields."""
    if salary_min and salary_max:
        return f"{currency}{int(salary_min):,} – {currency}{int(salary_max):,}"
    if salary_min:
        return f"From {currency}{int(salary_min):,}"
    if salary_max:
        return f"Up to {currency}{int(salary_max):,}"
    return None


async def _upsert_job(
    col,
    job: dict,
    career_id: str,
    country_code: str,
    currency: str,
    nlp_labels: list[str],
    now: datetime,
) -> None:
    """Upsert a single Adzuna job document into jobs_snapshot."""
    job_id: str = str(job.get("id", ""))
    if not job_id:
        return

    title = html.unescape((job.get("title") or "").strip())
    company = html.unescape(((job.get("company") or {}).get("display_name") or "").strip())
    loc_obj = job.get("location") or {}
    location = (loc_obj.get("display_name") or "").strip()
    description = (job.get("description") or "").strip()
    raw_skills: list[str] = [s.strip() for s in description.split(",") if s.strip()] if description else []

    doc = {
        "job_id": job_id,
        "title": title,
        "company": company,
        "industry": career_id,          # our internal slug — keeps recommendations compatible
        "country_code": country_code,
        "location": location,           # Adzuna display_name e.g. "London, South East England"
        "salary_range": _parse_salary(job.get("salary_min"), job.get("salary_max"), currency),
        "skills": nlp_labels,
        "raw_skills": raw_skills,
        "redirect_url": job.get("redirect_url", ""),
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
    """Full sync cycle across all configured countries: fetch → normalise → upsert → mark stale."""
    countries = [c.strip().lower() for c in settings.target_countries.split(",") if c.strip()]
    logger.info("Job sync cycle started — countries=%s", countries)

    now = datetime.now(UTC)
    col = jobs_snapshot_col()
    total_upserted = 0

    async with httpx.AsyncClient() as http:
        for country in countries:
            currency = _CURRENCY.get(country, "")
            country_code = country.upper()

            for career in _CAREER_QUERIES:
                if total_upserted > 0:
                    await asyncio.sleep(settings.inter_query_delay_seconds)

                jobs = await _fetch_jobs_for_archetype(http, career, country)

                for job in jobs:
                    desc = (job.get("description") or "").strip()
                    raw_skills = [s.strip() for s in desc.split(",") if s.strip()] if desc else []
                    nlp_labels = await _normalise_skills(http, raw_skills)
                    await _upsert_job(col, job, career["career_id"], country_code, currency, nlp_labels, now)
                    total_upserted += 1

            logger.info("Finished country=%s running_total=%d", country, total_upserted)

    cutoff = now - timedelta(days=settings.job_stale_days)
    stale_count = await _mark_stale(col, cutoff)

    logger.info(
        "Job sync cycle complete — upserted=%d stale_marked=%d",
        total_upserted,
        stale_count,
    )
