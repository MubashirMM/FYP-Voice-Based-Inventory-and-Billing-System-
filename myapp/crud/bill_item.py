from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import date, datetime
from decimal import Decimal
from fastapi import HTTPException,BackgroundTasks

from myapp.models.bill_item import BillItem
from myapp.models.bill import Bill
from myapp.models.item import Item
from myapp.models.sales import Sale
from myapp.models.user import User
from myapp.models.bill_item_history import BillItemHistory

from myapp.utils.units import UnitConverter
from myapp.utils.urdu_date import convert_datetime_to_urdu
from myapp.services.email import low_stock_template, send_email

# =========================
# GLOBAL
# =========================
converter = UnitConverter()


# =========================
# FORMAT RESPONSE
# =========================
def format_bill_item(i: BillItem):
    return {
        "billitem_id": i.billitem_id,
        "bill_id": i.bill_id,
        "item_id": i.item_id,
        "item_name": i.item_name,

        # ✅ IMPORTANT
        "item_unit": i.item_unit,          # base unit
        "requested_unit": i.requested_unit,  # user entered

        "quantity": float(i.quantity),
        "unit_price": float(i.unit_price),
        "total_amount": float(i.total_amount),

        "created_date": i.created_date,

        "billitem_day": i.billitem_day,
        "billitem_month": i.billitem_month,
        "billitem_year": i.billitem_year,
        "billitem_time": i.billitem_time,
        "billitem_day_name": i.billitem_day_name,
    }


# =========================
# CREATE BILL ITEM
# =========================
from fastapi import BackgroundTasks

async def create_bill_item(
    db: AsyncSession,
    data: dict,
    current_user: User,
    background_tasks: BackgroundTasks
):
    # 🔍 Check if item exists
    res = await db.execute(
        select(Item).where(
            Item.item_name == data["item_name"],
            Item.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="❌ آئٹم موجود نہیں ہے - براہ کرم درست آئٹم کا نام درج کریں")

    requested_unit = str(data.get("requested_unit", "")).strip()
    if not requested_unit:
        raise HTTPException(status_code=400, detail="⚠️ اکائی ضروری ہے - براہ کرم اکائی منتخب کریں")

    item_unit = str(item.item_unit).strip()
    requested_quantity = float(data["quantity"])

    if requested_quantity <= 0:
        raise HTTPException(status_code=400, detail="⚠️ مقدار صفر یا منفی نہیں ہو سکتی - براہ کرم درست مقدار درج کریں")

    # ================= UNIT LOGIC =================
    # Normalize both units to their base form (e.g., "آدھا درجن" -> ("درجن", 0.5))
    normalized_item_unit, item_factor = converter.normalize_unit(item_unit, 1)
    normalized_requested_unit, requested_factor = converter.normalize_unit(requested_unit, 1)
    
    # Calculate base quantity in the normalized unit (e.g., in "درجن")
    quantity_in_normalized = requested_quantity * requested_factor
    
    if normalized_requested_unit == normalized_item_unit:
        # Same unit family (both are dozen-based)
        # Convert to item's actual unit
        qty_base = quantity_in_normalized / item_factor
        display_quantity = requested_quantity
        display_unit = requested_unit
    else:
        # Different unit families - need compatibility check
        if not converter.is_compatible(normalized_requested_unit, normalized_item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"❌ '{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا - یہ اکائیاں مختلف اقسام کی ہیں"
            )
        
        try:
            # Convert from normalized requested unit to normalized item unit
            converted_value = converter.convert(
                from_unit=normalized_requested_unit,
                to_unit=normalized_item_unit,
                value=quantity_in_normalized
            )
            # Then convert to item's actual unit
            qty_base = converted_value / item_factor
            display_quantity = requested_quantity
            display_unit = requested_unit
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"❌ یونٹ تبدیل نہیں ہو سکتا: {str(e)} - براہ کرم صحیح اکائی منتخب کریں")

    # ================= STOCK CHECK =================
    if qty_base > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"⚠️ ذخیرہ ناکافی ہے! موجودہ اسٹاک: {item.stock_quantity} {item_unit} - آپ {qty_base} {item_unit} خریدنا چاہتے ہیں"
        )

    # ================= TOTAL CALCULATION =================
    # Calculate total based on base quantity (in item's actual unit)
    total_amount = Decimal(str(qty_base)) * Decimal(str(item.unit_price))

    # ================= DATE =================
    now = datetime.now()
    urdu_bill = convert_datetime_to_urdu(now, prefix="bill")
    urdu_item = convert_datetime_to_urdu(now, prefix="billitem")
    urdu_sale = convert_datetime_to_urdu(now, prefix="sale")

    # ================= CREATE BILL =================
    bill = Bill(
        customer_id=None,
        user_id=current_user.user_id,
        udhar_items_total=0.0,
        direct_addition=0.0,
        direct_deduction=0.0,
        effective_total=float(total_amount),
        status="paid",
        bill_date=date.today(),
        bill_day=urdu_bill["bill_day"],
        bill_month=urdu_bill["bill_month"],
        bill_year=urdu_bill["bill_year"],
        bill_time=urdu_bill["bill_time"],
        bill_day_name=urdu_bill["bill_day_name"]
    )
    db.add(bill)
    await db.flush()

    # ================= CREATE BILL ITEM =================
    bill_item = BillItem(
        bill_id=bill.bill_id,
        item_id=item.item_id,
        item_name=item.item_name,
        item_unit=item.item_unit,
        unit_price=float(item.unit_price),
        quantity=display_quantity,  # User's entered quantity
        requested_unit=display_unit,  # User's requested unit
        total_amount=float(total_amount),
        created_date=date.today(),
        user_id=current_user.user_id,
        billitem_day=urdu_item["billitem_day"],
        billitem_month=urdu_item["billitem_month"],
        billitem_year=urdu_item["billitem_year"],
        billitem_time=urdu_item["billitem_time"],
        billitem_day_name=urdu_item["billitem_day_name"]
    )
    db.add(bill_item)

    # ================= ADD TO HISTORY =================
    db.add(BillItemHistory(
        bill_id=bill.bill_id,
        user_id=current_user.user_id,
        item_name=item.item_name,
        unit_price=float(item.unit_price),
        quantity=display_quantity,
        requested_unit=display_unit,
        total_amount=float(total_amount),
    ))

    # ================= ADD TO SALE RECORD =================
    db.add(Sale(
        customer_name="نقد",
        item_id=item.item_id,
        item_name=item.item_name,
        quantity_sold=display_quantity,
        unit_price=float(item.unit_price),
        item_unit=display_unit,
        sale_date=date.today(),
        user_id=current_user.user_id,
        sale_day=urdu_sale["sale_day"],
        sale_month=urdu_sale["sale_month"],
        sale_year=urdu_sale["sale_year"],
        sale_time=urdu_sale["sale_time"],
        sale_day_name=urdu_sale["sale_day_name"]
    ))

    # ================= UPDATE STOCK =================
    item.stock_quantity -= qty_base

    await db.commit()
    
    # ================= LOW STOCK ALERT =================
    if int(item.stock_quantity) <= 9:
        try:
            subject = f"⚠️ کم اسٹاک الرٹ: {item.item_name}"
            body = low_stock_template(
                item_name=item.item_name,
                stock=item.stock_quantity,
                unit=item.item_unit
            )
            background_tasks.add_task(
                send_email,
                current_user.email,
                subject,
                body
            )
        except Exception as e:
            print(f"⚠️ کم اسٹاک ای میل بھیجنے میں خرابی: {str(e)}")
    
    await db.refresh(bill_item)
    
    # Success message
    print(f"✅ بل آئٹم کامیابی سے بن گیا: {display_quantity} {display_unit} {item.item_name} - کل رقم: {total_amount} روپے")
    
    return format_bill_item(bill_item)


# =========================
# LIST
# =========================
async def list_bill_items(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(BillItem).where(BillItem.user_id == current_user.user_id)
    )
    return [format_bill_item(i) for i in res.scalars().all()]


# =========================
# GET ONE
# =========================
async def get_bill_item_by_id(db: AsyncSession, billitem_id: int, current_user: User):
    res = await db.execute(
        select(BillItem).where(
            BillItem.billitem_id == billitem_id,
            BillItem.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="بل آئٹم نہیں ملا")

    return format_bill_item(item)


# =========================
# DELETE
# =========================
async def delete_bill_item(db: AsyncSession, billitem_id: int, current_user: User):

    res = await db.execute(
        select(BillItem).where(
            BillItem.billitem_id == billitem_id,
            BillItem.user_id == current_user.user_id
        )
    )
    bill_item = res.scalar_one_or_none()

    if not bill_item:
        raise HTTPException(status_code=404, detail="بل آئٹم نہیں ملا")

    # restore stock ONLY if item exists
    if bill_item.item_id:
        res_item = await db.execute(
            select(Item).where(Item.item_id == bill_item.item_id)
        )
        item = res_item.scalar_one_or_none()
        if item:
            item.stock_quantity += float(bill_item.quantity)

    await db.execute(
        delete(BillItem).where(BillItem.billitem_id == billitem_id)
    )

    await db.commit()

    return {"message": "بل آئٹم حذف ہو گیا"}


# =========================
# SEARCH
# =========================
async def search_bill_items(db: AsyncSession, keyword: str, current_user: User):
    res = await db.execute(
        select(BillItem).where(
            BillItem.user_id == current_user.user_id,
            BillItem.item_name.ilike(f"%{keyword.strip()}%")
        )
    )
    return [format_bill_item(i) for i in res.scalars().all()]