from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone

from myapp.models.report import Report
from myapp.utils.urdu_date import convert_datetime_to_urdu, format_full_date_urdu


# =========================
# CREATE REPORT
# =========================
async def create_report(
    db: AsyncSession,
    user_id: int,
    title: str,
    kpi_summary: dict,
    table_data: dict | None = None,
    charts_static: dict | None = None,
    charts_interactive: dict | None = None
) -> Report:
    
    # Get current datetime in UTC
    now_utc = datetime.now(timezone.utc)
    
    # Convert to Urdu date components (using local time for display)
    # Convert UTC to local time first (you may want to adjust based on user's timezone)
    from datetime import timedelta
    local_now = now_utc + timedelta(hours=5)  # Pakistan time (UTC+5)
    
    urdu_date_parts = convert_datetime_to_urdu(local_now, "report")
    
    # Create full date string
    full_date_urdu = format_full_date_urdu(local_now)
    
    # Create report with Urdu date fields
    report = Report(
        user_id=user_id,
        title=title,
        filters=None,
        kpi_summary=kpi_summary,
        table_data=table_data or {},
        charts_static=charts_static or {},
        charts_interactive=charts_interactive or {},
        created_at=now_utc,  # Keep UTC in database
        # Urdu date fields for display
        report_day=urdu_date_parts.get("report_day", ""),
        report_month=urdu_date_parts.get("report_month", ""),
        report_year=urdu_date_parts.get("report_year", ""),
        report_time=urdu_date_parts.get("report_time", ""),
        report_day_name=urdu_date_parts.get("report_day_name", ""),
        report_full_date=full_date_urdu
    )

    db.add(report)
    await db.flush()   # important (get report_id)

    return report


# =========================
# GET SINGLE REPORT
# =========================
async def get_report(
    db: AsyncSession,
    report_id: int,
    user_id: int
) -> Optional[Report]:

    stmt = select(Report).where(
        Report.report_id == report_id,
        Report.user_id == user_id
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


# =========================
# GET ALL REPORTS
# =========================
async def get_reports(
    db: AsyncSession,
    user_id: int
) -> List[Report]:

    stmt = select(Report).where(Report.user_id == user_id).order_by(Report.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


# =========================
# DELETE REPORT
# =========================
async def delete_report(
    db: AsyncSession,
    report_id: int,
    user_id: int
) -> bool:

    report = await get_report(db, report_id, user_id)

    if not report:
        return False

    await db.delete(report)
    await db.commit()

    return True


# =========================
# UPDATE REPORT (Optional)
# =========================
async def update_report(
    db: AsyncSession,
    report_id: int,
    user_id: int,
    **kwargs
) -> Optional[Report]:
    
    report = await get_report(db, report_id, user_id)
    
    if not report:
        return None
    
    for key, value in kwargs.items():
        if hasattr(report, key):
            setattr(report, key, value)
    
    await db.commit()
    await db.refresh(report)
    
    return report