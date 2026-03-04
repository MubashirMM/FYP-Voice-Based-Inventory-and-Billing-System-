
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
from myapp.utils.security import get_current_user
from myapp.models.user import User

router = APIRouter(prefix="/udhars", tags=["udhars"])

@router.get("/", response_model=list[UdharRead])
async def get_all_udhars(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await list_udhars(db, current_user)

@router.get("/{customer_id}", response_model=UdharRead)
async def get_udhar_for_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    udhar = await get_udhar_by_customer(db, customer_id, current_user)
    if not udhar:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی اُدھار موجود نہیں ہے")
    return udhar

@router.put("/{customer_id}/direct-addition")
async def set_direct_addition(customer_id: int, amount: float, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    udhar = await update_direct_addition(db, customer_id, amount, current_user)
    return {
        "message": f"براہ راست جمع: {amount} روپے سیٹ کر دیے گئے",
        "subtotal": udhar.subtotal,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "total": udhar.total,
        "status": udhar.status,
        "udhar": UdharRead.model_validate(udhar)
    }

@router.put("/{customer_id}/direct-deduction")
async def set_direct_deduction(customer_id: int, amount: float, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    udhar = await update_direct_deduction(db, customer_id, amount, current_user)
    return {
        "message": f"براہ راست کٹوتی: {amount} روپے سیٹ کر دی گئی",
        "subtotal": udhar.subtotal,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "total": udhar.total,
        "status": udhar.status,
        "udhar": UdharRead.model_validate(udhar)
    }

@router.get("/{customer_id}/summary")
async def get_udhar_summary(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    udhar = await get_udhar_by_customer(db, customer_id, current_user)
    if not udhar:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی اُدھار موجود نہیں ہے")
    
    return {
        "subtotal": udhar.subtotal,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "total": udhar.total,
        "status": udhar.status
    }
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.crud.udhar import delete_udhar_by_id
from myapp.utils.security import get_current_user
from myapp.models.user import User

@router.delete("/{udhar_id}", status_code=status.HTTP_200_OK)
async def delete_udhar_endpoint(udhar_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await delete_udhar_by_id(db, udhar_id, current_user)
    return result
