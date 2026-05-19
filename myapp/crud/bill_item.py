
# myapp/crud/bill_item_cart.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_
from datetime import datetime, date
from decimal import Decimal
from fastapi import HTTPException, BackgroundTasks

from myapp.models.bill_item import BillItem
from myapp.models.bill import Bill
from myapp.models.item import Item
from myapp.models.sales import Sale
from myapp.models.bill_item_history import BillItemHistory
from myapp.models.user import User
from myapp.utils.units import UnitConverter
from myapp.utils.urdu_date import convert_datetime_to_urdu
from myapp.services.email import low_stock_template, send_email_async

converter = UnitConverter()


# Add this function before list_bill_items
def format_bill_item(i: BillItem):
    return {
        "billitem_id": i.billitem_id,
        "bill_id": i.bill_id,
        "item_id": i.item_id,
        "item_name": i.item_name,
        "item_unit": i.item_unit,
        "requested_unit": i.requested_unit,
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
 
def format_cart_item(item: BillItem):
    """Format pending cart item - FIXED: Include cart_item_id"""
    return {
        "cart_item_id": item.billitem_id,  # CRITICAL: Map to frontend expected name
        "billitem_id": item.billitem_id,
        "item_id": item.item_id,
        "item_name": item.item_name,
        "item_unit": item.item_unit,
        "quantity": float(item.quantity),
        "requested_unit": item.requested_unit,
        "unit_price": float(item.unit_price),
        "total_amount": float(item.total_amount),
        "base_quantity": float(item.base_quantity),
        "created_date": item.created_date,
        "billitem_day": item.billitem_day,
        "billitem_month": item.billitem_month,
        "billitem_year": item.billitem_year,
        "billitem_time": item.billitem_time,
        "billitem_day_name": item.billitem_day_name,
    }
# =========================
# ADD ITEM TO CART (NO BILL CREATED)
# =========================
async def add_to_cart(
    db: AsyncSession,
    data: dict,
    current_user: User,
    background_tasks: BackgroundTasks
):
    """Add item to cart without creating a bill"""
    
    # Check if item exists
    res = await db.execute(
        select(Item).where(
            Item.item_name == data["item_name"],
            Item.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="❌ آئٹم موجود نہیں ہے")
    
    requested_unit = str(data.get("requested_unit", "")).strip()
    if not requested_unit:
        raise HTTPException(status_code=400, detail="⚠️ اکائی ضروری ہے")
    
    requested_quantity = float(data["quantity"])
    if requested_quantity <= 0:
        raise HTTPException(status_code=400, detail="⚠️ مقدار صفر یا منفی نہیں ہو سکتی")
    
    item_unit = str(item.item_unit).strip()
    
    # Unit conversion logic
    normalized_item_unit, item_factor = converter.normalize_unit(item_unit, 1)
    normalized_requested_unit, requested_factor = converter.normalize_unit(requested_unit, 1)
    
    quantity_in_normalized = requested_quantity * requested_factor
    
    if normalized_requested_unit == normalized_item_unit:
        base_quantity = quantity_in_normalized / item_factor
        display_quantity = requested_quantity
        display_unit = requested_unit
    else:
        if not converter.is_compatible(normalized_requested_unit, normalized_item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"❌ '{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا"
            )
        
        try:
            converted_value = converter.convert(
                from_unit=normalized_requested_unit,
                to_unit=normalized_item_unit,
                value=quantity_in_normalized
            )
            base_quantity = converted_value / item_factor
            display_quantity = requested_quantity
            display_unit = requested_unit
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"❌ یونٹ تبدیل نہیں ہو سکتا: {str(e)}")
    
    # Check stock
    if base_quantity > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"⚠️ ذخیرہ ناکافی ہے! موجودہ اسٹاک: {item.stock_quantity} {item_unit}"
        )
    
    # Calculate total
    total_amount = Decimal(str(base_quantity)) * Decimal(str(item.unit_price))
    
    # Date for cart item
    now = datetime.now()
    urdu_cart = convert_datetime_to_urdu(now, prefix="billitem")
    
    # Create cart item (NO bill_id - pending)
    cart_item = BillItem(
        bill_id=None,  # ✅ Important: No bill yet
        item_id=item.item_id,
        user_id=current_user.user_id,
        item_name=item.item_name,
        item_unit=item.item_unit,
        requested_unit=display_unit,
        quantity=display_quantity,
        base_quantity=base_quantity,
        unit_price=float(item.unit_price),
        total_amount=float(total_amount),
        created_date=date.today(),
        is_pending=1,
        billitem_day=urdu_cart["billitem_day"],
        billitem_month=urdu_cart["billitem_month"],
        billitem_year=urdu_cart["billitem_year"],
        billitem_time=urdu_cart["billitem_time"],
        billitem_day_name=urdu_cart["billitem_day_name"]
    )
    
    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)
    
    return format_cart_item(cart_item)


# =========================
# GET ALL PENDING CART ITEMS
# =========================
async def get_cart_items(db: AsyncSession, current_user: User):
    """Get all pending items in cart"""
    res = await db.execute(
        select(BillItem).where(
            and_(
                BillItem.user_id == current_user.user_id,
                BillItem.is_pending == 1,
                BillItem.bill_id.is_(None)
            )
        )
    )
    items = res.scalars().all()
    return [format_cart_item(item) for item in items]


# =========================
# REMOVE ITEM FROM CART
# =========================
async def remove_from_cart(db: AsyncSession, cart_item_id: int, current_user: User):
    """Remove item from cart (restore stock)"""
    
    res = await db.execute(
        select(BillItem).where(
            and_(
                BillItem.billitem_id == cart_item_id,
                BillItem.user_id == current_user.user_id,
                BillItem.is_pending == 1
            )
        )
    )
    cart_item = res.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="کارٹ میں آئٹم نہیں ملا")
    
    # Restore stock
    res_item = await db.execute(
        select(Item).where(Item.item_id == cart_item.item_id)
    )
    item = res_item.scalar_one_or_none()
    if item:
        item.stock_quantity += cart_item.base_quantity
        db.add(item)
    
    # Delete from cart
    await db.delete(cart_item)
    await db.commit()
    
    return {"message": "✅ آئٹم کارٹ سے حذف کر دیا گیا"}


# =========================
# CLEAR ALL CART ITEMS
# =========================
async def clear_cart(db: AsyncSession, current_user: User):
    """Clear all pending items from cart (restore stock)"""
    
    res = await db.execute(
        select(BillItem).where(
            and_(
                BillItem.user_id == current_user.user_id,
                BillItem.is_pending == 1,
                BillItem.bill_id.is_(None)
            )
        )
    )
    cart_items = res.scalars().all()
    
    # Restore stock for all items
    for cart_item in cart_items:
        res_item = await db.execute(
            select(Item).where(Item.item_id == cart_item.item_id)
        )
        item = res_item.scalar_one_or_none()
        if item:
            item.stock_quantity += cart_item.base_quantity
            db.add(item)
        
        await db.delete(cart_item)
    
    await db.commit()
    
    return {"message": "✅ کارٹ خالی کر دیا گیا"}


# =========================
# GENERATE BILL FROM CART
# =========================
async def generate_bill_from_cart(
    db: AsyncSession,
    current_user: User,
    background_tasks: BackgroundTasks
):
    """Generate a single bill from all pending cart items"""
    
    # Get all pending cart items
    res = await db.execute(
        select(BillItem).where(
            and_(
                BillItem.user_id == current_user.user_id,
                BillItem.is_pending == 1,
                BillItem.bill_id.is_(None)
            )
        )
    )
    cart_items = res.scalars().all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="❌ کارٹ خالی ہے - کوئی آئٹم بل کے لیے موجود نہیں")
    
    # Calculate total bill amount
    total_bill_amount = sum(float(item.total_amount) for item in cart_items)
    
    # Create bill record
    now = datetime.now()
    urdu_bill = convert_datetime_to_urdu(now, prefix="bill")
    
    bill = Bill(
        customer_id=None,
        customer_name="نقد",  # Fixed for cash sales
        user_id=current_user.user_id,
        effective_total=float(total_bill_amount),
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
    
    # Update all cart items with bill_id and mark as not pending
    for cart_item in cart_items:
        cart_item.bill_id = bill.bill_id
        cart_item.is_pending = 0
        
        # Update stock (already deducted when added to cart, so no need to deduct again)
        # But we need to check low stock alert
        res_item = await db.execute(
            select(Item).where(Item.item_id == cart_item.item_id)
        )
        item = res_item.scalar_one_or_none()
        
        if item and int(item.stock_quantity) <= 9:
            try:
                subject = f"⚠️ کم اسٹاک الرٹ: {item.item_name}"
                body = low_stock_template(
                    item_name=item.item_name,
                    stock=item.stock_quantity,
                    unit=item.item_unit
                )
                background_tasks.add_task(
                    send_email_async,
                    current_user.email,
                    subject,
                    body
                )
            except Exception as e:
                print(f"⚠️ کم اسٹاک ای میل بھیجنے میں خرابی: {str(e)}")
        
        # Add to history
        db.add(BillItemHistory(
            bill_id=bill.bill_id,
            user_id=current_user.user_id,
            item_name=cart_item.item_name,
            unit_price=cart_item.unit_price,
            quantity=cart_item.quantity,
            requested_unit=cart_item.requested_unit,
            total_amount=cart_item.total_amount,
        ))
        
        # Add to sales record
        urdu_sale = convert_datetime_to_urdu(now, prefix="sale")
        db.add(Sale(
            customer_name="نقد",
            item_id=cart_item.item_id,
            item_name=cart_item.item_name,
            quantity_sold=cart_item.quantity,
            unit_price=cart_item.unit_price,
            item_unit=cart_item.requested_unit,
            sale_date=date.today(),
            user_id=current_user.user_id,
            sale_day=urdu_sale["sale_day"],
            sale_month=urdu_sale["sale_month"],
            sale_year=urdu_sale["sale_year"],
            sale_time=urdu_sale["sale_time"],
            sale_day_name=urdu_sale["sale_day_name"]
        ))
    
    await db.commit()
    await db.refresh(bill)
    
    # Return bill details with items
    return {
        "bill_id": bill.bill_id,
        "customer_name": bill.customer_name,
        "total_amount": bill.effective_total,
        "status": bill.status,
        "bill_date": bill.bill_date,
        "bill_day": bill.bill_day,
        "bill_month": bill.bill_month,
        "bill_year": bill.bill_year,
        "bill_time": bill.bill_time,
        "bill_day_name": bill.bill_day_name,
        "items": [format_cart_item(item) for item in cart_items]
    }

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
async def update_cart_item_quantity(
    db: AsyncSession, 
    cart_item_id: int, 
    new_quantity: float,
    requested_unit: str,
    current_user: User
):
    """Update cart item quantity"""
    try:
        # FIXED: Use billitem_id instead of id, and user_id instead of id
        result = await db.execute(
            select(BillItem).where(
                BillItem.billitem_id == cart_item_id,  # FIXED: billitem_id
                BillItem.user_id == current_user.user_id,  # FIXED: user_id
                BillItem.bill_id.is_(None)
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="کارٹ آئٹم موجود نہیں ہے")
        
        # Get original item to check stock
        res_item = await db.execute(
            select(Item).where(Item.item_id == cart_item.item_id)
        )
        item = res_item.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
        
        # Calculate new base quantity
        requested_quantity = new_quantity
        requested_unit_str = requested_unit
        
        item_unit = str(item.item_unit).strip()
        
        # Unit conversion logic
        normalized_item_unit, item_factor = converter.normalize_unit(item_unit, 1)
        normalized_requested_unit, requested_factor = converter.normalize_unit(requested_unit_str, 1)
        
        quantity_in_normalized = requested_quantity * requested_factor
        
        if normalized_requested_unit == normalized_item_unit:
            new_base_quantity = quantity_in_normalized / item_factor
        else:
            if not converter.is_compatible(normalized_requested_unit, normalized_item_unit):
                raise HTTPException(
                    status_code=400,
                    detail=f"❌ '{requested_unit_str}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا"
                )
            
            converted_value = converter.convert(
                from_unit=normalized_requested_unit,
                to_unit=normalized_item_unit,
                value=quantity_in_normalized
            )
            new_base_quantity = converted_value / item_factor
        
        # Calculate stock difference
        stock_difference = new_base_quantity - cart_item.base_quantity
        
        # Check if enough stock available
        if stock_difference > 0 and stock_difference > float(item.stock_quantity):
            raise HTTPException(
                status_code=400,
                detail=f"⚠️ ذخیرہ ناکافی ہے! موجودہ اسٹاک: {item.stock_quantity} {item_unit}"
            )
        
        # Update stock
        if stock_difference != 0:
            item.stock_quantity -= stock_difference
            db.add(item)
        
        # Update cart item
        cart_item.quantity = new_quantity
        cart_item.requested_unit = requested_unit
        cart_item.base_quantity = new_base_quantity
        cart_item.total_amount = new_base_quantity * cart_item.unit_price
        
        await db.commit()
        await db.refresh(cart_item)
        
        return {"message": "کارٹ آئٹم اپڈیٹ ہو گیا", "cart_item": cart_item}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"اپڈیٹ کرنے میں خرابی: {str(e)}")