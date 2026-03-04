from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.crud.bill import sync_bill_from_udhar
from myapp.models.user import User
from myapp.models.customer import Customer
from sqlalchemy.orm import selectinload
from datetime import datetime
from myapp.utils.urdu_date import convert_datetime_to_urdu

async def update_udhar_summary(db: AsyncSession, customer_id: int, current_user: User):
    # get all items for this customer
    res = await db.execute(
        select(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    items = res.scalars().all()

    # find unpaid udhar
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        # if no unpaid, create new
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid"
        )
        db.add(udhar)
        await db.flush()

    # recalc totals
    udhar.subtotal = sum(float(item.total_amount) for item in items)
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    udhar.status = "paid" if udhar.total == 0 else "unpaid"

    # update Urdu date fields
    now = datetime.now()
    urdu_udhar = convert_datetime_to_urdu(now, "udhar")
    udhar.udhar_day = urdu_udhar["udhar_day"]
    udhar.udhar_month = urdu_udhar["udhar_month"]
    udhar.udhar_year = urdu_udhar["udhar_year"]
    udhar.udhar_time = urdu_udhar["udhar_time"]
    udhar.udhar_day_name = urdu_udhar["udhar_day_name"]

    if udhar.status == "paid":
        udhar.paid_date = now.date()
        urdu_paid = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = urdu_paid["paid_day"]
        udhar.paid_month = urdu_paid["paid_month"]
        udhar.paid_year = urdu_paid["paid_year"]
        udhar.paid_time = urdu_paid["paid_time"]
        udhar.paid_day_name = urdu_paid["paid_day_name"]

    await db.commit()
    await db.refresh(udhar)

    await sync_bill_from_udhar(db, customer_id, current_user)
    return udhar


async def update_direct_addition(db: AsyncSession, customer_id: int, amount: float, current_user: User):
    # Ensure customer exists
    cust_res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id,
            Customer.user_id == current_user.user_id
        )
    )
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے، اس کا کوئی اُدھار نہیں ہے")

    # Get unpaid udhar or create new
    res = await db.execute(
        select(Udhar)
            .options(selectinload(Udhar.udharitems))
            .where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid" )
    )
    udhar = res.scalar_one_or_none()
    if not udhar:
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid",
            subtotal=0.0,
            direct_addition=0.0,
            direct_deduction=0.0,
            total=0.0
        )
        db.add(udhar)
        await db.flush()

    # Apply addition
    udhar.direct_addition += amount

    # Recalculate totals
    udhar.subtotal = sum(item.total_amount for item in udhar.udharitems)
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    udhar.status = "paid" if udhar.total == 0 else "unpaid"

    # Update Urdu date fields
    now = datetime.now()
    urdu_udhar = convert_datetime_to_urdu(now, "udhar")
    udhar.udhar_day = urdu_udhar["udhar_day"]
    udhar.udhar_month = urdu_udhar["udhar_month"]
    udhar.udhar_year = urdu_udhar["udhar_year"]
    udhar.udhar_time = urdu_udhar["udhar_time"]
    udhar.udhar_day_name = urdu_udhar["udhar_day_name"]

    if udhar.status == "paid":
        udhar.paid_date = now.date()
        urdu_paid = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = urdu_paid["paid_day"]
        udhar.paid_month = urdu_paid["paid_month"]
        udhar.paid_year = urdu_paid["paid_year"]
        udhar.paid_time = urdu_paid["paid_time"]
        udhar.paid_day_name = urdu_paid["paid_day_name"]

    await db.commit()
    await db.refresh(udhar)
    await sync_bill_from_udhar(db, customer_id, current_user)
    return udhar


async def update_direct_deduction(db: AsyncSession, customer_id: int, amount: float, current_user: User):
    # Ensure customer exists
    cust_res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id,
            Customer.user_id == current_user.user_id
        )
    )
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے، اس کا کوئی اُدھار نہیں ہے")

    # Get unpaid udhar or create new
    
    res = await db.execute(
        select(Udhar)
            .options(selectinload(Udhar.udharitems))
            .where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid" )
    )

    udhar = res.scalar_one_or_none()
    if not udhar:
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid",
            subtotal=0.0,
            direct_addition=0.0,
            direct_deduction=0.0,
            total=0.0
        )
        db.add(udhar)
        await db.flush()

    # Apply deduction
    udhar.direct_deduction += amount

    # Recalculate totals
    udhar.subtotal = sum(item.total_amount for item in udhar.udharitems)
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    udhar.status = "paid" if udhar.total == 0 else "unpaid"

    # Update Urdu date fields
    now = datetime.now()
    urdu_udhar = convert_datetime_to_urdu(now, "udhar")
    udhar.udhar_day = urdu_udhar["udhar_day"]
    udhar.udhar_month = urdu_udhar["udhar_month"]
    udhar.udhar_year = urdu_udhar["udhar_year"]
    udhar.udhar_time = urdu_udhar["udhar_time"]
    udhar.udhar_day_name = urdu_udhar["udhar_day_name"]

    if udhar.status == "paid":
        udhar.paid_date = now.date()
        urdu_paid = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = urdu_paid["paid_day"]
        udhar.paid_month = urdu_paid["paid_month"]
        udhar.paid_year = urdu_paid["paid_year"]
        udhar.paid_time = urdu_paid["paid_time"]
        udhar.paid_day_name = urdu_paid["paid_day_name"]

    await db.commit()
    await db.refresh(udhar)
    await sync_bill_from_udhar(db, customer_id, current_user)
    return udhar


async def get_udhar_by_customer(db: AsyncSession, customer_id: int, current_user: User):
    # First, try to get unpaid udhar (most common case for active transactions)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    unpaid_udhar = res.scalar_one_or_none()
    if unpaid_udhar:
        return unpaid_udhar
    
    # If no unpaid udhar, return the latest one (could be paid)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id
        ).order_by(Udhar.udhar_id.desc())
    )
    return res.scalar_one_or_none()


async def list_udhars(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(Udhar).where(Udhar.user_id == current_user.user_id)
    )
    return res.scalars().all()

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from fastapi import HTTPException
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.bill import Bill
from myapp.models.user import User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from fastapi import HTTPException
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.bill import Bill
from myapp.models.user import User

async def delete_udhar_by_id(db: AsyncSession, udhar_id: int, current_user: User):
    # Find the udhar by id scoped to user
    res = await db.execute(
        select(Udhar).where(
            Udhar.udhar_id == udhar_id,
            Udhar.user_id == current_user.user_id
        )
    )
    udhar = res.scalar_one_or_none()
    if not udhar:
        raise HTTPException(status_code=404, detail="یہ اُدھار موجود نہیں ہے")

    # Delete udhar items linked to this udhar
    await db.execute(
        delete(UdharItem).where(
            UdharItem.udhar_id == udhar.udhar_id,
            UdharItem.user_id == current_user.user_id
        )
    )

    # Delete unpaid bill for this customer (if any)
    await db.execute(
        delete(Bill).where(
            Bill.customer_id == udhar.customer_id,
            Bill.user_id == current_user.user_id,
            Bill.status == "unpaid"
        )
    )

    # Delete the udhar itself
    await db.execute(
        delete(Udhar).where(
            Udhar.udhar_id == udhar.udhar_id,
            Udhar.user_id == current_user.user_id
        )
    )

    await db.commit()
    return {"message": "اُدھار، متعلقہ آئٹمز اور غیر ادا شدہ بل کامیابی سے حذف کر دیے گئے"}
