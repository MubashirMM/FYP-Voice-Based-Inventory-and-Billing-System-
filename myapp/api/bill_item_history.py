from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from myapp.database.session import get_db
from myapp.utils.security import get_current_user
from myapp.schemas.bill_item_history import BillItemHistoryRead
from myapp.crud.bill_item_history import (
    get_all_bill_items,
    search_bill_items
)

router = APIRouter(prefix="/bill-items-history", tags=["Bill Item History"])


@router.get("/", response_model=List[BillItemHistoryRead])
async def read_all_items(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await get_all_bill_items(db, current_user)


@router.get("/search", response_model=List[BillItemHistoryRead])
async def search_items(
    item_name: str = Query(..., description="آئٹم کا نام"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await search_bill_items(db, current_user, item_name)