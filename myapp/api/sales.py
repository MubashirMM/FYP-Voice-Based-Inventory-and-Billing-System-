
from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from myapp.database.session import get_db
from myapp.schemas.sales import SaleRead
from myapp.models.sales import Sale
from myapp.utils.security import get_current_user
from myapp.crud.sales import delete_sale_by_id
from myapp.models.user import User


router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/", response_model=list[SaleRead])
async def get_all_sales(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Sale).where(Sale.user_id == current_user.user_id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{item_id}", response_model=list[SaleRead])
async def get_sale(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Sale).where(Sale.item_id == item_id, Sale.user_id == current_user.user_id)
    res = await db.execute(stmt)
    sale = res.scalars().all()
    if not sale:
        raise HTTPException(status_code=404, detail="آئٹم کی فروخت نہیں ملی")
    return sale

@router.delete("/{sale_id}", status_code=status.HTTP_200_OK)
async def delete_sale_endpoint(sale_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await delete_sale_by_id(db, sale_id, current_user)
    return result
