from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.database.session import get_db
from myapp.schemas.bill_item import BillItemCreate, BillItemRead
from myapp.crud.bill_item import (
    create_bill_item,
    list_bill_items,
    get_bill_item_by_id,
    delete_bill_item,
    search_bill_items
)
from myapp.models.user import User
from myapp.utils.security import get_current_user

router = APIRouter(prefix="/bill-items", tags=["Bill Items"])


# =========================
# CREATE
# =========================
from fastapi import BackgroundTasks   # ✅ ADD THIS IMPORT

@router.post("/", response_model=BillItemRead)
async def create_new_bill_item(
    bill_data: BillItemCreate,
    background_tasks: BackgroundTasks,   # ✅ ADD THIS LINE
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        data = bill_data.model_dump()
        return await create_bill_item(db, data, current_user,background_tasks)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# LIST ALL
# =========================
@router.get("/", response_model=list[BillItemRead])
async def get_all_bill_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await list_bill_items(db, current_user)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# GET BY ID
# =========================
@router.get("/{billitem_id}", response_model=BillItemRead)
async def get_bill_item(
    billitem_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await get_bill_item_by_id(db, billitem_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# DELETE
# =========================
@router.delete("/{billitem_id}")
async def delete_bill_item_endpoint(
    billitem_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await delete_bill_item(db, billitem_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# SEARCH
# =========================
@router.get("/search/", response_model=list[BillItemRead])
async def search_bill_items_endpoint(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if not keyword or not keyword.strip():
            raise HTTPException(status_code=400, detail="سرچ کی ورڈ درکار ہے")

        return await search_bill_items(db, keyword, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")