from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import date, datetime
from decimal import Decimal
from fastapi import HTTPException

from myapp.models.bill_item import BillItem
from myapp.models.bill import Bill
from myapp.models.item import Item
from myapp.models.sales import Sale
from myapp.models.user import User

from myapp.utils.units import UnitConverter
from myapp.utils.urdu_date import convert_datetime_to_urdu

# Global converter
converter = UnitConverter()


# =========================
# CREATE BILL ITEM
# =========================
async def create_bill_item(db: AsyncSession, data: dict, current_user: User):
    # Fetch item
    res = await db.execute(
        select(Item).where(
            Item.item_name == data["item_name"],
            Item.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")

    # Safe unit extraction
    requested_unit = str(data.get("requested_unit", "")).strip()
    if not requested_unit:
        raise HTTPException(status_code=400, detail="اکائی درج کرنا ضروری ہے")

    item_unit = str(item.item_unit).strip()

    # ======================
    # UNIT LOGIC - Same as create_udhar
    # ======================
    if requested_unit == item_unit:
        qty_in_base = float(data["quantity"])
    else:
        if not converter.is_compatible(requested_unit, item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"اکائی '{requested_unit}' آئٹم کی اکائی '{item_unit}' کے ساتھ مطابقت نہیں رکھتی"
            )
        try:
            qty_in_base = converter.convert(
                from_unit=requested_unit,
                to_unit=item_unit,
                value=float(data["quantity"])
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"یونٹ تبدیل نہیں ہو سکتا: {str(e)}"
            )

    # Stock check after conversion
    if qty_in_base > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {item.stock_quantity} {item_unit}"
        )

    total_amount = Decimal(str(qty_in_base)) * Decimal(str(item.unit_price))

    now = datetime.now()
    urdu_bill = convert_datetime_to_urdu(now, prefix="bill")
    urdu_billitem = convert_datetime_to_urdu(now, prefix="billitem")
    urdu_sale = convert_datetime_to_urdu(now, prefix="sale")

    # Create bill
    bill = Bill(
        customer_id=None,
        user_id=current_user.user_id,
        effective_total=float(total_amount),
        status="paid",
        bill_day=urdu_bill["bill_day"],
        bill_month=urdu_bill["bill_month"],
        bill_year=urdu_bill["bill_year"],
        bill_time=urdu_bill["bill_time"],
        bill_day_name=urdu_bill["bill_day_name"]
    )
    db.add(bill)
    await db.flush()

    # Create bill item
    bill_item = BillItem(
        bill_id=bill.bill_id,
        item_id=item.item_id,
        unit_price=float(item.unit_price),
        quantity=float(data["quantity"]),  # original user quantity
        requested_unit=requested_unit,
        total_amount=float(total_amount),
        created_date=date.today(),
        user_id=current_user.user_id,
        billitem_day=urdu_billitem["billitem_day"],
        billitem_month=urdu_billitem["billitem_month"],
        billitem_year=urdu_billitem["billitem_year"],
        billitem_time=urdu_billitem["billitem_time"],
        billitem_day_name=urdu_billitem["billitem_day_name"]
    )
    db.add(bill_item)

    # Sale record
    sale = Sale(
        customer_name="نقد",
        item_id=item.item_id,
        quantity_sold=float(data["quantity"]),
        sale_date=date.today(),
        user_id=current_user.user_id,
        sale_day=urdu_sale["sale_day"],
        sale_month=urdu_sale["sale_month"],
        sale_year=urdu_sale["sale_year"],
        sale_time=urdu_sale["sale_time"],
        sale_day_name=urdu_sale["sale_day_name"]
    )
    db.add(sale)

    # Deduct stock
    item.stock_quantity = float(item.stock_quantity) - qty_in_base

    await db.commit()
    await db.refresh(bill_item)
    return bill_item

# =========================
# LIST ALL BILL ITEMS
# =========================
async def list_bill_items(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(BillItem)
        .where(BillItem.user_id == current_user.user_id)
    )
    return res.scalars().all()


# =========================
# GET SINGLE BILL ITEM BY ID
# =========================
async def get_bill_item_by_id(db: AsyncSession, billitem_id: int, current_user: User):
    res = await db.execute(
        select(BillItem)
        .where(
            BillItem.billitem_id == billitem_id,
            BillItem.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="بل آئٹم نہیں ملا")
    return item


# =========================
# DELETE BILL ITEM
# =========================
async def delete_bill_item(db: AsyncSession, billitem_id: int, current_user: User):
    res = await db.execute(
        select(BillItem)
        .where(
            BillItem.billitem_id == billitem_id,
            BillItem.user_id == current_user.user_id
        )
    )
    bill_item = res.scalar_one_or_none()
    if not bill_item:
        raise HTTPException(status_code=404, detail="بل آئٹم نہیں ملا")

    # Restore stock
    item_res = await db.execute(
        select(Item).where(Item.item_id == bill_item.item_id)
    )
    item = item_res.scalar_one_or_none()
    if item:
        item.stock_quantity += float(bill_item.quantity)   # restore original requested quantity

    # Delete bill item
    await db.execute(
        delete(BillItem).where(
            BillItem.billitem_id == billitem_id,
            BillItem.user_id == current_user.user_id
        )
    )

    await db.commit()
    return {"message": "بل آئٹم کامیابی سے حذف کر دیا گیا"}


# =========================
# SEARCH BILL ITEMS
# =========================
async def search_bill_items(db: AsyncSession, keyword: str, current_user: User):
    res = await db.execute(
        select(BillItem)
        .where(
            BillItem.user_id == current_user.user_id,
            BillItem.item_name.ilike(f"%{keyword.strip()}%")
        )
    )
    return res.scalars().all()