from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime


class ReportGenerateRequest(BaseModel):
    pass


class ReportBase(BaseModel):
    title: str
    kpi_summary: Dict[str, Any]


class ReportCreate(ReportBase):
    pass


class ReportResponse(BaseModel):
    report_id: int
    title: str
    kpi_summary: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int