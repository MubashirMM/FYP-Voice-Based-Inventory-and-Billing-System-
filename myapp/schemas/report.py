from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime


# =========================
# GENERATE REQUEST (NO INPUT)
# =========================
class ReportGenerateRequest(BaseModel):
    pass


# =========================
# BASE
# =========================
class ReportBase(BaseModel):
    title: str
    kpi_summary: Dict[str, Any]


# =========================
# CREATE
# =========================
class ReportCreate(ReportBase):
    pass


# =========================
# RESPONSE
# =========================
class ReportResponse(BaseModel):
    report_id: int
    title: str
    kpi_summary: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# OPTIONAL (IF YOU LIST)
# =========================
class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int