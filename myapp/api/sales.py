# api/sales.py
from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.sales import SaleRead
from sqlalchemy import select
from myapp.models.sales import Sale

router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/", response_model=list[SaleRead])
async def get_all_sales(db: AsyncSession = Depends(get_db)):
    stmt=select(Sale)
    res=await db.execute(stmt)
    return res.scalars().all()

@router.get("/{item_id}",response_model=list[SaleRead])
async def get_sale(item_id:int,db:AsyncSession=Depends(get_db)):
    stmt=select(Sale).where(Sale.item_id==item_id)
    res=await db.execute(stmt)
    sale=res.scalars().all()
    if not sale:
        raise HTTPException(status_code=404,detail="آئٹم کی فروخت نہیں ملی")
    return sale
    
