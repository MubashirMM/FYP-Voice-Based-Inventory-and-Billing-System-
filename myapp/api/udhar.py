from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.database.session import get_db
from myapp.schemas.udhar import UdharRead
from myapp.crud.udhar import (
    list_udhars,
    get_udhar_by_customer,
    update_direct_addition,
    update_direct_deduction,
    update_udhar_summary_by_name,
    delete_udhar_by_id
)

from myapp.utils.security import get_current_user
from myapp.models.user import User


router = APIRouter(prefix="/udhars", tags=["udhars"])


# =========================
# GET ALL
# =========================
@router.get("/", response_model=list[UdharRead])
async def get_all_udhars(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await list_udhars(db, current_user)


# =========================
# GET BY CUSTOMER NAME
# =========================
@router.get("/{customer_name}", response_model=UdharRead)
async def get_udhar_for_customer(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    udhar = await get_udhar_by_customer(db, customer_name, current_user)

    if not udhar:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی اُدھار موجود نہیں ہے")

    return udhar


# =========================
# DIRECT ADDITION
# =========================
@router.put("/{customer_name}/direct-addition")
async def set_direct_addition(
    customer_name: str,
    amount: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    udhar = await update_direct_addition(db, customer_name, amount, current_user)

    return {
        "message": f"براہ راست جمع: {amount} روپے شامل کر دیے گئے",
        "subtotal": udhar.subtotal,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "total": udhar.total,
        "status": udhar.status,
        "udhar": UdharRead.model_validate(udhar)
    }


# =========================
# DIRECT DEDUCTION
# =========================
@router.put("/{customer_name}/direct-deduction")
async def set_direct_deduction(
    customer_name: str,
    amount: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    udhar = await update_direct_deduction(db, customer_name, amount, current_user)

    return {
        "message": f"براہ راست کٹوتی: {amount} روپے شامل کر دی گئی",
        "subtotal": udhar.subtotal,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "total": udhar.total,
        "status": udhar.status,
        "udhar": UdharRead.model_validate(udhar)
    }


# =========================
# SUMMARY (UPDATED)
# =========================
@router.get("/{customer_name}/summary")
async def get_udhar_summary(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    udhar = await update_udhar_summary_by_name(db, customer_name, current_user)

    if not udhar:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی اُدھار موجود نہیں ہے")

    return {
        "subtotal": udhar.subtotal,
        "direct_addition": udhar.direct_addition,
        "direct_deduction": udhar.direct_deduction,
        "total": udhar.total,
        "status": udhar.status
    }


# =========================
# DELETE
# =========================
@router.delete("/{udhar_id}", status_code=status.HTTP_200_OK)
async def delete_udhar_endpoint(
    udhar_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await delete_udhar_by_id(db, udhar_id, current_user)