# =========================
# IMPORTS (ALL AT TOP)
# =========================
import os
import stat
import time
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from myapp.database.session import get_db
from myapp.models.sales import Sale
from myapp.models.report import Report
from myapp.models.user import User
from myapp.utils.security import get_current_user
from myapp.schemas.report import ReportResponse
from myapp.crud.report import create_report, delete_report, get_reports, get_report
from myapp.utils.report_generator import generate_report_files
from myapp.utils.urdu_date import convert_datetime_to_urdu

router = APIRouter(prefix="/reports", tags=["Reports"])
BASE_DIR = "reports_storage"


# =========================
# HELPER: Safe Folder Deletion (Windows-Compatible)
# =========================
def _remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def safe_delete_folder(folder_path: str, max_retries: int = 3, delay: float = 0.3) -> bool:
    """Safely delete a folder with retry logic for Windows file locks."""
    if not os.path.exists(folder_path):
        return True
    
    for attempt in range(max_retries):
        try:
            shutil.rmtree(folder_path, ignore_errors=False, onerror=_remove_readonly)
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                print(f"⚠️ Failed to delete {folder_path} after {max_retries} attempts")
                return False
            time.sleep(delay * (attempt + 1))
        except Exception as e:
            print(f"⚠️ Error deleting {folder_path}: {e}")
            return False
    return False


# =========================
# GENERATE REPORT
# =========================
@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    """Generate a new sales report (Excel only)"""
    
    # Get all sales for this user
    stmt = select(Sale).where(Sale.user_id == current_user.user_id).order_by(Sale.sale_date.desc())
    res = await db.execute(stmt)
    sales = res.scalars().all()
    
    if len(sales) < 5:
        raise HTTPException(status_code=400, detail="رپورٹ جنریٹ کرنے کے لیے کم از کم 5 فروخت کے ریکارڈز ضروری ہیں۔")
    
    unique_items = {s.item_name for s in sales}
    if len(unique_items) < 5:
        raise HTTPException(status_code=400, detail=f"کم از کم 5 مختلف اشیاء ضروری ہیں۔ موجودہ: {len(unique_items)}")
    
    # Create report record (Urdu dates will be automatically added in create_report)
    report = await create_report(
        db, 
        user_id=current_user.user_id,
        title=f"فروخت رپورٹ - {len(sales)} ریکارڈز", 
        kpi_summary={},
        table_data={
            "total_records": len(sales),
            "unique_items": len(unique_items)
        }
    )
    
    # Generate Excel report
    result = await generate_report_files(report.report_id, sales)
    
    if result.get("error"):
        await db.delete(report)
        await db.commit()
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Update report with KPI data
    report.kpi_summary = result["kpi"]
    await db.commit()
    await db.refresh(report)
    
    return report


# =========================
# DOWNLOAD EXCEL
# =========================
@router.get("/download-excel/{report_id}")
async def download_report_excel(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download Excel report file"""
    report = await get_report(db, report_id, current_user.user_id)
    if not report:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
    excel_path = os.path.join(BASE_DIR, f"report_{report_id}", "sales_report.xlsx")
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="Excel فائل موجود نہیں ہے")
    
    return FileResponse(
        excel_path, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        filename=f"sales_report_{report_id}.xlsx"
    )


# =========================
# LIST ALL REPORTS
# =========================
@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all reports for current user"""
    return await get_reports(db, current_user.user_id)


# =========================
# GET SINGLE REPORT
# =========================
@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report by ID"""
    report = await get_report(db, report_id, current_user.user_id)
    if not report:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    return report


# =========================
# DELETE ALL REPORTS
# =========================
@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all reports for current user"""
    reports = await get_reports(db, current_user.user_id)
    if not reports:
        raise HTTPException(status_code=404, detail="کوئی رپورٹ موجود نہیں")
    
    deleted_count = 0
    for report in reports:
        success = await delete_report(db, report.report_id, current_user.user_id)
        if not success:
            continue
        
        folder = f"{BASE_DIR}/report_{report.report_id}"
        if safe_delete_folder(folder):
            deleted_count += 1
        else:
            print(f"⚠️ Folder cleanup failed: {folder}")
    
    return {"message": f"{deleted_count} رپورٹس کامیابی سے حذف کر دی گئیں"}


# =========================
# DELETE SINGLE REPORT
# =========================
@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report_endpoint(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a single report"""
    success = await delete_report(db, report_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="رپورٹ نہیں ملی")
    
    folder = f"{BASE_DIR}/report_{report_id}"
    if not safe_delete_folder(folder):
        print(f"⚠️ Folder cleanup failed: {folder}")
    
    return {"message": "رپورٹ کامیابی سے حذف کر دی گئی"}