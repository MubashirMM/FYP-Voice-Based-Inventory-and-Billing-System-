from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from myapp.database.session import get_db
from myapp.schemas.bill import BillRead
from myapp.crud.bill import (
    get_bills_by_customer,
    get_all_bills,
    pay_bill,
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
# GET ALL BILLS (with paid/unpaid filter)
# =========================
@router.get("/", response_model=list[BillRead])
async def get_all_bills_endpoint(
    status: str | None = None,  # paid, unpaid or None
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bills = await get_all_bills(db, current_user, status)
    if not bills:
        raise HTTPException(status_code=404, detail="کوئی بل موجود نہیں ہے")
    return bills


# =========================
# PAY BILL BY CUSTOMER ID
# =========================
@router.put("/customer/{customer_id}/pay", response_model=BillRead)
async def pay_customer_bill(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bill = await pay_bill(db, customer_id, current_user)
    if not bill:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی غیر ادا شدہ بل موجود نہیں")
    return bill


# =========================
# PAY BILL BY CUSTOMER NAME
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
        raise HTTPException(status_code=400, detail="بل ادا نہیں ہوا۔ پہلے ادا کریں۔")
    if not result:
        raise HTTPException(status_code=404, detail="بل نہیں ملا")
    return {"پیغام": f"بل {bill_id} کامیابی سے حذف کر دیا گیا"}


# =========================
# SEARCH BILLS BY CUSTOMER NAME
# =========================
@router.get("/search/", response_model=list[BillRead])
async def search_bills(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .join(Customer)
        .where(
            Customer.customer_name.ilike(f"%{keyword.strip()}%"),
            Bill.user_id == current_user.user_id
        )
    )
    bills = res.scalars().all()

    if not bills:
        raise HTTPException(status_code=404, detail="کوئی مماثل بل نہیں ملا")
    return bills