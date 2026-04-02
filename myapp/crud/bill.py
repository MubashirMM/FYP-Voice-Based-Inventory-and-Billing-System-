from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from myapp.models.bill import Bill
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem  # ✅ Fixed: udhar_item not udhaar_item
from myapp.models.customer import Customer
from myapp.models.user import User 
from myapp.models.bill_item_history import BillItemHistory

from myapp.utils.urdu_date import convert_datetime_to_urdu


# =========================
# HELPER
# =========================
async def get_customer_by_name(db: AsyncSession, name: str, current_user: User):
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
# =========================
# SYNC BILL FROM UDHAAR
# =========================
async def sync_bill_from_udhar(db: AsyncSession, customer_id: int, current_user: User):

    # Get the most recent unpaid udhar (if multiple, take the latest one)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
        .order_by(Udhar.udhar_id.desc())
        .limit(1)  # ✅ Add limit to get only one row
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        # If no unpaid udhar, get the most recent one (any status)
        res = await db.execute(
            select(Udhar)
            .where(
                Udhar.customer_id == customer_id,
                Udhar.user_id == current_user.user_id
            )
            .order_by(Udhar.udhar_id.desc())
            .limit(1)  # ✅ Add limit
        )
        udhar = res.scalar_one_or_none()

    # If still no udhar, return without syncing
    if not udhar:
        return None

    res = await db.execute(
        select(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
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
    urdu = convert_datetime_to_urdu(now, "bill")

    if not bill:
        bill = Bill(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid",
            bill_date=now.date(),
            bill_day=urdu["bill_day"],
            bill_month=urdu["bill_month"],
            bill_year=urdu["bill_year"],
            bill_time=urdu["bill_time"],
            bill_day_name=urdu["bill_day_name"]
        )
        db.add(bill)
        await db.flush()

    bill.udhar_items_total = items_total
    bill.direct_addition = direct_add
    bill.direct_deduction = direct_ded
    bill.effective_total = effective_total
    bill.status = "paid" if effective_total == 0 else "unpaid"

    # rebuild history
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
            item_name=item.item_name,
            unit_price=float(item.unit_price),
            quantity=float(item.quantity),
            requested_unit=item.requested_unit,
            total_amount=float(item.total_amount),
        ))

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
# FORMAT BILL (NEW COMMON FUNCTION)
# =========================
async def format_bill(db, bill, current_user):
    customer_name = "نقد"

    if bill.customer_id:
        res = await db.execute(
            select(Customer.customer_name).where(
                Customer.customer_id == bill.customer_id,
                Customer.user_id == current_user.user_id
            )
        )
        customer_name = res.scalar_one_or_none() or "نامعلوم"

    items = [
        {
            "item_name": i.item_name,
            "unit_price": i.unit_price,
            "quantity": i.quantity,
            "requested_unit": i.requested_unit,
            "total_amount": i.total_amount
        }
        for i in bill.items
    ]

    return {
        "bill_id": bill.bill_id,
        "customer_id": bill.customer_id,
        "customer_name": customer_name,
        "udhar_items_total": bill.udhar_items_total,
        "direct_addition": bill.direct_addition,
        "direct_deduction": bill.direct_deduction,
        "effective_total": bill.effective_total,
        "status": bill.status,
        "bill_date": bill.bill_date,
        "bill_day": bill.bill_day,
        "bill_month": bill.bill_month,
        "bill_year": bill.bill_year,
        "bill_time": bill.bill_time,
        "bill_day_name": bill.bill_day_name,
        "items": items
    }


# =========================
# GET ALL BILLS
# =========================
async def get_all_bills(db: AsyncSession, current_user: User, status=None):
    query = (
        select(Bill)
        .options(selectinload(Bill.items))
        .where(Bill.user_id == current_user.user_id)
    )

    if status:
        query = query.where(Bill.status == status)

    res = await db.execute(query.order_by(Bill.bill_id.desc()))
    bills = res.scalars().all()

    return [await format_bill(db, b, current_user) for b in bills]


# =========================
# GET BILLS BY CUSTOMER
# =========================
async def get_bills_by_customer(db: AsyncSession, customer_id: int, current_user: User):

    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .where(
            Bill.customer_id == customer_id,
            Bill.user_id == current_user.user_id
        )
    )
    bills = res.scalars().all()

    return [await format_bill(db, b, current_user) for b in bills]


# =========================
# PAY BILL (INTERNAL)
# =========================
async def pay_bill(db: AsyncSession, customer_id: int, current_user: User):

    res = await db.execute(
        select(Bill).where(
            Bill.customer_id == customer_id,
            Bill.user_id == current_user.user_id,
            Bill.status == "unpaid"
        )
    )
    bill = res.scalar_one_or_none()

    if not bill:
        return None

    bill.status = "paid"

    now = datetime.now()
    urdu = convert_datetime_to_urdu(now, "bill")

    bill.bill_day = urdu["bill_day"]
    bill.bill_month = urdu["bill_month"]
    bill.bill_year = urdu["bill_year"]
    bill.bill_time = urdu["bill_time"]
    bill.bill_day_name = urdu["bill_day_name"]

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
# PAY BILL BY CUSTOMER NAME
# =========================
# =========================
# PAY BILL BY CUSTOMER NAME
# =========================
async def pay_bill_by_customer_name(db: AsyncSession, customer_name: str, current_user: User):

    customer = await get_customer_by_name(db, customer_name, current_user)

    # Get the unpaid udhar for this customer
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
        .order_by(Udhar.udhar_id.desc())
        .limit(1)
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        raise HTTPException(status_code=400, detail="یہ ادھار پہلے ہی ادا ہو چکا ہے")

    # Pay the bill
    bill = await pay_bill(db, customer.customer_id, current_user)

    if not bill:
        raise HTTPException(status_code=404, detail="بل نہیں ملا")

    # ✅ ADD THIS: Update udhar status to paid
    if udhar:
        udhar.status = "paid"
        udhar.paid_date = datetime.now().date()
        now = datetime.now()
        paid_urdu = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = paid_urdu["paid_day"]
        udhar.paid_month = paid_urdu["paid_month"]
        udhar.paid_year = paid_urdu["paid_year"]
        udhar.paid_time = paid_urdu["paid_time"]
        udhar.paid_day_name = paid_urdu["paid_day_name"]
        await db.commit()
        await db.refresh(udhar)

    return {
        "message": "بل اور ادھار کامیابی سے ادا کر دیا گیا",
        "customer_name": customer.customer_name,
        "bill_id": bill.bill_id,
        "udhar_id": udhar.udhar_id,
        "status": "paid"
    }
# =========================
# DELETE BILL
# =========================
async def delete_bill(db: AsyncSession, bill_id: int, current_user: User):

    from myapp.models.bill_item import BillItem  # Import here to avoid circular import

    # Check if bill exists
    res = await db.execute(
        select(Bill).where(
            Bill.bill_id == bill_id,
            Bill.user_id == current_user.user_id
        )
    )
    bill = res.scalar_one_or_none()

    if not bill:
        return False

    # Cannot delete unpaid bill
    if bill.status == "unpaid":
        return "unpaid"

    # ✅ First delete all related bill items (BillItem table)
    await db.execute(
        delete(BillItem).where(
            BillItem.bill_id == bill_id,
            BillItem.user_id == current_user.user_id
        )
    )

    # ✅ Then delete bill item history
    await db.execute(
        delete(BillItemHistory).where(
            BillItemHistory.bill_id == bill_id,
            BillItemHistory.user_id == current_user.user_id
        )
    )

    # ✅ Finally delete the bill itself
    await db.execute(
        delete(Bill).where(
            Bill.bill_id == bill_id,
            Bill.user_id == current_user.user_id
        )
    )

    await db.commit()
    return True