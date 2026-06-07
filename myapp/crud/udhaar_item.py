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
from myapp.services.email import low_stock_template, send_email_async

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
from fastapi import BackgroundTasks  # if not added

async def create_udhar(
    db: AsyncSession,
    customer_name: str,
    item_name: str,
    quantity: float,
    unit: str,
    current_user: User,
    background_tasks: BackgroundTasks
):
    # ================= VALIDATION =================
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="⚠️ مقدار صفر یا منفی نہیں ہو سکتی - براہ کرم درست مقدار درج کریں")

    # Get or create customer
    customer = await get_or_create_customer(db, customer_name, current_user)
    if not customer:
        raise HTTPException(status_code=404, detail="❌ گاہک موجود نہیں ہے یا بنایا نہیں جا سکتا")

    # Get item
    item = await get_item_by_name(db, item_name, current_user)
    if not item:
        raise HTTPException(status_code=404, detail="❌ آئٹم موجود نہیں ہے - براہ کرم درست آئٹم کا نام درج کریں")

    requested_unit = str(unit).strip()
    if not requested_unit:
        raise HTTPException(status_code=400, detail="⚠️ اکائی ضروری ہے - براہ کرم اکائی منتخب کریں")

    item_unit = str(item.item_unit).strip()
    requested_quantity = float(quantity)

    # ================= UNIT CONVERSION LOGIC =================
    # Normalize both units to their base form (e.g., "آدھا درجن" -> ("درجن", 0.5))
    normalized_item_unit, item_factor = converter.normalize_unit(item_unit, 1)
    normalized_requested_unit, requested_factor = converter.normalize_unit(requested_unit, 1)
    
    # Calculate base quantity in the normalized unit (e.g., in "درجن")
    quantity_in_normalized = requested_quantity * requested_factor
    
    if normalized_requested_unit == normalized_item_unit:
        # Same unit family (both are dozen-based)
        # Convert to item's actual unit
        base_quantity = quantity_in_normalized / item_factor
        display_quantity = requested_quantity
        display_unit = requested_unit
    else:
        # Different unit families - need compatibility check
        if not converter.is_compatible(normalized_requested_unit, normalized_item_unit):
            raise HTTPException(
                status_code=400,
                detail=f"❌ '{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا - یہ اکائیاں مختلف اقسام کی ہیں (مثال: کلو کو درجن میں تبدیل نہیں کر سکتے)"
            )
        
        try:
            # Convert from normalized requested unit to normalized item unit
            converted_value = converter.convert(
                from_unit=normalized_requested_unit,
                to_unit=normalized_item_unit,
                value=quantity_in_normalized
            )
            # Then convert to item's actual unit
            base_quantity = converted_value / item_factor
            display_quantity = requested_quantity
            display_unit = requested_unit
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"❌ یونٹ تبدیل نہیں ہو سکتا: {str(e)} - براہ کرم صحیح اکائی منتخب کریں")

    # ================= STOCK CHECK =================
    if base_quantity > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"⚠️ ذخیرہ ناکافی ہے! موجودہ اسٹاک: {item.stock_quantity} {item_unit} - آپ {base_quantity} {item_unit} لینا چاہتے ہیں"
        )

    # ================= UPDATE STOCK =================
    item.stock_quantity -= base_quantity

    # ================= LOW STOCK ALERT =================
    # ================= LOW STOCK ALERT WITH RETRY =================
    if float(item.stock_quantity) <= 9:
        try:
            subject = f"⚠️ کم اسٹاک الرٹ: {item.item_name}"
            body = low_stock_template(
                item_name=item.item_name,
                stock=item.stock_quantity,
                unit=item.item_unit
            )
            # Use background tasks for async email
            background_tasks.add_task(
                send_email_async,  # Changed from send_email
                current_user.email,
                subject,
                body
            )
            print(f"✅ کم اسٹاک ای میل بھیجنے کے لیے قطار میں لگا دیا گیا: {item.item_name}")
        except Exception as e:
            print(f"⚠️ کم اسٹاک ای میل قطار میں لگانے میں خرابی: {str(e)}")
        # ================= GET OR CREATE UDHAR RECORD =================
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

    # ================= CALCULATE TOTAL AMOUNT =================
    # Calculate total based on base quantity (in item's actual unit)
    total_amount = Decimal(str(base_quantity)) * Decimal(str(item.unit_price))

    # ================= DATE FOR UDHAR =================
    now = datetime.now()
    urdu_udhar = convert_datetime_to_urdu(now, prefix="udhar")
    urdu_sale = convert_datetime_to_urdu(now, prefix="sale")

    # ================= CREATE UDHAR ITEM =================
    new_item = UdharItem(
        udhar_id=udhar.udhar_id,
        customer_id=customer.customer_id,
        item_id=item.item_id,
        item_name=item.item_name,  # Snapshot stored
        base_unit=item.item_unit,
        requested_unit=display_unit,  # User's requested unit
        user_id=current_user.user_id,
        quantity=Decimal(str(display_quantity)),  # ✅ User's entered quantity (FIXED)
        unit_price=float(item.unit_price),
        total_amount=total_amount,
        udhar_day=urdu_udhar["udhar_day"],
        udhar_month=urdu_udhar["udhar_month"],
        udhar_year=urdu_udhar["udhar_year"],
        udhar_time=urdu_udhar["udhar_time"],
        udhar_day_name=urdu_udhar["udhar_day_name"]
    )

    db.add(new_item)

    # ================= ADD TO SALE RECORD =================
    db.add(Sale(
        customer_name=customer_name,
        item_id=item.item_id,
        item_name=item.item_name,
        quantity_sold=display_quantity,  # User's entered quantity
        unit_price=float(item.unit_price),
        item_unit=display_unit,  # User's requested unit
        sale_date=date.today(),
        user_id=current_user.user_id,
        sale_day=urdu_sale["sale_day"],
        sale_month=urdu_sale["sale_month"],
        sale_year=urdu_sale["sale_year"],
        sale_time=urdu_sale["sale_time"],
        sale_day_name=urdu_sale["sale_day_name"]
    ))

    # ================= UPDATE UDHAR SUMMARY =================
    await update_udhar_summary(db, customer.customer_id, current_user)
    await db.commit()

    # ================= FETCH COMPLETE RECORD =================
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(UdharItem.udharitem_id == new_item.udharitem_id)
    )
    
    # Success message
    print(f"✅ ادھار آئٹم کامیابی سے بن گیا: {display_quantity} {display_unit} {item.item_name} - گاہک: {customer_name} - کل رقم: {total_amount} روپے")

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

    # ================= FIXED: PROPER STOCK RESTORATION WITH CONVERSION =================
    # Get the old quantity and unit from the udhar item
    old_quantity_requested = float(udhar_item.quantity)  # This is in requested_unit
    old_requested_unit = udhar_item.requested_unit
    old_item_id = udhar_item.item_id
    
    # Get the old item to restore stock
    if old_item_id:
        old_item_res = await db.execute(
            select(Item).where(Item.item_id == old_item_id)
        )
        old_item = old_item_res.scalar_one_or_none()
        if old_item:
            # Convert old quantity from requested_unit to base_unit (old_item.item_unit)
            old_item_base_unit = old_item.item_unit.strip()
            
            # Check if conversion is needed
            if old_requested_unit == old_item_base_unit:
                # Same unit, no conversion needed
                old_quantity_base = old_quantity_requested
            else:
                # Check compatibility before conversion
                if not converter.is_compatible(old_requested_unit, old_item_base_unit):
                    # If not compatible, we can't restore properly - log error but continue?
                    # Better to raise an exception to avoid data corruption
                    raise HTTPException(
                        status_code=400,
                        detail=f"پرانی اکائی '{old_requested_unit}' کو بیس اکائی '{old_item_base_unit}' میں تبدیل نہیں کیا جا سکتا"
                    )
                
                # Convert from requested_unit to base_unit
                old_quantity_base = converter.convert(
                    from_unit=old_requested_unit,
                    to_unit=old_item_base_unit,
                    value=old_quantity_requested
                )
            
            # Restore the converted quantity to stock
            old_item.stock_quantity += old_quantity_base
            db.add(old_item)
            print(f"✅ اسٹاک بحال: {old_quantity_base} {old_item_base_unit} (اصل: {old_quantity_requested} {old_requested_unit})")
    
    # Get the new item
    db_item = await get_item_by_name(db, data.item_name, current_user)

    requested_unit = data.unit.strip()
    item_unit = db_item.item_unit.strip()

    # Calculate new quantity for deduction
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

    # Check stock for new item (after restoration of old stock)
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
    udhar_item.quantity = Decimal(str(float(data.quantity)))  # Store as requested quantity
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
