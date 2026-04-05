from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

from datetime import datetime, date
from decimal import Decimal

from myapp.models.udhaar_item import UdharItem
from myapp.models.customer import Customer
from myapp.models.item import Item
from myapp.models.user import User
from myapp.models.udhar import Udhar
from myapp.models.sales import Sale

from myapp.utils.urdu_date import convert_datetime_to_urdu
from myapp.utils.units import UnitConverter
from myapp.crud.udhar import update_udhar_summary
from myapp.services.email import low_stock_template, send_email

# =========================
# GLOBAL
# =========================
converter = UnitConverter()


# =========================
# FORMAT
# =========================
def format_item(i: UdharItem):
    return {
        "udharitem_id": i.udharitem_id,
        "customer_id": i.customer_id,
        "customer_name": i.customer.customer_name if i.customer else None,

        "item_id": i.item_id,
        "item_name": i.item_name,   # always from stored column

        "unit_price": float(i.unit_price),

        "quantity": float(i.quantity),   # base quantity
        "base_unit": i.base_unit,
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
# HELPERS
# =========================
async def get_or_create_customer(db: AsyncSession, name: str, current_user: User):
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


async def get_item_by_name(db: AsyncSession, name: str, current_user: User):
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

    requested_unit = str(unit).strip()
    if not requested_unit:
        raise HTTPException(status_code=400, detail="اکائی درج کرنا ضروری ہے")

    item_unit = item.item_unit.strip()

    # ================= UNIT CHECK =================
    if requested_unit == item_unit:
        base_quantity = float(quantity)
    else:
        if not converter.is_compatible(requested_unit, item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"'{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا (مثلاً کلو کو درجن میں تبدیل نہیں کیا جا سکتا)"
            )

        base_quantity = converter.convert(
            from_unit=requested_unit,
            to_unit=item_unit,
            value=float(quantity)
        )

    # ================= STOCK CHECK =================
    if base_quantity > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item_unit}"
        )

    item.stock_quantity -= base_quantity

    # ================= LOW STOCK ALERT =================
    if float(item.stock_quantity) < 10:
        try:
            subject = f"⚠️ Low Stock: {item.item_name}"

            body = low_stock_template(
                item_name=item.item_name,
                stock=item.stock_quantity,
                unit=item.item_unit
            )

            send_email(current_user.email, subject, body)

        except Exception as e:
            print("Low stock email error:", str(e))

    # ================= UDhar =================
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

    total_amount = Decimal(str(base_quantity)) * Decimal(str(item.unit_price))

    now = datetime.now()
    urdu_udhar = convert_datetime_to_urdu(now, prefix="udhar")
    urdu_sale = convert_datetime_to_urdu(now, prefix="sale")

    new_item = UdharItem(
        udhar_id=udhar.udhar_id,
        customer_id=customer.customer_id,

        item_id=item.item_id,
        item_name=item.item_name,  # ✅ Snapshot stored
        base_unit=item.item_unit,
        requested_unit=requested_unit,

        user_id=current_user.user_id,
        quantity=Decimal(str(base_quantity)),
        unit_price=float(item.unit_price),
        total_amount=total_amount,

        udhar_day=urdu_udhar["udhar_day"],
        udhar_month=urdu_udhar["udhar_month"],
        udhar_year=urdu_udhar["udhar_year"],
        udhar_time=urdu_udhar["udhar_time"],
        udhar_day_name=urdu_udhar["udhar_day_name"]
    )

    db.add(new_item)

    # ✅ FIXED: Added item_name, unit_price, and item_unit to sale
    db.add(Sale(
        customer_name=customer_name,
        item_id=item.item_id,
        item_name=item.item_name,  # ✅ CRITICAL: Added item_name
        quantity_sold=float(quantity),
        unit_price=float(item.unit_price),  # ✅ Added unit_price
        item_unit=requested_unit,  # ✅ Added item_unit
        sale_date=date.today(),
        user_id=current_user.user_id,
        sale_day=urdu_sale["sale_day"],
        sale_month=urdu_sale["sale_month"],
        sale_year=urdu_sale["sale_year"],
        sale_time=urdu_sale["sale_time"],
        sale_day_name=urdu_sale["sale_day_name"]
    ))

    await update_udhar_summary(db, customer.customer_id, current_user)
    await db.commit()

    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(UdharItem.udharitem_id == new_item.udharitem_id)
    )

    return format_item(res.scalar_one())


# =========================
# UPDATE
# =========================
async def update_udharitem(db: AsyncSession, item_id: int, data, current_user: User):
    # Get the udhar item
    res = await db.execute(
        select(UdharItem).where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    udhar_item = res.scalar_one_or_none()

    if not udhar_item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

    # ❗ IMPORTANT: deleted item check
    if udhar_item.item_id is None:
        raise HTTPException(
            status_code=400,
            detail="یہ آئٹم ڈیلیٹ ہو چکا ہے، اپڈیٹ ممکن نہیں"
        )

    # Get customer info
    customer_res = await db.execute(
        select(Customer).where(Customer.customer_id == udhar_item.customer_id)
    )
    customer = customer_res.scalar_one_or_none()
    customer_name = customer.customer_name if customer else "نامعلوم"

    # Get the old quantity to restore stock
    old_quantity = float(udhar_item.quantity)
    old_item_id = udhar_item.item_id
    
    # Get the old item to restore stock
    if old_item_id:
        old_item_res = await db.execute(
            select(Item).where(Item.item_id == old_item_id)
        )
        old_item = old_item_res.scalar_one_or_none()
        if old_item:
            # Restore old stock
            old_item.stock_quantity += old_quantity
            db.add(old_item)
    
    # Get the new item
    db_item = await get_item_by_name(db, data.item_name, current_user)

    requested_unit = data.unit.strip()
    item_unit = db_item.item_unit.strip()

    # Calculate new quantity
    if requested_unit == item_unit:
        base_quantity = float(data.quantity)
    else:
        if not converter.is_compatible(requested_unit, item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"'{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا"
            )

        base_quantity = converter.convert(
            from_unit=requested_unit,
            to_unit=item_unit,
            value=float(data.quantity)
        )

    # Check stock for new item
    if base_quantity > float(db_item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {db_item.stock_quantity} {item_unit}"
        )

    # Deduct new stock
    db_item.stock_quantity -= base_quantity
    db.add(db_item)

    # Update udhar item
    udhar_item.item_id = db_item.item_id
    udhar_item.item_name = db_item.item_name
    udhar_item.base_unit = db_item.item_unit
    udhar_item.quantity = Decimal(str(base_quantity))
    udhar_item.requested_unit = requested_unit
    udhar_item.unit_price = db_item.unit_price
    udhar_item.total_amount = Decimal(str(base_quantity)) * Decimal(str(db_item.unit_price))
    
    db.add(udhar_item)

    # ================= UPDATE SALE RECORD =================
    # Find the corresponding sale record for this udhar item
    sale_res = await db.execute(
        select(Sale).where(
            Sale.customer_name == customer_name,
            Sale.item_id == old_item_id,  # Old item ID
            Sale.user_id == current_user.user_id
        )
        .order_by(Sale.sale_id.desc())
        .limit(1)
    )
    sale = sale_res.scalar_one_or_none()
    
    if sale:
        # Update the existing sale record
        sale.item_id = db_item.item_id
        sale.item_name = db_item.item_name
        sale.quantity_sold = float(data.quantity)  # User entered quantity
        sale.unit_price = db_item.unit_price
        sale.item_unit = requested_unit
        db.add(sale)
    else:
        # Create a new sale record if not found
        now = datetime.now()
        urdu_sale = convert_datetime_to_urdu(now, prefix="sale")
        
        new_sale = Sale(
            customer_name=customer_name,
            item_id=db_item.item_id,
            item_name=db_item.item_name,
            quantity_sold=float(data.quantity),
            unit_price=db_item.unit_price,
            item_unit=requested_unit,
            sale_date=date.today(),
            user_id=current_user.user_id,
            sale_day=urdu_sale["sale_day"],
            sale_month=urdu_sale["sale_month"],
            sale_year=urdu_sale["sale_year"],
            sale_time=urdu_sale["sale_time"],
            sale_day_name=urdu_sale["sale_day_name"]
        )
        db.add(new_sale)

    # Commit changes
    await db.commit()
    await db.refresh(udhar_item)
    
    # Update udhar summary (this will also sync bill)
    await update_udhar_summary(db, udhar_item.customer_id, current_user)

    # Refresh again to get latest data
    await db.refresh(udhar_item)
    
    # Get fresh udhar item with customer relationship
    fresh_res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(UdharItem.udharitem_id == udhar_item.udharitem_id)
    )
    fresh_item = fresh_res.scalar_one()
    
    return format_item(fresh_item)

# =========================
# DELETE
# =========================
async def delete_udharitem(db, item_id, current_user):
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
        delete(UdharItem).where(UdharItem.udharitem_id == item_id)
    )

    await db.commit()
    await update_udhar_summary(db, customer_id, current_user)

    return {"message": "آئٹم کامیابی سے حذف کر دیا گیا"}


# =========================
# LIST
# =========================
async def list_udharitems(db, current_user):
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(UdharItem.user_id == current_user.user_id)
    )

    items = res.scalars().all()
    return [format_item(i) for i in items]