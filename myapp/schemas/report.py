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


from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class ReportResponse(BaseModel):
    report_id: int
    user_id: int
    title: str
    filters: Optional[Dict[str, Any]] = None
    kpi_summary: Dict[str, Any]
    table_data: Dict[str, Any]
    charts_static: Optional[Dict[str, Any]] = None
    charts_interactive: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    # Urdu date fields
    report_day: Optional[str] = None
    report_month: Optional[str] = None
    report_year: Optional[str] = None
    report_time: Optional[str] = None
    report_day_name: Optional[str] = None
    report_full_date: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int