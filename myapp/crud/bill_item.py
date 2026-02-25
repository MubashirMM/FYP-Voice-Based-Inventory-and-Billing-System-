from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from myapp.models.bill_item import BillItem
from myapp.models.bill import Bill
from myapp.models.item import Item
from myapp.utils.units import UnitConverter
from myapp.models.user import User
from myapp.models.sales import Sale

from datetime import date, datetime
from fastapi import HTTPException
from myapp.utils.urdu_date import convert_datetime_to_urdu

async def create_bill_item(db: AsyncSession, data: dict, current_user: User):
    # Find item by name scoped to user
    res = await db.execute(
        select(Item).where(Item.item_name == data["item_name"], Item.user_id == current_user.user_id)
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")

    # Unit conversion
    converter = UnitConverter()
    if not converter.is_compatible(item.item_unit, data["requested_unit"]):
        raise HTTPException(status_code=400, detail=f"اکائی '{data['requested_unit']}' آئٹم کی اکائی '{item.item_unit}' کے ساتھ مطابقت نہیں رکھتی")

    qty_in_base = converter.convert(item.item_unit, data["requested_unit"], data["quantity"])

    # Inventory check
    if qty_in_base > float(item.stock_quantity):
        raise HTTPException(status_code=400, detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item.item_unit}, درکار: {qty_in_base} {item.item_unit}")

    # Calculate total
    unit_price_base = float(item.unit_price)
    total_amount = unit_price_base * qty_in_base

    # Get Urdu date/time fields
    urdu_datetime = convert_datetime_to_urdu(datetime.now(), prefix="bill")
    
    # Create bill (direct paid bill)
    bill = Bill(
        customer_id=None,  # direct customer
        user_id=current_user.user_id,
        effective_total=total_amount,  # only this is updated
        status="paid",                  # explicitly set or rely on default
        bill_day=urdu_datetime.get("bill_day", ""),
        bill_month=urdu_datetime.get("bill_month", ""),
        bill_year=urdu_datetime.get("bill_year", ""),
        bill_time=urdu_datetime.get("bill_time", ""),
        bill_day_name=urdu_datetime.get("bill_day_name", "")
    )
    db.add(bill)
    await db.flush()  # ensures bill_id is available
    
    # Create bill item
    bill_item = BillItem(
        bill_id=bill.bill_id,
        item_id=item.item_id,
        unit_price=unit_price_base,
        quantity=data["quantity"],
        requested_unit=data["requested_unit"],
        total_amount=total_amount,
        date_=date.today(),
        user_id=current_user.user_id,
        billitem_day=urdu_datetime.get("billitem_day", ""),
        billitem_month=urdu_datetime.get("billitem_month", ""),
        billitem_year=urdu_datetime.get("billitem_year", ""),
        billitem_time=urdu_datetime.get("billitem_time", ""),
        billitem_day_name=urdu_datetime.get("billitem_day_name", "")
    )
    db.add(bill_item)
    
    # Also create a sale record
    sale = Sale(
        customer_name="نقد",  # Cash customer
        item_id=item.item_id,
        quantity_sold=int(data["quantity"]),
        sale_date=date.today(),
        user_id=current_user.user_id,
        sale_day=urdu_datetime.get("billitem_day", ""),
        sale_month=urdu_datetime.get("billitem_month", ""),
        sale_year=urdu_datetime.get("billitem_year", ""),
        sale_time=urdu_datetime.get("billitem_time", ""),
        sale_day_name=urdu_datetime.get("billitem_day_name", "")
    )
    db.add(sale)

    # Deduct stock
    item.stock_quantity = float(item.stock_quantity) - qty_in_base

    await db.commit()
    await db.refresh(bill_item)
    return bill_item

async def list_bill_items(db: AsyncSession, current_user: User): 
    # Fetch all bill items scoped to the current user 
    res = await db.execute( select(BillItem).where(BillItem.user_id == current_user.user_id) )
    return res.scalars().all()
