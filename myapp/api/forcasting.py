from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update, desc
import uuid
import os
import stat
import time
import shutil
from datetime import datetime
from typing import List, Optional

from myapp.database.session import AsyncSessionLocal, get_db
from myapp.models.user import User
from myapp.models.sales import Sale
from myapp.models.forecast_report import ForecastReport
from myapp.utils.security import get_current_user
from myapp.utils.forecast_report_charts import (
    generate_forecast_report,
    delete_forecast_report as delete_report_files
)

router = APIRouter(prefix="/forecast-report", tags=["Forecast Report"])

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


def safe_delete_folder(folder_path: str, max_retries: int = 3, delay: float = 0.5) -> bool:
    """Safely delete a folder with retry logic for Windows file locks."""
    if not os.path.exists(folder_path):
        return True
    
    # First try normal deletion
    for attempt in range(max_retries):
        try:
            shutil.rmtree(folder_path, onerror=_remove_readonly)
            print(f"✅ Successfully deleted folder: {folder_path}")
            return True
        except PermissionError as e:
            print(f"⚠️ Permission error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1:
                print(f"❌ Failed to delete {folder_path} after {max_retries} attempts")
                # Try alternative method - rename then delete
                try:
                    import tempfile
                    temp_name = os.path.join(os.path.dirname(folder_path), f"__delete_{int(time.time())}")
                    os.rename(folder_path, temp_name)
                    shutil.rmtree(temp_name, onerror=_remove_readonly)
                    print(f"✅ Successfully deleted via rename: {folder_path}")
                    return True
                except Exception:
                    return False
            time.sleep(delay * (attempt + 1))
        except Exception as e:
            print(f"⚠️ Error deleting {folder_path}: {e}")
            return False
    return False


@router.post("/generate/{days}")
async def create_forecast_report(
    days: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a forecast report for the current user (Excel only)
    
    - **days**: Number of days for forecast (minimum 7)
    """
    
    # Validate days - minimum 7 days
    if days < 7:
        raise HTTPException(
            status_code=400, 
            detail="Forecast days must be at least 7 days"
        )
    
    # Get user's sales data
    result = await db.execute(
        select(Sale).where(Sale.user_id == current_user.user_id)
    )
    sales = result.scalars().all()
    
    if not sales:
        raise HTTPException(
            status_code=404, 
            detail="No sales data found for this user"
        )
    
    # ✅ VALIDATE DATA BEFORE CREATING DB ENTRY
    # Check if there are enough items with 3+ sales
    from collections import defaultdict
    item_sales_count = defaultdict(int)
    for s in sales:
        item_sales_count[s.item_name] += 1
    
    valid_items = [item for item, count in item_sales_count.items() if count >= 3]
    
    # Validation: Need at least 2 items with 3+ sales
    if len(valid_items) < 2:
        raise HTTPException(
            status_code=400, 
            detail=f"پیشن گوئی کے لیے کم از کم 2 مختلف اشیاء کی ضرورت ہے جن کی کم از کم 3 سیلز ہوں۔ موجودہ: {len(valid_items)} اشیاء جن کی 3+ سیلز ہیں"
        )
    
    # Validation: Need at least 5 total sales records
    if len(sales) < 5:
        raise HTTPException(
            status_code=400, 
            detail=f"پیشن گوئی کے لیے کم از کم 5 سیلز ریکارڈ کی ضرورت ہے۔ موجودہ: {len(sales)}"
        )
    
    # Convert to list of dicts for forecasting
    sales_list = []
    for s in sales:
        sales_list.append({
            'sale_id': s.sale_id,
            'item_name': s.item_name,
            'quantity_sold': s.quantity_sold,
            'unit_price': float(s.unit_price) if s.unit_price else 0,
            'item_unit': s.item_unit or 'عدد',
            'sale_date': s.sale_date,
            'total_amount': s.quantity_sold * (float(s.unit_price) if s.unit_price else 0)
        })
    
    # Generate unique report ID
    report_id = str(uuid.uuid4())[:8]
    
    # ✅ ONLY CREATE DB ENTRY AFTER VALIDATION PASSES
    # Create report record
    report = ForecastReport(
        id=report_id,
        user_id=current_user.user_id,
        period_type=f"{days}_days",
        forecast_days=days,
        status="processing"
    )
    db.add(report)
    await db.commit()
    
    # Background task function
    async def generate_forecast_background():
        """Background task with its own database session"""
        async with AsyncSessionLocal() as bg_db:
            try:
                print(f"Starting forecast generation for report {report_id}, {days} days")
                
                # Generate forecast report (Excel only)
                result = await generate_forecast_report(
                    report_id, 
                    sales_list, 
                    days
                )
                
                if result.get("error"):
                    print(f"Forecast generation error: {result.get('message')}")
                    await bg_db.execute(
                        update(ForecastReport)
                        .where(ForecastReport.id == report_id)
                        .values(
                            status="failed",
                            error_message=result.get("message", "Unknown error")[:500]
                        )
                    )
                    await bg_db.commit()
                else:
                    print(f"Forecast generation completed successfully")
                    await bg_db.execute(
                        update(ForecastReport)
                        .where(ForecastReport.id == report_id)
                        .values(
                            status="completed",
                            total_items_analyzed=result["forecast_summary"]["total_items_analyzed"],
                            increasing_count=result["forecast_summary"]["increasing_count"],
                            decreasing_count=result["forecast_summary"]["decreasing_count"],
                            stable_count=result["forecast_summary"]["stable_count"],
                            excel_path=result["excel_path"],
                            folder_path=result["output_folder"],
                            completed_at=datetime.now()
                        )
                    )
                    await bg_db.commit()
                    
            except Exception as e:
                print(f"Exception in background task: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await bg_db.execute(
                        update(ForecastReport)
                        .where(ForecastReport.id == report_id)
                        .values(
                            status="failed",
                            error_message=str(e)[:500]
                        )
                    )
                    await bg_db.commit()
                except Exception as db_error:
                    print(f"Error updating report: {db_error}")
    
    # Add to background tasks
    background_tasks.add_task(generate_forecast_background)
    
    return {
        "message": f"Forecast report generation started for {days} days",
        "report_id": report_id,
        "status": "processing",
        "forecast_days": days
    }

@router.get("/status/{report_id}")
async def get_report_status(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status of a forecast report"""
    result = await db.execute(
        select(ForecastReport).where(
            ForecastReport.id == report_id,
            ForecastReport.user_id == current_user.user_id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    response = {
        "report_id": report.id,
        "status": report.status,
        "period_type": report.period_type,
        "generated_at": report.generated_at,
        "completed_at": report.completed_at if hasattr(report, 'completed_at') else None,
        "error_message": report.error_message,
        "summary": {
            "total_items_analyzed": report.total_items_analyzed,
            "increasing_count": report.increasing_count,
            "decreasing_count": report.decreasing_count,
            "stable_count": report.stable_count
        } if report.status == "completed" else None
    }
    
    if hasattr(report, 'forecast_days'):
        response["forecast_days"] = report.forecast_days
    
    return response


@router.get("/download/{report_id}")
async def download_forecast_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download forecast report Excel file only"""
    result = await db.execute(
        select(ForecastReport).where(
            ForecastReport.id == report_id,
            ForecastReport.user_id == current_user.user_id,
            ForecastReport.status == "completed"
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=404, 
            detail="Report not found or not completed"
        )
    
    file_path = report.excel_path
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Excel file not found")
    
    file_name = f"forecast_report_{report.period_type}.xlsx"
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a forecast report and all associated files"""
    result = await db.execute(
        select(ForecastReport).where(
            ForecastReport.id == report_id,
            ForecastReport.user_id == current_user.user_id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete physical files using safe_delete_folder
    if report.folder_path and os.path.exists(report.folder_path):
        if not safe_delete_folder(report.folder_path):
            print(f"⚠️ Warning: Could not fully delete folder {report.folder_path}")
    
    # Delete from database
    await db.execute(
        delete(ForecastReport).where(ForecastReport.id == report_id)
    )
    await db.commit()
    
    return {
        "message": "Report deleted successfully",
        "report_id": report_id
    }


@router.get("/list")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """List all forecast reports for the current user"""
    query = select(ForecastReport).where(
        ForecastReport.user_id == current_user.user_id
    )
    
    if status:
        query = query.where(ForecastReport.status == status)
    
    query = query.order_by(desc(ForecastReport.generated_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    # Get total count
    count_query = select(ForecastReport).where(
        ForecastReport.user_id == current_user.user_id
    )
    if status:
        count_query = count_query.where(ForecastReport.status == status)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    reports_list = []
    for r in reports:
        report_dict = {
            "id": r.id,
            "period_type": r.period_type,
            "generated_at": r.generated_at,
            "completed_at": r.completed_at if hasattr(r, 'completed_at') else None,
            "status": r.status,
            "total_items_analyzed": r.total_items_analyzed,
            "increasing_count": r.increasing_count,
            "decreasing_count": r.decreasing_count,
            "stable_count": r.stable_count,
            "error_message": r.error_message
        }
        if hasattr(r, 'forecast_days'):
            report_dict["forecast_days"] = r.forecast_days
        reports_list.append(report_dict)
    
    return {
        "reports": reports_list,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/details/{report_id}")
async def get_report_details(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific report"""
    result = await db.execute(
        select(ForecastReport).where(
            ForecastReport.id == report_id,
            ForecastReport.user_id == current_user.user_id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    response = {
        "id": report.id,
        "user_id": report.user_id,
        "period_type": report.period_type,
        "generated_at": report.generated_at,
        "completed_at": report.completed_at if hasattr(report, 'completed_at') else None,
        "status": report.status,
        "total_items_analyzed": report.total_items_analyzed,
        "increasing_count": report.increasing_count,
        "decreasing_count": report.decreasing_count,
        "stable_count": report.stable_count,
        "excel_path": report.excel_path,
        "folder_path": report.folder_path,
        "error_message": report.error_message
    }
    
    if hasattr(report, 'forecast_days'):
        response["forecast_days"] = report.forecast_days
    
    return response


@router.delete("/all", status_code=200)
async def delete_all_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all forecast reports for the current user"""
    result = await db.execute(
        select(ForecastReport).where(
            ForecastReport.user_id == current_user.user_id
        )
    )
    reports = result.scalars().all()
    
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    
    deleted_count = 0
    for report in reports:
        # Delete physical files
        if report.folder_path and os.path.exists(report.folder_path):
            if safe_delete_folder(report.folder_path):
                deleted_count += 1
            else:
                print(f"⚠️ Could not delete folder: {report.folder_path}")
        
        # Delete from database
        await db.execute(
            delete(ForecastReport).where(ForecastReport.id == report.id)
        )
    
    await db.commit()
    
    return {
        "message": f"{deleted_count} reports deleted successfully",
        "total_reports": len(reports)
    }