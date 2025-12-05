# crud/udharitem.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date as date_cls

from myapp.models.customer import Customer
from myapp.models.item import Item
from myapp.models.udhaar_item import UdharItem  # ← Fixed import name
from myapp.models.sales import Sale
from myapp.utils.units import UnitConverter
from myapp.crud.udhar import update_udhar_summary

async def create_udhar(
    db: AsyncSession, 
    customer_name: str, 
    item_name: str, 
    quantity: float, 
    unit: str, 
    req_date: date_cls | None = None
):
    """Create udhar record - accepts user input (names)"""
    # 1) Validate quantity (already done in schema, but double-check)
    if quantity <= 0:
        raise ValueError("مقدار صفر یا منفی نہیں ہو سکتی")

    # 2) Fetch item
    item_res = await db.execute(
        select(Item).where(Item.item_name == item_name)
    )
    item = item_res.scalar_one_or_none()
    if not item:
        raise ValueError(f"آئٹم '{item_name}' موجود نہیں ہے")

    # 3) Validate unit compatibility
    converter = UnitConverter()
    if not converter.is_compatible(item.item_unit, unit):
        raise ValueError(f"اکائی '{unit}' آئٹم کی بنیادی اکائی '{item.item_unit}' کے ساتھ مطابقت نہیں رکھتی")

    # 4) Fetch or create customer
    cust_res = await db.execute(
        select(Customer).where(Customer.customer_name == customer_name)
    )
    customer = cust_res.scalar_one_or_none()
    
    if not customer:
        customer = Customer(customer_name=customer_name)
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

    # 5) Convert to base unit for calculations
    qty_in_base = converter.convert(item.item_unit, unit, quantity)

    # 6) Inventory check
    if qty_in_base > float(item.stock_quantity):
        raise ValueError(f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item.item_unit}, درکار: {qty_in_base} {item.item_unit}")

    # 7) Calculate total (price per base unit × normalized quantity)
    unit_price_base = float(item.unit_price)
    total_amount = unit_price_base * qty_in_base

    # 8) Prepare date
    use_date = req_date or date_cls.today()

    # 9) Create udhar record (store original requested qty and unit)
    udhar = UdharItem(
        customer_id=customer.customer_id,
        item_id=item.item_id,
        unit_price=unit_price_base,
        quantity=quantity,  # Store original quantity
        requested_unit=unit.strip(),
        total_amount=total_amount,
        date_=use_date,  # ← Match model field name
    )
    db.add(udhar)

    # 10) Create corresponding sale
    sale = Sale(
        customer_id=customer.customer_id,
        item_id=item.item_id,
        quantity_sold=qty_in_base,  # In base units
        dat=use_date,
    )
    db.add(sale)

    # 11) Deduct inventory (in base units)
    item.stock_quantity = float(item.stock_quantity) - qty_in_base

    # 12) Commit once
    await db.commit()
    await db.refresh(udhar)
    await db.refresh(sale)
    await db.refresh(item)

    # 13) Update main Udhar summary table
    await update_udhar_summary(db, customer.customer_id)

    return udhar

async def get_udhar_by_id(db: AsyncSession, udhar_id: int):
    """Get single udhar item by ID"""
    result = await db.execute(
        select(UdharItem).where(UdharItem.udharitem_id == udhar_id)
    )
    return result.scalar_one_or_none()

async def list_udharitems(db: AsyncSession):
    """List all udhar items"""
    res = await db.execute(select(UdharItem).order_by(UdharItem.date_.desc()))
    return res.scalars().all()

async def list_udharitems_by_customer(db: AsyncSession, customer_id: int):
    """List udhar items for specific customer"""
    res = await db.execute(
        select(UdharItem)
        .where(UdharItem.customer_id == customer_id)
        .order_by(UdharItem.date.desc())
    )
    return res.scalars().all()