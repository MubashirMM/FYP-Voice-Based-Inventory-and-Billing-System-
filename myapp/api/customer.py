from fastapi import HTTPException, APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from myapp.database.session import get_db
from myapp.crud import customer as crud
from typing import List
from myapp.utils.security import get_current_user
from myapp.models.user import User

router = APIRouter(prefix="/customers", tags=["customers"])


# ============================
# CREATE CUSTOMER
# ============================
@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """نیا کسٹمر بنائیں"""
    return await crud.create_customers(db, customer, current_user)


# ============================
# SEARCH CUSTOMERS
# ============================
@router.get("/search", response_model=List[CustomerRead])  # ✅ Returns list
async def search_customers(
    customer_name: str = Query(..., description="کسٹمر کا نام یا اس کا حصہ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """نام کی بنیاد پر کسٹمر تلاش کریں"""
    return await crud.search_customer(db, customer_name, current_user)


# ============================
# GET ALL CUSTOMERS
# ============================
@router.get("/", response_model=List[CustomerRead])
async def get_all_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تمام کسٹمرز کی فہرست دیکھیں"""
    return await crud.read_all(db, current_user)


# ============================
# GET SINGLE CUSTOMER
# ============================
@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ایک کسٹمر دیکھیں"""
    return await crud.read_customer(db, customer_id, current_user)


# ============================
# UPDATE CUSTOMER
# ============================
@router.patch("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    customer: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """کسٹمر کا نام اپ ڈیٹ کریں"""
    return await crud.update_customer(db, customer_id, customer, current_user)


# ============================
# DELETE CUSTOMER
# ============================
@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer_endpoint(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """کسٹمر حذف کریں (صرف اس صورت میں جب کوئی غیر ادا شدہ بل نہ ہوں)"""
    result = await crud.delete_customer(db, customer_id, current_user)
    
    if not result["success"]:
        if result["customer_name"] is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    
    return {"detail": result["message"]}