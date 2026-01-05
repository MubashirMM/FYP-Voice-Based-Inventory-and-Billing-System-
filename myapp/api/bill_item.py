from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.bill_item import BillItemCreate, BillItemRead
from myapp.crud import bill_item as crud
from myapp.utils.security import get_current_user
from myapp.models.user import User
from typing import List

router = APIRouter(prefix="/billitems", tags=["billitems"])

@router.post("/", response_model=BillItemRead, status_code=status.HTTP_201_CREATED)
async def create_bill_item_endpoint(data: BillItemCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await crud.create_bill_item(db, data.model_dump(), current_user)

@router.get("/", response_model=List[BillItemRead])
async def list_bill_items_endpoint(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # list scoped to user
    return await crud.list_bill_items(db, current_user)
