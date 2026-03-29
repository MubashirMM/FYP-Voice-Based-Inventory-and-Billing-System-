from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from datetime import datetime

from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem  # ✅ Fixed import path
from myapp.models.customer import Customer
from myapp.models.bill import Bill
from myapp.models.user import User

from myapp.utils.urdu_date import convert_datetime_to_urdu
from myapp.crud.bill import sync_bill_from_udhar, pay_bill
from myapp.schemas.udhar import UdharRead


# =========================
# HELPER - GET EXISTING CUSTOMER ONLY
# =========================
async def get_customer_by_name(db: AsyncSession, name: str, current_user: User):
    """Get existing customer only (raises error if not found)"""
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
        raise HTTPException(
            status_code=404, 
            detail=f"'{name}' نام کا کوئی کسٹمر موجود نہیں ہے۔ پہلے کسٹمر بنائیں۔"
        )

    return customer


# =========================
# HELPER: GET OR CREATE CUSTOMER
# =========================
async def get_or_create_customer_by_name(db: AsyncSession, name: str, current_user: User):
    """Get existing customer or create a new one"""
    name = name.strip()
    
    if not name:
        raise HTTPException(status_code=400, detail="کسٹمر کا نام خالی نہیں ہو سکتا")

    # Try to find existing customer
    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == name,
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()

    # If not found, create new customer
    if not customer:
        customer = Customer(
            customer_name=name,
            user_id=current_user.user_id
        )
        db.add(customer)
        await db.flush()

    return customer


# =========================
# HELPER: GET OR CREATE UNPAID UDHAR
# =========================
async def get_or_create_unpaid_udhar(db: AsyncSession, customer_id: int, current_user: User):
    """Get existing unpaid udhar or create a new one (ensures only one unpaid udhar per customer)"""
    
    # First, close any other unpaid udhars for this customer (mark them as paid if total is 0)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    unpaid_udhars = res.scalars().all()
    
    # If there are multiple unpaid udhars, consolidate them
    if len(unpaid_udhars) > 1:
        # Keep the most recent one, mark others as paid
        most_recent = unpaid_udhars[0]
        for u in unpaid_udhars[1:]:
            u.status = "paid"
            u.paid_date = datetime.now().date()
            now = datetime.now()
            paid_urdu = convert_datetime_to_urdu(now, "paid")
            u.paid_day = paid_urdu["paid_day"]
            u.paid_month = paid_urdu["paid_month"]
            u.paid_year = paid_urdu["paid_year"]
            u.paid_time = paid_urdu["paid_time"]
            u.paid_day_name = paid_urdu["paid_day_name"]
        await db.flush()
        
        # Get the most recent unpaid udhar (should be the first one if total > 0)
        res = await db.execute(
            select(Udhar).where(
                Udhar.customer_id == customer_id,
                Udhar.user_id == current_user.user_id,
                Udhar.status == "unpaid"
            )
            .order_by(Udhar.udhar_id.desc())
            .limit(1)
        )
        udhar = res.scalar_one_or_none()
        
        if udhar and udhar.total == 0:
            udhar.status = "paid"
            await db.flush()
            udhar = None
    
    # Get the active unpaid udhar
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
        .order_by(Udhar.udhar_id.desc())
        .limit(1)
    )
    udhar = res.scalar_one_or_none()
    
    # If no unpaid udhar exists, create a new one
    if not udhar:
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid",
            direct_addition=0.0,
            direct_deduction=0.0,
            subtotal=0.0,
            total=0.0
        )
        db.add(udhar)
        await db.flush()
        
        # Add Urdu date for new udhar
        now = datetime.now()
        urdu = convert_datetime_to_urdu(now, "udhar")
        udhar.udhar_day = urdu["udhar_day"]
        udhar.udhar_month = urdu["udhar_month"]
        udhar.udhar_year = urdu["udhar_year"]
        udhar.udhar_time = urdu["udhar_time"]
        udhar.udhar_day_name = urdu["udhar_day_name"]
    
    return udhar


# =========================
# SUMMARY + BILL SYNC
# =========================
async def update_udhar_summary(db: AsyncSession, customer_id: int, current_user: User):

    # Get all udhar items for this customer
    res = await db.execute(
        select(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    items = res.scalars().all()

    # Get or create unpaid udhar (ensures only one)
    udhar = await get_or_create_unpaid_udhar(db, customer_id, current_user)

    if not udhar:
        return None

    # Calculate totals
    udhar.subtotal = sum(float(i.total_amount) for i in items)
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    
    # Update status
    if udhar.total == 0:
        udhar.status = "paid"
        now = datetime.now()
        udhar.paid_date = now.date()
        paid_urdu = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = paid_urdu["paid_day"]
        udhar.paid_month = paid_urdu["paid_month"]
        udhar.paid_year = paid_urdu["paid_year"]
        udhar.paid_time = paid_urdu["paid_time"]
        udhar.paid_day_name = paid_urdu["paid_day_name"]
    else:
        udhar.status = "unpaid"
        # Update Urdu fields for unpaid udhar
        now = datetime.now()
        urdu = convert_datetime_to_urdu(now, "udhar")
        udhar.udhar_day = urdu["udhar_day"]
        udhar.udhar_month = urdu["udhar_month"]
        udhar.udhar_year = urdu["udhar_year"]
        udhar.udhar_time = urdu["udhar_time"]
        udhar.udhar_day_name = urdu["udhar_day_name"]

    await db.commit()
    await db.refresh(udhar)

    # ✅ Sync bill
    await sync_bill_from_udhar(db, customer_id, current_user)

    return udhar


async def update_udhar_summary_by_name(
    db: AsyncSession,
    customer_name: str,
    current_user: User
):
    # Get customer
    customer = await get_customer_by_name(db, customer_name, current_user)

    # Recalculate + sync
    udhar = await update_udhar_summary(db, customer.customer_id, current_user)

    if not udhar:
        return None

    # Return validated schema
    return UdharRead.model_validate({
        **udhar.__dict__,
        "customer_name": customer.customer_name
    })


# =========================
# LIST ALL UDHARS
# =========================
async def list_udhars(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(Udhar)
        .options(selectinload(Udhar.customer))
        .where(Udhar.user_id == current_user.user_id)
        .order_by(Udhar.udhar_id.desc())
    )
    udhars = res.scalars().all()

    return [
        UdharRead.model_validate({
            **u.__dict__,
            "customer_name": u.customer.customer_name if u.customer else "نامعلوم"
        })
        for u in udhars
    ]


# =========================
# GET UDHAR BY CUSTOMER
# =========================
async def get_udhar_by_customer(db: AsyncSession, customer_name: str, current_user: User):

    customer = await get_customer_by_name(db, customer_name, current_user)

    # ✅ ALWAYS SYNC BEFORE RETURNING
    await update_udhar_summary(db, customer.customer_id, current_user)

    # Get the most recent unpaid udhar for this customer
    res = await db.execute(
        select(Udhar)
        .options(selectinload(Udhar.customer))
        .where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
        .order_by(Udhar.udhar_id.desc())
        .limit(1)
    )
    
    udhar = res.scalar_one_or_none()

    if not udhar:
        return None

    return UdharRead.model_validate({
        **udhar.__dict__,
        "customer_name": udhar.customer.customer_name if udhar.customer else customer.customer_name
    })


# =========================
# DIRECT ADDITION
# =========================
async def update_direct_addition(db: AsyncSession, customer_name: str, amount: float, current_user: User):
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="رقم صفر سے زیادہ ہونی چاہیے")

    # Get or create customer
    customer = await get_or_create_customer_by_name(db, customer_name, current_user)

    # Get or create unpaid udhar (ensures only one)
    udhar = await get_or_create_unpaid_udhar(db, customer.customer_id, current_user)

    # Add the amount
    udhar.direct_addition += amount
    
    # Recalculate total
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    
    # Update status if total becomes zero
    if udhar.total == 0:
        udhar.status = "paid"
        now = datetime.now()
        udhar.paid_date = now.date()
        paid_urdu = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = paid_urdu["paid_day"]
        udhar.paid_month = paid_urdu["paid_month"]
        udhar.paid_year = paid_urdu["paid_year"]
        udhar.paid_time = paid_urdu["paid_time"]
        udhar.paid_day_name = paid_urdu["paid_day_name"]
    else:
        udhar.status = "unpaid"

    await db.commit()
    await db.refresh(udhar)

    # ✅ Sync bill
    await sync_bill_from_udhar(db, customer.customer_id, current_user)

    return await get_udhar_by_customer(db, customer_name, current_user)


# =========================
# DIRECT DEDUCTION
# =========================

async def update_direct_deduction(db: AsyncSession, customer_name: str, amount: float, current_user: User):
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="رقم صفر سے زیادہ ہونی چاہیے")

    # First check if customer exists
    customer = await get_customer_by_name(db, customer_name, current_user)

    # Check if customer has any unpaid udhar
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

    # If no unpaid udhar exists, return error
    if not udhar:
        raise HTTPException(
            status_code=400, 
            detail=f"{customer.customer_name} کا کوئی غیر ادا شدہ ادھار موجود نہیں ہے۔ پہلے ادھار میں اشیاء شامل کریں یا ڈائریکٹ ایڈیشن کریں۔"
        )

    # Check if customer has any udhar items or direct additions to deduct from
    current_total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    
    if current_total <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"{customer.customer_name} کا موجودہ ادھار {current_total:.2f} ہے۔ کٹوتی ممکن نہیں۔"
        )

    if amount > current_total:
        raise HTTPException(
            status_code=400,
            detail=f"کٹوتی زیادہ ہے۔ {customer.customer_name} کا دستیاب ادھار: {current_total:.2f}"
        )

    # Apply deduction
    udhar.direct_deduction += amount
    udhar.total = udhar.subtotal + udhar.direct_addition - udhar.direct_deduction
    
    # Update status if total becomes zero
    if udhar.total == 0:
        udhar.status = "paid"
        now = datetime.now()
        udhar.paid_date = now.date()
        paid_urdu = convert_datetime_to_urdu(now, "paid")
        udhar.paid_day = paid_urdu["paid_day"]
        udhar.paid_month = paid_urdu["paid_month"]
        udhar.paid_year = paid_urdu["paid_year"]
        udhar.paid_time = paid_urdu["paid_time"]
        udhar.paid_day_name = paid_urdu["paid_day_name"]

    await db.commit()
    await db.refresh(udhar)

    # ✅ Sync bill
    await sync_bill_from_udhar(db, customer.customer_id, current_user)

    return await get_udhar_by_customer(db, customer_name, current_user)


# =========================
# DELETE UDHAR BY ID
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
        raise HTTPException(status_code=404, detail="یہ ادھار موجود نہیں ہے")

    customer_id = udhar.customer_id

    # Delete related udhar items
    await db.execute(
        delete(UdharItem).where(
            UdharItem.udhar_id == udhar.udhar_id,
            UdharItem.user_id == current_user.user_id
        )
    )

    # Delete related unpaid bill
    await db.execute(
        delete(Bill).where(
            Bill.customer_id == customer_id,
            Bill.user_id == current_user.user_id,
            Bill.status == "unpaid"
        )
    )

    # Delete the udhar record
    await db.execute(
        delete(Udhar).where(
            Udhar.udhar_id == udhar.udhar_id,
            Udhar.user_id == current_user.user_id
        )
    )

    await db.commit()

    return {"message": "ادھار کامیابی سے حذف کر دیا گیا"}


# =========================
# PAY UDHAR BY CUSTOMER NAME
# =========================
async def pay_udhaar_by_customer_name(db: AsyncSession, customer_name: str, current_user: User):

    customer = await get_customer_by_name(db, customer_name, current_user)

    # First sync to ensure latest data
    await update_udhar_summary(db, customer.customer_id, current_user)

    # Pay the bill
    bill = await pay_bill(db, customer.customer_id, current_user)

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="اس گاہک کا کوئی غیر ادا شدہ بل موجود نہیں"
        )

    return {
        "message": "ادھار اور بل کامیابی سے ادا کر دیا گیا",
        "customer_id": customer.customer_id,
        "customer_name": customer.customer_name,
        "bill_id": bill.bill_id,
        "status": bill.status,
        "effective_total": float(getattr(bill, "effective_total", 0))
    }