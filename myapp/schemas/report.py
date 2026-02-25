# schemas/report.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ReportGenerateRequest(BaseModel):
    """Request schema for generating a sales report"""
    item_name: str
    filters_applied: Optional[str] = None


class ReportBase(BaseModel):
    user_id: int
    item_name: str
    filters_applied: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class ReportResponse(BaseModel):
    """Response schema for report"""
    report_id: int
    user_id: int
    item_name: str
    filters_applied: Optional[str] = None
    kpi_summary: Optional[str] = None
    charts_paths: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Response schema for listing reports"""
    reports: List[ReportResponse]
    total: int
