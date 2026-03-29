from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from myapp.database.session import get_db
from myapp.schemas.items import ItemCreate, ItemUpdate, ItemRead
from myapp.crud import items as crud
from myapp.models.user import User
from myapp.utils.security import get_current_user

router = APIRouter(prefix="/items", tags=["items"])


# ============================
# CREATE ITEM
# ============================
@router.post(
    "/", 
    response_model=ItemRead, 
    status_code=status.HTTP_201_CREATED,
    summary="نیا آئٹم بنائیں",
    description="ایک نیا آئٹم بنائیں۔ آئٹم کا نام منفرد ہونا چاہیے۔"
)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    نیا آئٹم بنائیں
    
    - **item_name**: آئٹم کا نام (مثال: چاول، شکر، وغیرہ)
    - **item_unit**: یونٹ (مثال: کلو، بوری، kg، وغیرہ)
    - **unit_price**: فی یونٹ قیمت
    - **stock_quantity**: موجودہ اسٹاک مقدار
    """
    return await crud.create_items(db, item, current_user)


# ============================
# GET ALL ITEMS
# ============================
@router.get(
    "/", 
    response_model=List[ItemRead],
    summary="تمام آئٹمز دیکھیں",
    description="صارف کے تمام آئٹمز کی فہرست دیکھیں"
)
async def get_all_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """تمام آئٹمز کی فہرست حاصل کریں"""
    return await crud.read_all(db, current_user)


# ============================
# SEARCH ITEMS
# ============================
@router.get(
    "/search", 
    response_model=List[ItemRead],
    summary="آئٹمز تلاش کریں",
    description="نام کی بنیاد پر آئٹمز تلاش کریں"
)
async def search_items(
    keywords: str = Query(..., description="تلاش کے لیے کلیدی الفاظ", min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    نام کی بنیاد پر آئٹمز تلاش کریں
    
    - **keywords**: آئٹم کا نام یا اس کا حصہ
    """
    return await crud.search_item(db, keywords, current_user)


# ============================
# GET SINGLE ITEM
# ============================
@router.get(
    "/{item_id}", 
    response_model=ItemRead,
    summary="ایک آئٹم دیکھیں",
    description="آئی ڈی کی بنیاد پر ایک آئٹم دیکھیں"
)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    آئی ڈی کی بنیاد پر ایک آئٹم حاصل کریں
    
    - **item_id**: آئٹم کی شناختی نمبر
    """
    return await crud.read_item(db, item_id, current_user)


# ============================
# UPDATE ITEM
# ============================
@router.patch(
    "/{item_id}", 
    response_model=ItemRead,
    summary="آئٹم اپ ڈیٹ کریں",
    description="آئٹم کی معلومات میں ترمیم کریں"
)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    آئٹم کی معلومات اپ ڈیٹ کریں
    
    - **item_id**: آئٹم کی شناختی نمبر
    - **item_name**: نیا نام (اختیاری)
    - **item_unit**: نیا یونٹ (اختیاری)
    - **unit_price**: نئی قیمت (اختیاری)
    - **stock_quantity**: نیا اسٹاک (اختیاری)
    """
    return await crud.update_items(db, item_id, item, current_user)


# ============================
# DELETE ITEM
# ============================
@router.delete(
    "/{item_id}", 
    status_code=status.HTTP_200_OK,
    summary="آئٹم حذف کریں",
    description="آئٹم کو حذف کریں (متعلقہ فروخت/ادھار/بل ریکارڈز میں item_id NULL ہو جائے گا)"
)
async def delete_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    آئٹم حذف کریں
    
    **نوٹ**: آئٹم حذف ہونے کے بعد بھی:
    - فروخت کے ریکارڈز میں آئٹم کا نام محفوظ رہے گا
    - ادھار کے ریکارڈز میں آئٹم کا نام محفوظ رہے گا
    - بل کے ریکارڈز میں آئٹم کا نام محفوظ رہے گا
    - item_id NULL ہو جائے گا
    """
    await crud.delete_item(db, item_id, current_user)
    return {
        "message": "آئٹم کامیابی سے حذف کر دیا گیا۔",
        "detail": "متعلقہ فروخت، ادھار اور بل ریکارڈز میں آئٹم کا نام محفوظ رہے گا۔"
    }