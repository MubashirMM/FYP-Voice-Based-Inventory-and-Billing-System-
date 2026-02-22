from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date as date_cls, datetime

from myapp.models.customer import Customer
from myapp.models.item import Item
from myapp.models.udhaar_item import UdharItem
from myapp.models.sales import Sale
from myapp.utils.units import UnitConverter
from myapp.crud.udhar import update_udhar_summary
from myapp.models.user import User
from myapp.utils.urdu_date import convert_datetime_to_urdu

async def create_udhar(
    db: AsyncSession,
    customer_name: str,
    item_name: str,
    quantity: float,
    unit: str,
    current_user: User,
    req_date: date_cls | None = None
):
    if quantity <= 0:
        raise ValueError("مقدار صفر یا منفی نہیں ہو سکتی")

    # Fetch item scoped to user
    item_res = await db.execute(
        select(Item).where(Item.item_name == item_name, Item.user_id == current_user.user_id)
    )
    item = item_res.scalar_one_or_none()
    if not item:
        raise ValueError(f"آئٹم '{item_name}' موجود نہیں ہے")

    # Fetch or create customer scoped to user
    cust_res = await db.execute(
        select(Customer).where(Customer.customer_name == customer_name, Customer.user_id == current_user.user_id)
    )
    customer = cust_res.scalar_one_or_none()
    if not customer:
        customer = Customer(customer_name=customer_name, user_id=current_user.user_id)
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

    # Unit conversion
    converter = UnitConverter()
    if not converter.is_compatible(item.item_unit, unit):
        raise ValueError(f"اکائی '{unit}' آئٹم کی بنیادی اکائی '{item.item_unit}' کے ساتھ مطابقت نہیں رکھتی")

    qty_in_base = converter.convert(item.item_unit, unit, quantity)

    # Inventory check
    if qty_in_base > float(item.stock_quantity):
        raise ValueError(
            f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item.item_unit}, "
            f"درکار: {qty_in_base} {item.item_unit}"
        )

    # Calculate total
    unit_price_base = float(item.unit_price)
    total_amount = unit_price_base * qty_in_base

    # Prepare date
    use_date = req_date or date_cls.today()
    
    # Get current datetime for time
    now = datetime.now()
    
    # Convert to Urdu format for Udhar
    udhar_urdu = convert_datetime_to_urdu(now, "udhar")
    
    # Convert to Urdu format for Sale
    sale_urdu = convert_datetime_to_urdu(now, "sale")

    # Create udhar record with Urdu date/time fields
    udhar = UdharItem(
        customer_id=customer.customer_id,
        item_id=item.item_id,
        unit_price=unit_price_base,
        quantity=quantity,
        requested_unit=unit.strip(),
        total_amount=total_amount,
        date_=use_date,
        user_id=current_user.user_id,
        udhar_day=udhar_urdu["udhar_day"],
        udhar_month=udhar_urdu["udhar_month"],
        udhar_year=udhar_urdu["udhar_year"],
        udhar_time=udhar_urdu["udhar_time"],
        udhar_day_name=udhar_urdu["udhar_day_name"]
    )
    db.add(udhar)

    # Create corresponding sale with Urdu date/time fields
    sale = Sale(
        customer_name=customer.customer_name,
        item_id=item.item_id,
        quantity_sold=qty_in_base,
        sale_date=use_date,
        user_id=current_user.user_id,
        sale_day=sale_urdu["sale_day"],
        sale_month=sale_urdu["sale_month"],
        sale_year=sale_urdu["sale_year"],
        sale_time=sale_urdu["sale_time"],
        sale_day_name=sale_urdu["sale_day_name"]
    )
    db.add(sale)

    # Deduct inventory
    item.stock_quantity = float(item.stock_quantity) - qty_in_base

    # Commit once
    await db.commit()
    await db.refresh(udhar)
    await db.refresh(sale)
    await db.refresh(item)

    # Update summary (pass current_user!)
    await update_udhar_summary(db, customer.customer_id, current_user)

    return udhar


async def get_udhar_by_id(db: AsyncSession, udhar_id: int, current_user: User):
    result = await db.execute(
        select(UdharItem).where(UdharItem.udharitem_id == udhar_id, UdharItem.user_id == current_user.user_id)
    )
    return result.scalar_one_or_none()


async def list_udharitems(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(UdharItem).where(UdharItem.user_id == current_user.user_id).order_by(UdharItem.date_.desc())
    )
    return res.scalars().all()


async def list_udharitems_by_customer(db: AsyncSession, customer_id: int, current_user: User):
    res = await db.execute(
        select(UdharItem)
        .where(UdharItem.customer_id == customer_id, UdharItem.user_id == current_user.user_id)
        .order_by(UdharItem.date_.desc())
    )
    return res.scalars().all()
