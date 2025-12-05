from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.udhar import UdharRead
from myapp.crud.udhar import (
    list_udhars, 
    get_udhar_by_customer, 
    update_direct_addition, 
    update_direct_deduction
)
from pydantic import BaseModel

router = APIRouter(prefix="/udhars", tags=["udhars"])

class DirectAmountUpdate(BaseModel):
    customer_id: int
    amount: float

@router.get("/", response_model=list[UdharRead])
async def get_all_udhars(db: AsyncSession = Depends(get_db)):
    """Get all udhars with computed effective total"""
    return await list_udhars(db)

@router.get("/{customer_id}", response_model=UdharRead)
async def get_udhar_for_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    udhar = await get_udhar_by_customer(db, customer_id)
    if not udhar:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی اُدھار موجود نہیں ہے")
    return udhar

@router.put("/{customer_id}/direct-addition")
async def set_direct_addition(
    customer_id: int, 
    amount: float, 
    db: AsyncSession = Depends(get_db)
):
    """Set direct addition amount (replaces existing value)"""
    udhar = await update_direct_addition(db, customer_id, amount)
    return {
        "message": f"براہ راست جمع: {amount} روپے سیٹ کر دیے گئے",
        "effective_total": udhar.total_amount + udhar.direct_addition - udhar.direct_deduction,
        "udhar": UdharRead.from_orm(udhar)
    }

@router.put("/{customer_id}/direct-deduction")
async def set_direct_deduction(
    customer_id: int, 
    amount: float, 
    db: AsyncSession = Depends(get_db)
):
    """Set direct deduction amount (replaces existing value)"""
    udhar = await update_direct_deduction(db, customer_id, amount)
    return {
        "message": f"براہ راست کٹوتی: {amount} روپے سیٹ کر دی گئی",
        "effective_total": udhar.total_amount + udhar.direct_addition - udhar.direct_deduction,
        "udhar": UdharRead.from_orm(udhar)
    }

@router.get("/{customer_id}/summary")
async def get_udhar_summary(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed summary including effective calculations"""
    udhar = await get_udhar_by_customer(db, customer_id)
    if not udhar:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی اُدھار موجود نہیں ہے")
    
    effective_total = udhar.total_amount + udhar.direct_addition - udhar.direct_deduction
    
    return {
        "udhar_items_total": udhar.total_amount,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "effective_total": effective_total,
        "effective_status": "paid" if effective_total == 0 else "unpaid",
        "base_status": udhar.status
    }