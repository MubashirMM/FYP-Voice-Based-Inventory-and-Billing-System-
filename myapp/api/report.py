from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
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
from myapp.crud.report import create_report, delete_report, get_reports, get_report
from myapp.utils.report_generator import generate_report_files

router = APIRouter(prefix="/reports", tags=["Reports"])

BASE_DIR = "reports_storage"


# Update the generate_report function in routers/report.py

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all sales for this user
    stmt = (
        select(Sale)
        .where(Sale.user_id == current_user.user_id)
        .order_by(Sale.sale_date.desc())
    )
    
    res = await db.execute(stmt)
    sales = res.scalars().all()
    
    # Check if at least 5 sales exist
    if len(sales) < 5:
        raise HTTPException(
            status_code=400, 
            detail="رپورٹ جنریٹ کرنے کے لیے کم از کم 5 فروخت کے ریکارڈز ضروری ہیں۔ براہ کرم مزید فروخت شامل کریں۔"
        )
    
    # Check if at least 5 unique items exist
    unique_items = set()
    for sale in sales:
        unique_items.add(sale.item_name)
    
    if len(unique_items) < 5:
        raise HTTPException(
            status_code=400, 
            detail=f"رپورٹ جنریٹ کرنے کے لیے کم از کم 5 مختلف اشیاء کی فروخت ضروری ہے۔ موجودہ منفرد اشیاء: {len(unique_items)}"
        )
    
    # Create report in database
    report = await create_report(
        db,
        user_id=current_user.user_id,
        title=f"فروخت رپورٹ - {len(sales)} ریکارڈز, {len(unique_items)} اشیاء",
        kpi_summary={}
    )
    
    # Generate report files
    result = await generate_report_files(report.report_id, sales)
    
    # Check if generation had an error
    if result.get("error"):
        # Delete the report if generation failed
        await db.delete(report)
        await db.commit()
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Update report with KPI summary
    report.kpi_summary = result["kpi"]
    report.table_data = {"total_records": len(sales), "unique_items": len(unique_items)}
    
    await db.commit()
    await db.refresh(report)
    
    return report


# =========================
# DOWNLOAD REPORT (PDF)
# =========================
@router.get("/download-pdf/{report_id}")
async def download_report_pdf(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify report exists and belongs to user
    report = await get_report(db, report_id, current_user.user_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
    folder = f"{BASE_DIR}/report_{report_id}"
    pdf_path = os.path.join(folder, "dashboard.pdf")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF فائل موجود نہیں ہے")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"sales_report_{report_id}.pdf"
    )


# =========================
# DOWNLOAD REPORT (EXCEL)
# =========================
@router.get("/download-excel/{report_id}")
async def download_report_excel(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify report exists and belongs to user
    report = await get_report(db, report_id, current_user.user_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
    folder = f"{BASE_DIR}/report_{report_id}"
    excel_path = os.path.join(folder, "sales_report.xlsx")
    
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="Excel فائل موجود نہیں ہے")
    
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"sales_report_{report_id}.xlsx"
    )


# # =========================
# # DOWNLOAD REPORT (CSV)
# # =========================
# @router.get("/download-csv/{report_id}")
# async def download_report_csv(
#     report_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Verify report exists and belongs to user
#     report = await get_report(db, report_id, current_user.user_id)
    
#     if not report:
#         raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
#     folder = f"{BASE_DIR}/report_{report_id}"
#     csv_path = os.path.join(folder, "sales_export.csv")
    
#     if not os.path.exists(csv_path):
#         raise HTTPException(status_code=404, detail="CSV فائل موجود نہیں ہے")
    
#     return FileResponse(
#         csv_path,
#         media_type="text/csv",
#         filename=f"sales_report_{report_id}.csv"
#     )


# =========================
# GET ALL REPORTS
# =========================
@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = await get_reports(db, current_user.user_id)
    return reports


# =========================
# GET SINGLE REPORT
# =========================
@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = await get_report(db, report_id, current_user.user_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
    return report


# =========================
# DELETE REPORT
# =========================
@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report_endpoint(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Delete from database
    success = await delete_report(db, report_id, current_user.user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
    # Delete files
    folder = f"{BASE_DIR}/report_{report_id}"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    
    return {"message": "رپورٹ کامیابی سے حذف کر دی گئی"}


# =========================
# DELETE ALL REPORTS
# =========================
@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all reports for user
    reports = await get_reports(db, current_user.user_id)
    
    if not reports:
        raise HTTPException(status_code=404, detail="کوئی رپورٹ موجود نہیں")
    
    # Delete each report
    for report in reports:
        await delete_report(db, report.report_id, current_user.user_id)
        
        # Delete files
        folder = f"{BASE_DIR}/report_{report.report_id}"
        if os.path.exists(folder):
            shutil.rmtree(folder)
    
    return {"message": f"{len(reports)} رپورٹس کامیابی سے حذف کر دی گئیں"}