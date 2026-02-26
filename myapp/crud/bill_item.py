from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, datetime
from fastapi import HTTPException

from myapp.models.bill_item import BillItem
from myapp.models.bill import Bill
from myapp.models.item import Item
from myapp.models.sales import Sale
from myapp.models.user import User
from myapp.utils.units import UnitConverter
from myapp.utils.urdu_date import convert_datetime_to_urdu


async def create_bill_item(db: AsyncSession, data: dict, current_user: User):
    # Find item by name scoped to user
    res = await db.execute(
        select(Item).where(Item.item_name == data["item_name"], Item.user_id == current_user.user_id)
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")

    # Unit conversion check
    converter = UnitConverter()
    if not converter.is_compatible(item.item_unit, data["requested_unit"]):
        raise HTTPException(
            status_code=400,
            detail=f"اکائی '{data['requested_unit']}' آئٹم کی اکائی '{item.item_unit}' کے ساتھ مطابقت نہیں رکھتی"
        )

    # Always convert requested unit → item base unit
    qty_in_base = converter.convert(data["requested_unit"], item.item_unit, data["quantity"])

    # Inventory check
    if qty_in_base > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item.item_unit}, درکار: {qty_in_base} {item.item_unit}"
        )

    # Calculate total
    unit_price_base = float(item.unit_price)
    total_amount = unit_price_base * qty_in_base

    # Get Urdu date/time fields separately for each entity
    urdu_bill = convert_datetime_to_urdu(datetime.now(), prefix="bill")
    urdu_billitem = convert_datetime_to_urdu(datetime.now(), prefix="billitem")
    urdu_sale = convert_datetime_to_urdu(datetime.now(), prefix="sale")

    # Create bill (direct paid bill)
    bill = Bill(
        customer_id=None,  # direct customer
        user_id=current_user.user_id,
        effective_total=total_amount,
        status="paid",
        bill_day=urdu_bill["bill_day"],
        bill_month=urdu_bill["bill_month"],
        bill_year=urdu_bill["bill_year"],
        bill_time=urdu_bill["bill_time"],
        bill_day_name=urdu_bill["bill_day_name"]
    )
    db.add(bill)
    await db.flush()  # ensures bill_id is available

    # Create bill item
    bill_item = BillItem(
        bill_id=bill.bill_id,
        item_id=item.item_id,
        unit_price=unit_price_base,
        quantity=data["quantity"],  # original requested quantity
        requested_unit=data["requested_unit"],
        total_amount=total_amount,
        date_=date.today(),
        user_id=current_user.user_id,
        billitem_day=urdu_billitem["billitem_day"],
        billitem_month=urdu_billitem["billitem_month"],
        billitem_year=urdu_billitem["billitem_year"],
        billitem_time=urdu_billitem["billitem_time"],
        billitem_day_name=urdu_billitem["billitem_day_name"]
    )
    db.add(bill_item)

    # Also create a sale record (always in base unit)
    sale = Sale(
        customer_name="نقد",  # Cash customer
        item_id=item.item_id,
        quantity_sold=float(data["quantity"]),  # keep float for fractional units
        sale_date=date.today(),
        user_id=current_user.user_id,
        sale_day=urdu_sale["sale_day"],
        sale_month=urdu_sale["sale_month"],
        sale_year=urdu_sale["sale_year"],
        sale_time=urdu_sale["sale_time"],
        sale_day_name=urdu_sale["sale_day_name"]
    )
    db.add(sale)

    # Deduct stock (in base unit)
    item.stock_quantity = float(item.stock_quantity) - qty_in_base

    await db.commit()
    await db.refresh(bill_item)
    return bill_item


async def list_bill_items(db: AsyncSession, current_user: User):
    # Fetch all bill items scoped to the current user
    res = await db.execute(
        select(BillItem).where(BillItem.user_id == current_user.user_id)
    )
    return res.scalars().all()
