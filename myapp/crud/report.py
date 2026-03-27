from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from myapp.models.report import Report


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

    report = Report(
        user_id=user_id,
        title=title,
        filters=None,
        kpi_summary=kpi_summary,
        table_data=table_data or {},
        charts_static=charts_static or {},
        charts_interactive=charts_interactive or {}
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

    stmt = select(Report).where(Report.user_id == user_id)
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