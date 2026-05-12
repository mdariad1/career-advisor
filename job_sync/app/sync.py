"""
Job sync logic — no business logic implemented yet.
Steps per cycle (see chapter3.tex Module 5):
  1. For each industry in career taxonomy, GET /v1/jobs from JobDataPool
  2. Pass skill strings through NLP Service skill normalisation
  3. Upsert normalised records into jobs_snapshot keyed on job_id
  4. Mark listings older than 14 days as stale
"""
import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_sync_cycle() -> None:
    logger.info("Job sync cycle started")
    raise NotImplementedError
