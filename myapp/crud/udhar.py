from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from datetime import datetime

from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.customer import Customer
from myapp.models.bill import Bill
from myapp.models.user import User
from myapp.utils.urdu_date import convert_datetime_to_urdu
from myapp.crud.bill import sync_bill_from_udhar


# =========================
# HELPER
# =========================
async def get_customer_by_name(db: AsyncSession, name: str, current_user: User):
    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == name.strip(),
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے")
    return customer


# =========================
# SUMMARY (UNCHANGED)
# =========================
async def update_udhar_summary(db: AsyncSession, customer_id: int, current_user: User):
    # all items for this customer
    res = await db.execute(
        select(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    items = res.scalars().all()

    # unpaid udhar
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid"
        )
        db.add(udhar)
        await db.flush()

    # recalc totals
    # udhar.subtotal = sum(float(item.total_amount) for item in items)
    udhar.subtotal = sum(float(item.total_amount) for item in items if not isinstance(item, dict))
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    udhar.status = "paid" if udhar.total == 0 else "unpaid"

    now = datetime.now()
    urdu = convert_datetime_to_urdu(now, "udhar")
    udhar.udhar_day = urdu["udhar_day"]
    udhar.udhar_month = urdu["udhar_month"]
    udhar.udhar_year = urdu["udhar_year"]
    udhar.udhar_time = urdu["udhar_time"]
    udhar.udhar_day_name = urdu["udhar_day_name"]

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

    # update bill
    await sync_bill_from_udhar(db, customer_id, current_user)

    return udhar


# =========================
# LIST ALL UDHAARS
# =========================
async def list_udhars(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(Udhar)
        .options(selectinload(Udhar.customer))
        .where(Udhar.user_id == current_user.user_id)
    )
    udhars = res.scalars().all()

    return [
        {
            "udhar_id": u.udhar_id,
            "customer_id": u.customer_id,                    # ✅ required by Pydantic
            "customer_name": u.customer.customer_name if u.customer else "",
            "subtotal": u.subtotal,
            "direct_addition": u.direct_addition,
            "direct_deduction": u.direct_deduction,
            "total": u.total,
            "status": u.status,
            "created_date": u.created_date,
            "paid_date": u.paid_date,
            "udhar_day": u.udhar_day,
            "udhar_month": u.udhar_month,
            "udhar_year": u.udhar_year,
            "udhar_time": u.udhar_time,
            "udhar_day_name": u.udhar_day_name,
            "paid_day": u.paid_day,
            "paid_month": u.paid_month,
            "paid_year": u.paid_year,
            "paid_time": u.paid_time,
            "paid_day_name": u.paid_day_name,
        }
        for u in udhars
    ]


# =========================
# GET UDHAAR BY CUSTOMER NAME
# =========================
async def get_udhar_by_customer(db: AsyncSession, customer_name: str, current_user: User):
    customer = await get_customer_by_name(db, customer_name, current_user)

    # unpaid first
    res = await db.execute(
        select(Udhar)
        .options(selectinload(Udhar.customer))
        .where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    unpaid = res.scalar_one_or_none()
    if unpaid:
        return {
            "udhar_id": unpaid.udhar_id,
            "customer_id": unpaid.customer_id,
            "customer_name": unpaid.customer.customer_name if unpaid.customer else "",
            "subtotal": unpaid.subtotal,
            "direct_addition": unpaid.direct_addition,
            "direct_deduction": unpaid.direct_deduction,
            "total": unpaid.total,
            "status": unpaid.status,
            "created_date": unpaid.created_date,
            "paid_date": unpaid.paid_date,
            "udhar_day": unpaid.udhar_day,
            "udhar_month": unpaid.udhar_month,
            "udhar_year": unpaid.udhar_year,
            "udhar_time": unpaid.udhar_time,
            "udhar_day_name": unpaid.udhar_day_name,
            "paid_day": unpaid.paid_day,
            "paid_month": unpaid.paid_month,
            "paid_year": unpaid.paid_year,
            "paid_time": unpaid.paid_time,
            "paid_day_name": unpaid.paid_day_name,
        }

    # otherwise latest
    res = await db.execute(
        select(Udhar)
        .options(selectinload(Udhar.customer))
        .where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id
        )
        .order_by(Udhar.udhar_id.desc())
    )
    u = res.scalar_one_or_none()
    if not u:
        return None

    return {
        "udhar_id": u.udhar_id,
        "customer_id": u.customer_id,
        "customer_name": u.customer.customer_name if u.customer else "",
        "subtotal": u.subtotal,
        "direct_addition": u.direct_addition,
        "direct_deduction": u.direct_deduction,
        "total": u.total,
        "status": u.status,
        "created_date": u.created_date,
        "paid_date": u.paid_date,
        "udhar_day": u.udhar_day,
        "udhar_month": u.udhar_month,
        "udhar_year": u.udhar_year,
        "udhar_time": u.udhar_time,
        "udhar_day_name": u.udhar_day_name,
        "paid_day": u.paid_day,
        "paid_month": u.paid_month,
        "paid_year": u.paid_year,
        "paid_time": u.paid_time,
        "paid_day_name": u.paid_day_name,
    }


# =========================
# DIRECT ADDITION / DEDUCTION
# =========================
from myapp.schemas.udhar import UdharRead

async def update_direct_addition(db: AsyncSession, customer_name: str, amount: float, current_user: User):
    customer = await get_customer_by_name(db, customer_name, current_user)

    res = await db.execute(
        select(Udhar)
        .where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        udhar = Udhar(customer_id=customer.customer_id, user_id=current_user.user_id, status="unpaid")
        db.add(udhar)
        await db.flush()

    udhar.direct_addition += amount
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction

    await db.commit()
    await db.refresh(udhar)

    await sync_bill_from_udhar(db, customer.customer_id, current_user)

    # ✅ Include customer_name explicitly for Pydantic
    return UdharRead.model_validate({
        **udhar.__dict__,
        "customer_name": customer.customer_name
    })

async def update_udhar_summary_by_name(db: AsyncSession, customer_name: str, current_user: User):
    customer = await get_customer_by_name(db, customer_name, current_user)

    udhar = await update_udhar_summary(db, customer.customer_id, current_user)

    return UdharRead.model_validate({
        **udhar.__dict__,
        "customer_name": customer.customer_name
    })

async def update_direct_deduction(db: AsyncSession, customer_name: str, amount: float, current_user: User):
    customer = await get_customer_by_name(db, customer_name, current_user)

    res = await db.execute(
        select(Udhar)
        .where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        raise HTTPException(status_code=400, detail="کوئی اُدھار موجود نہیں ہے")

    # ✅ Prevent over deduction
    current_total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction

    if amount > current_total:
        raise HTTPException(
            status_code=400,
            detail=f"کٹوتی زیادہ ہے۔ دستیاب رقم: {current_total}"
        )

    udhar.direct_deduction += amount
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction

    await db.commit()
    await db.refresh(udhar)

    await sync_bill_from_udhar(db, customer.customer_id, current_user)

    return UdharRead.model_validate({
        **udhar.__dict__,
        "customer_name": customer.customer_name
    })


# =========================
# DELETE
# =========================
async def delete_udhar_by_id(db: AsyncSession, udhar_id: int, current_user: User):
    res = await db.execute(
        select(Udhar).where(
            Udhar.udhar_id == udhar_id,
            Udhar.user_id == current_user.user_id
        )
    )
    udhar = res.scalar_one_or_none()
    if not udhar:
        raise HTTPException(status_code=404, detail="یہ اُدھار موجود نہیں ہے")

    # delete items
    await db.execute(
        delete(UdharItem).where(
            UdharItem.udhar_id == udhar.udhar_id,
            UdharItem.user_id == current_user.user_id
        )
    )

    # delete unpaid bill
    await db.execute(
        delete(Bill).where(
            Bill.customer_id == udhar.customer_id,
            Bill.user_id == current_user.user_id,
            Bill.status == "unpaid"
        )
    )

    # delete udhar itself
    await db.execute(
        delete(Udhar).where(
            Udhar.udhar_id == udhar.udhar_id,
            Udhar.user_id == current_user.user_id
        )
    )

    await db.commit()
    return {"message": "اُدھار کامیابی سے حذف کر دیا گیا"}