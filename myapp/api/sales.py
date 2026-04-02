from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime

from myapp.database.session import get_db
from myapp.schemas.sales import SaleRead, SaleCreate, SaleUpdate
from myapp.crud import sales as crud
from myapp.models.user import User
from myapp.utils.security import get_current_user
from myapp.utils.urdu_date import convert_datetime_to_urdu, get_urdu_day_number, get_urdu_month

router = APIRouter(prefix="/sales", tags=["sales"])

 
# ============================
# CREATE SALE
# ============================
@router.post("/", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """نیا سیلز ریکارڈ بنائیں"""
    sale_data = sale.model_dump()
    
    # Add Urdu date components
    sale_date = sale_data.get("sale_date", date.today())
    urdu_parts = convert_datetime_to_urdu(datetime.combine(sale_date, datetime.min.time()), "sale")
    sale_data.update(urdu_parts)
    
    return await crud.create_sale(db, sale_data, current_user)


# ============================
# GET ALL SALES
# ============================
@router.get("/", response_model=List[SaleRead])
async def get_all_sales(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="گاہک یا آئٹم کے نام سے تلاش کریں"),
    start_date: Optional[date] = Query(None, description="شروع تاریخ"),
    end_date: Optional[date] = Query(None, description="آخر تاریخ"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """تمام سیلز ریکارڈز دیکھیں"""
    return await crud.get_sales(db, current_user, search, start_date, end_date, skip, limit)


# ============================
# GET SINGLE SALE
# ============================
@router.get("/{sale_id}", response_model=SaleRead)
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ایک سیلز ریکارڈ دیکھیں"""
    return await crud.get_sale(db, sale_id, current_user)


# ============================
# SUMMARY
# ============================
@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """سیلز کا خلاصہ دیکھیں"""
    return await crud.get_sales_summary(db, current_user, start_date, end_date)


# ============================
# UPDATE SALE
# ============================
@router.patch("/{sale_id}", response_model=SaleRead)
async def update_sale(
    sale_id: int,
    sale: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """سیلز ریکارڈ اپ ڈیٹ کریں"""
    update_data = sale.model_dump(exclude_unset=True)
    
    # If date is updated, update Urdu components
    if "sale_date" in update_data and update_data["sale_date"]:
        urdu_parts = convert_datetime_to_urdu(datetime.combine(update_data["sale_date"], datetime.min.time()), "sale")
        update_data.update(urdu_parts)
    
    return await crud.update_sale(db, sale_id, update_data, current_user)


# ============================
# DELETE SALE
# ============================
@router.delete("/{sale_id}", status_code=status.HTTP_200_OK)
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """سیلز ریکارڈ حذف کریں"""
    return await crud.delete_sale_by_id(db, sale_id, current_user)


# ============================
# DELETE ALL SALES
# ============================
@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_sales(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تمام سیلز ریکارڈز حذف کریں"""
    return await crud.delete_all_sales(db, current_user)