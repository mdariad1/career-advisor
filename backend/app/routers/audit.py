from fastapi import APIRouter, Depends
from ..dependencies import require_admin

router = APIRouter()


@router.post("/run")
async def run_audit(admin: dict = Depends(require_admin)):
    """
    Admin-only. Joins recommendations + user_demographics, computes disparate
    impact ratios and equal opportunity scores across gender, age_group,
    field_of_study, and socioeconomic_background. Writes snapshot to bias_audit.
    """
    raise NotImplementedError


@router.get("/reports")
async def list_reports(admin: dict = Depends(require_admin)):
    raise NotImplementedError


@router.get("/reports/{report_id}")
async def get_report(report_id: str, admin: dict = Depends(require_admin)):
    raise NotImplementedError
