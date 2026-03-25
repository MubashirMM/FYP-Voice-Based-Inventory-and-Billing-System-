from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from datetime import datetime
from decimal import Decimal

from myapp.models.udhaar_item import UdharItem
from myapp.models.customer import Customer
from myapp.models.item import Item
from myapp.models.user import User
from myapp.models.udhar import Udhar

from myapp.utils.urdu_date import convert_datetime_to_urdu
from myapp.utils.units import UnitConverter
from myapp.crud.udhar import update_udhar_summary


# Global converter
converter = UnitConverter()


# =========================
# HELPERS
# =========================
async def get_or_create_customer(
    db: AsyncSession, 
    name: str, 
    current_user: User
) -> Customer:
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
        customer = Customer(
            customer_name=name,
            user_id=current_user.user_id
        )
        db.add(customer)
        await db.flush()

    return customer


async def get_item_by_name(db: AsyncSession, name: str, current_user: User) -> Item:
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="آئٹم کا نام خالی نہیں ہو سکتا")

    res = await db.execute(
        select(Item).where(
            Item.item_name == name,
            Item.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")

    return item


def format_item(i: UdharItem):
    if not i:
        return None

    return {
        "udharitem_id": i.udharitem_id,
        "customer_id": i.customer_id,
        "customer_name": i.customer.customer_name if getattr(i, 'customer', None) else None,
        "item_id": i.item_id,
        "item_name": i.item.item_name if getattr(i, 'item', None) else None,
        "unit_price": float(i.unit_price),
        "quantity": float(i.quantity),
        "requested_unit": i.requested_unit,
        "total_amount": float(i.total_amount),
        "created_date": i.created_date,
        "udhar_day": i.udhar_day,
        "udhar_month": i.udhar_month,
        "udhar_year": i.udhar_year,
        "udhar_time": i.udhar_time,
        "udhar_day_name": i.udhar_day_name,
    }


# =========================
# CREATE
# =========================
async def create_udhar(
    db: AsyncSession,
    customer_name: str,
    item_name: str,
    quantity: float,
    unit: str,
    current_user: User
):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="مقدار صفر یا منفی نہیں ہو سکتی")

    customer = await get_or_create_customer(db, customer_name, current_user)
    item = await get_item_by_name(db, item_name, current_user)

    # Safe unit extraction
    requested_unit = str(unit).strip() if unit else ""

    if not requested_unit:
        raise HTTPException(status_code=400, detail="اکائی درج کرنا ضروری ہے")

    # ======================
    # UNIT LOGIC
    # ======================
    item_unit = str(item.item_unit).strip()

    if requested_unit == item_unit:
        base_quantity = quantity
    else:
        if not converter.is_compatible(requested_unit, item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"اکائی '{requested_unit}' آئٹم کی اکائی '{item_unit}' کے ساتھ مطابقت نہیں رکھتی"
            )
        try:
            base_quantity = converter.convert(
                from_unit=requested_unit,
                to_unit=item_unit,
                value=quantity
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"یونٹ تبدیل نہیں ہو سکتا: {str(e)}"
            )

    # ======================
    # NEW CHECK: Ensure enough stock
    # ======================
    if base_quantity > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item_unit}"
        )

    # Find or create unpaid Udhar
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer.customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()

    if not udhar:
        udhar = Udhar(
            customer_id=customer.customer_id,
            user_id=current_user.user_id,
            status="unpaid"
        )
        db.add(udhar)
        await db.flush()

    total_amount = Decimal(str(base_quantity)) * item.unit_price

    now = datetime.now()
    urdu = convert_datetime_to_urdu(now, "udhar")

    new_item = UdharItem(
        udhar_id=udhar.udhar_id,
        customer_id=customer.customer_id,
        item_id=item.item_id,
        user_id=current_user.user_id,
        quantity=Decimal(str(base_quantity)),
        requested_unit=requested_unit,
        unit_price=item.unit_price,
        total_amount=total_amount,
        udhar_day=urdu["udhar_day"],
        udhar_month=urdu["udhar_month"],
        udhar_year=urdu["udhar_year"],
        udhar_time=urdu["udhar_time"],
        udhar_day_name=urdu["udhar_day_name"]
    )

    db.add(new_item)
    await db.commit()

    await update_udhar_summary(db, customer.customer_id, current_user)

    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(UdharItem.udharitem_id == new_item.udharitem_id)
    )

    loaded_item = res.scalars().one()
    return format_item(loaded_item)

# =========================
# UPDATE
# =========================
async def update_udharitem(
    db: AsyncSession,
    item_id: int,
    data,                    # Pydantic model
    current_user: User
):
    res = await db.execute(
        select(UdharItem)
        .where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    udhar_item = res.scalar_one_or_none()

    if not udhar_item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="مقدار صفر یا منفی نہیں ہو سکتی")

    db_item = await get_item_by_name(db, data.item_name, current_user)

    requested_unit = str(data.unit).strip() if data.unit else ""

    if not requested_unit:
        raise HTTPException(status_code=400, detail="اکائی درج کرنا ضروری ہے")

    item_unit = str(db_item.item_unit).strip()

    # Same logic as create
    if requested_unit == item_unit:
        base_quantity = data.quantity
    else:
        if not converter.is_compatible(requested_unit, item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"اکائی '{requested_unit}' آئٹم کی اکائی '{item_unit}' کے ساتھ مطابقت نہیں رکھتی"
            )

        try:
            base_quantity = converter.convert(
                from_unit=requested_unit,
                to_unit=item_unit,
                value=data.quantity
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"یونٹ تبدیل نہیں ہو سکتا: {str(e)}"
            )

    # Update
    udhar_item.item_id = db_item.item_id
    udhar_item.quantity = Decimal(str(base_quantity))
    udhar_item.requested_unit = requested_unit
    udhar_item.unit_price = db_item.unit_price
    udhar_item.total_amount = Decimal(str(base_quantity)) * db_item.unit_price

    await db.commit()

    await update_udhar_summary(db, udhar_item.customer_id, current_user)

    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(UdharItem.udharitem_id == udhar_item.udharitem_id)
    )

    loaded_item = res.scalars().one()
    return format_item(loaded_item)


# =========================
# DELETE + LIST (unchanged)
# =========================
async def delete_udharitem(
    db: AsyncSession,
    item_id: int,
    current_user: User
):
    res = await db.execute(
        select(UdharItem).where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )

    item = res.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

    customer_id = item.customer_id

    await db.execute(
        delete(UdharItem).where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )

    await db.commit()

    await update_udhar_summary(db, customer_id, current_user)

    return {"message": "آئٹم کامیابی سے حذف کر دیا گیا"}


async def list_udharitems(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(UdharItem.user_id == current_user.user_id)
    )

    items = res.scalars().all()
    return [format_item(i) for i in items]