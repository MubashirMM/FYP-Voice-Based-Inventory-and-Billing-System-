from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os
import shutil

from myapp.database.session import get_db
from myapp.models.sales import Sale
from myapp.models.report import Report
from myapp.models.user import User
from myapp.utils.security import get_current_user

from myapp.schemas.report import ReportResponse
from myapp.crud.report import create_report, delete_report, get_reports
from myapp.utils.report_generator import generate_report_files

router = APIRouter(prefix="/reports", tags=["Reports"])

BASE_DIR = "reports_storage"


# =========================
# GENERATE REPORT
# =========================
@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get all sales
    stmt = (
        select(Sale)
        .options(selectinload(Sale.item))
        .where(Sale.user_id == current_user.user_id)
    )

    res = await db.execute(stmt)
    sales = res.scalars().all()

    if not sales:
        raise HTTPException(status_code=404, detail="فروخت کا ڈیٹا نہیں ملا")

    # 2. Create report (DB)
    report = await create_report(
        db,
        user_id=current_user.user_id,
        title="مکمل فروخت رپورٹ",
        kpi_summary={}
    )

    # 3. Generate files
    result = await generate_report_files(report.report_id, sales)

    # 4. Save KPI
    report.kpi_summary = result["kpi"]

    await db.commit()
    await db.refresh(report)

    return report


# =========================
# DOWNLOAD REPORT
# =========================
@router.get("/download/{report_id}")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check report exists
    stmt = select(Report).where(
        Report.report_id == report_id,
        Report.user_id == current_user.user_id
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")

    folder = f"{BASE_DIR}/report_{report_id}"

    if not os.path.exists(folder):
        raise HTTPException(status_code=404, detail="فائلز موجود نہیں ہیں")

    # Return file paths (frontend will download)
    return {
        "pdf": f"{folder}/dashboard.pdf",
        "excel": f"{folder}/report.xlsx"
    }


# =========================
# DELETE REPORT
# =========================
@router.delete("/{report_id}")
async def delete_report_endpoint(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await delete_report(db, report_id, current_user.user_id)

    if not success:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")

    # Also delete files
    folder = f"{BASE_DIR}/report_{report_id}"
    if os.path.exists(folder):
        shutil.rmtree(folder)

    return {"message": "رپورٹ کامیابی سے حذف کر دی گئی"}


# =========================
# LIST REPORTS (OPTIONAL)
# =========================
@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = await get_reports(db, current_user.user_id)

    if not reports:
        raise HTTPException(status_code=404, detail="کوئی رپورٹ موجود نہیں")

    return reports