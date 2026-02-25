from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List, Optional
from myapp.models.report import Report
from myapp.schemas.report import ReportCreate
import json

# ---------------------------
# Synchronous CRUD (optional)
# ---------------------------
def create_report(db: Session, report_data: ReportCreate, kpi_summary: dict, charts_paths: list):
    """
    Synchronous function to create a report (for sync contexts)
    """
    report = Report(
        user_id=report_data.user_id,
        item_name=report_data.item_name,
        filters_applied=report_data.filters_applied,
        kpi_summary=json.dumps(kpi_summary, ensure_ascii=False),
        charts_paths=json.dumps(charts_paths)
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_report(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.report_id == report_id).first()

def get_reports(db: Session, user_id: int) -> List[Report]:
    return db.query(Report).filter(Report.user_id == user_id).all()

def delete_report(db: Session, report_id: int) -> Optional[Report]:
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
    return report

# ---------------------------
# Async CRUD (preferred)
# ---------------------------
async def create_report_async(
    db: AsyncSession,
    user_id: int,
    item_name: str,
    kpi_summary: dict,
    charts_paths: list,
    filters_applied: Optional[str] = None
) -> Report:
    """
    Async function to create a report (for async contexts)
    """
    report = Report(
        user_id=user_id,
        item_name=item_name,
        filters_applied=filters_applied,
        kpi_summary=json.dumps(kpi_summary, ensure_ascii=False),
        charts_paths=json.dumps(charts_paths)
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def get_report_async(db: AsyncSession, report_id: int) -> Optional[Report]:
    from sqlalchemy import select
    stmt = select(Report).where(Report.report_id == report_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_reports_async(db: AsyncSession, user_id: int) -> List[Report]:
    from sqlalchemy import select
    stmt = select(Report).where(Report.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def delete_report_async(db: AsyncSession, report_id: int) -> Optional[Report]:
    from sqlalchemy import select
    stmt = select(Report).where(Report.report_id == report_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    if report:
        await db.delete(report)
        await db.commit()
    return report
