from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from myapp.models.bill import Bill
from myapp.models.bill_item_history import BillItemHistory
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.customer import Customer
from myapp.models.user import User
from myapp.utils.urdu_date import convert_datetime_to_urdu


# =========================
# HELPER
# =========================
async def get_customer_by_name(db: AsyncSession, name: str, current_user: User) -> Customer:
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="کسٹمر کا نام خالی نہیں ہو سکتا")

    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == name,
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے")
    return customer


# =========================
# SYNC BILL FROM UDHAAR
# =========================
async def sync_bill_from_udhar(db: AsyncSession, customer_id: int, current_user: User) -> Bill:
    # Get unpaid udhar or latest one
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        res = await db.execute(
            select(Udhar)
            .where(Udhar.customer_id == customer_id, Udhar.user_id == current_user.user_id)
            .order_by(Udhar.udhar_id.desc())
        )
        udhar = res.scalar_one_or_none()

    # Get udhar items
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.item))
        .where(UdharItem.customer_id == customer_id, UdharItem.user_id == current_user.user_id)
    )
    items = res.scalars().all()

    items_total = sum(float(i.total_amount) for i in items)
    direct_add = float(udhar.direct_addition) if udhar else 0.0
    direct_ded = float(udhar.direct_deduction) if udhar else 0.0
    effective_total = items_total + direct_add - direct_ded

    # Get or create unpaid bill
    res = await db.execute(
        select(Bill).where(
            Bill.customer_id == customer_id,
            Bill.user_id == current_user.user_id,
            Bill.status == "unpaid"
        )
    )
    bill = res.scalar_one_or_none()

    now = datetime.now()
    bill_urdu = convert_datetime_to_urdu(now, "bill")

    if not bill or bill.status == "paid":
        bill = Bill(
            customer_id=customer_id,
            status="unpaid",
            user_id=current_user.user_id,
            bill_day=bill_urdu["bill_day"],
            bill_month=bill_urdu["bill_month"],
            bill_year=bill_urdu["bill_year"],
            bill_time=bill_urdu["bill_time"],
            bill_day_name=bill_urdu["bill_day_name"]
        )
        db.add(bill)
        await db.flush()

    # Update totals
    bill.udhar_items_total = items_total
    bill.direct_addition = direct_add
    bill.direct_deduction = direct_ded
    bill.effective_total = effective_total
    bill.status = "paid" if effective_total == 0 else "unpaid"

    # Rebuild bill items history
    await db.execute(
        delete(BillItemHistory).where(
            BillItemHistory.bill_id == bill.bill_id,
            BillItemHistory.user_id == current_user.user_id
        )
    )

    for item in items:
        db.add(BillItemHistory(
            bill_id=bill.bill_id,
            user_id=current_user.user_id,
            item_name=item.item.item_name if item.item else "",
            unit_price=float(item.unit_price),
            quantity=float(item.quantity),
            requested_unit=item.requested_unit,
            total_amount=float(item.total_amount),
        ))

    # If fully paid, mark udhar as paid and clear items
    if bill.status == "paid" and udhar:
        udhar.status = "paid"
        await db.execute(
            delete(UdharItem).where(
                UdharItem.customer_id == customer_id,
                UdharItem.user_id == current_user.user_id
            )
        )

    await db.commit()
    await db.refresh(bill)
    return bill


# =========================
# GET BILLS
# =========================
async def get_bills_by_customer(db: AsyncSession, customer_id: int, current_user: User):
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .where(Bill.customer_id == customer_id, Bill.user_id == current_user.user_id)
    )
    return res.scalars().all()


async def get_all_bills(db: AsyncSession, current_user: User, status: str | None = None):
    query = select(Bill).options(selectinload(Bill.items)).where(Bill.user_id == current_user.user_id)

    if status == "paid":
        query = query.where(Bill.status == "paid")
    elif status == "unpaid":
        query = query.where(Bill.status == "unpaid")

    res = await db.execute(query)
    return res.scalars().all()


# =========================
# PAY BILL
# =========================
async def pay_bill(db: AsyncSession, customer_id: int, current_user: User):
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .where(Bill.customer_id == customer_id, Bill.user_id == current_user.user_id)
    )
    bill = res.scalar_one_or_none()
    if not bill:
        return None

    bill.status = "paid"

    now = datetime.now()
    bill_urdu = convert_datetime_to_urdu(now, "bill")
    bill.bill_day = bill_urdu["bill_day"]
    bill.bill_month = bill_urdu["bill_month"]
    bill.bill_year = bill_urdu["bill_year"]
    bill.bill_time = bill_urdu["bill_time"]
    bill.bill_day_name = bill_urdu["bill_day_name"]

    # Mark udhar as paid
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()
    if udhar:
        udhar.status = "paid"
        udhar.paid_date = now.date()
        urdu_paid = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = urdu_paid["paid_day"]
        udhar.paid_month = urdu_paid["paid_month"]
        udhar.paid_year = urdu_paid["paid_year"]
        udhar.paid_time = urdu_paid["paid_time"]
        udhar.paid_day_name = urdu_paid["paid_day_name"]

    # Clear udhar items
    await db.execute(
        delete(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )

    await db.commit()
    await db.refresh(bill)
    return bill


async def pay_bill_by_customer_name(db: AsyncSession, customer_name: str, current_user: User):
    customer = await get_customer_by_name(db, customer_name, current_user)
    bill = await pay_bill(db, customer.customer_id, current_user)

    if not bill:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی غیر ادا شدہ بل موجود نہیں")

    return {
        "message": "بل کامیابی سے ادا کر دیا گیا",
        "customer_id": customer.customer_id,
        "customer_name": customer.customer_name,
        "bill_id": bill.bill_id,
        "status": bill.status,
        "effective_total": float(getattr(bill, "effective_total", 0)),
        "paid_on": f"{bill.bill_day_name} {bill.bill_day}/{bill.bill_month}/{bill.bill_year}"
    }


# =========================
# DELETE BILL
# =========================
async def delete_bill(db: AsyncSession, bill_id: int, current_user: User):
    res = await db.execute(
        select(Bill).where(Bill.bill_id == bill_id, Bill.user_id == current_user.user_id)
    )
    bill = res.scalar_one_or_none()

    if not bill:
        return False
    if bill.status == "unpaid":
        return "unpaid"

    await db.execute(
        delete(BillItemHistory).where(
            BillItemHistory.bill_id == bill_id,
            BillItemHistory.user_id == current_user.user_id
        )
    )
    await db.execute(
        delete(Bill).where(Bill.bill_id == bill_id, Bill.user_id == current_user.user_id)
    )

    await db.commit()
    return True