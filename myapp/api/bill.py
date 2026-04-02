from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from myapp.database.session import get_db
from myapp.schemas.bill import BillRead
from myapp.crud.bill import (
    get_bills_by_customer,
    get_all_bills,
    pay_bill_by_customer_name,
    delete_bill
)

from myapp.models.bill import Bill
from myapp.models.customer import Customer
from myapp.models.user import User
from myapp.utils.security import get_current_user

router = APIRouter(prefix="/bills", tags=["Bills"])


# =========================
# BILL HISTORY BY CUSTOMER ID
# =========================
@router.get("/customer/{customer_id}", response_model=list[BillRead])
async def bill_history_by_id(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bills = await get_bills_by_customer(db, customer_id, current_user)

    if not bills:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی بل موجود نہیں ہے")

    return bills


# =========================
# BILL HISTORY BY CUSTOMER NAME
# =========================
@router.get("/customer/name/{customer_name}", response_model=list[BillRead])
async def bill_history_by_name(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == customer_name.strip(),
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے")

    bills = await get_bills_by_customer(db, customer.customer_id, current_user)

    if not bills:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی بل موجود نہیں ہے")

    return bills


# =========================
# GET ALL BILLS
# =========================
@router.get("/", response_model=list[BillRead])
async def get_all_bills_endpoint(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bills = await get_all_bills(db, current_user, status)

    if not bills:
        raise HTTPException(status_code=404, detail="کوئی بل موجود نہیں ہے")

    return bills


# =========================
# PAY BILL
# =========================
@router.put("/pay/{customer_name}")
async def pay_bill_by_name(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await pay_bill_by_customer_name(db, customer_name, current_user)


# =========================
# DELETE BILL
# =========================
@router.delete("/{bill_id}")
async def delete_bill_endpoint(
    bill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await delete_bill(db, bill_id, current_user)

    if result == "unpaid":
        raise HTTPException(status_code=400, detail="❌ بل ادا نہیں ہوا۔ پہلے ادا کریں۔")

    if not result:
        raise HTTPException(status_code=404, detail="❌ بل نہیں ملا")

    return {"message": f"✅ بل {bill_id} کامیابی سے حذف کر دیا گیا", "success": True}


# =========================
# SEARCH BILLS (FIXED)
# =========================
@router.get("/search/", response_model=list[BillRead])
async def search_bills(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keyword = keyword.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="سرچ کی ورڈ درکار ہے")

    # 🔹 get matching customers
    res = await db.execute(
        select(Customer.customer_id).where(
            Customer.customer_name.ilike(f"%{keyword}%"),
            Customer.user_id == current_user.user_id
        )
    )
    customer_ids = [c for c in res.scalars().all()]

    if not customer_ids:
        raise HTTPException(status_code=404, detail="کوئی مماثل بل نہیں ملا")

    # 🔹 use your main formatter function (IMPORTANT)
    bills = []
    for cid in customer_ids:
        data = await get_bills_by_customer(db, cid, current_user)
        bills.extend(data)

    if not bills:
        raise HTTPException(status_code=404, detail="کوئی مماثل بل نہیں ملا")

    return bills