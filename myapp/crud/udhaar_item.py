# from fastapi import HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy.orm import selectinload
# from sqlalchemy import delete

# from datetime import datetime, date
# from decimal import Decimal

# from myapp.models.udhaar_item import UdharItem
# from myapp.models.customer import Customer
# from myapp.models.item import Item
# from myapp.models.user import User
# from myapp.models.udhar import Udhar
# from myapp.models.sales import Sale

# from myapp.utils.urdu_date import convert_datetime_to_urdu
# from myapp.utils.units import UnitConverter
# from myapp.crud.udhar import update_udhar_summary
# from myapp.services.email import low_stock_template, send_email

# # =========================
# # GLOBAL
# # =========================
# converter = UnitConverter()


# # =========================
# # FORMAT
# # =========================
# def format_item(i: UdharItem):
#     return {
#         "udharitem_id": i.udharitem_id,
#         "customer_id": i.customer_id,
#         "customer_name": i.customer.customer_name if i.customer else None,

#         "item_id": i.item_id,
#         "item_name": i.item_name,   # always from stored column

#         "unit_price": float(i.unit_price),

#         "quantity": float(i.quantity),   # base quantity
#         "base_unit": i.base_unit,
#         "requested_unit": i.requested_unit,

#         "total_amount": float(i.total_amount),
#         "created_date": i.created_date,

#         "udhar_day": i.udhar_day,
#         "udhar_month": i.udhar_month,
#         "udhar_year": i.udhar_year,
#         "udhar_time": i.udhar_time,
#         "udhar_day_name": i.udhar_day_name,
#     }


# # =========================
# # HELPERS
# # =========================
# async def get_or_create_customer(db: AsyncSession, name: str, current_user: User):
#     name = name.strip()
#     if not name:
#         raise HTTPException(status_code=400, detail="کسٹمر کا نام خالی نہیں ہو سکتا")

#     res = await db.execute(
#         select(Customer).where(
#             Customer.customer_name == name,
#             Customer.user_id == current_user.user_id
#         )
#     )
#     customer = res.scalar_one_or_none()

#     if not customer:
#         customer = Customer(
#             customer_name=name,
#             user_id=current_user.user_id
#         )
#         db.add(customer)
#         await db.flush()

#     return customer


# async def get_item_by_name(db: AsyncSession, name: str, current_user: User):
#     name = name.strip()
#     if not name:
#         raise HTTPException(status_code=400, detail="آئٹم کا نام خالی نہیں ہو سکتا")

#     res = await db.execute(
#         select(Item).where(
#             Item.item_name == name,
#             Item.user_id == current_user.user_id
#         )
#     )
#     item = res.scalar_one_or_none()

#     if not item:
#         raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")

#     return item


# # =========================
# # CREATE
# # =========================
# from fastapi import BackgroundTasks  # if not added

# async def create_udhar(
#     db: AsyncSession,
#     customer_name: str,
#     item_name: str,
#     quantity: float,
#     unit: str,
#     current_user: User,
#     background_tasks: BackgroundTasks
# ):
#     # ================= VALIDATION =================
#     if quantity <= 0:
#         raise HTTPException(status_code=400, detail="⚠️ مقدار صفر یا منفی نہیں ہو سکتی - براہ کرم درست مقدار درج کریں")

#     # Get or create customer
#     customer = await get_or_create_customer(db, customer_name, current_user)
#     if not customer:
#         raise HTTPException(status_code=404, detail="❌ گاہک موجود نہیں ہے یا بنایا نہیں جا سکتا")

#     # Get item
#     item = await get_item_by_name(db, item_name, current_user)
#     if not item:
#         raise HTTPException(status_code=404, detail="❌ آئٹم موجود نہیں ہے - براہ کرم درست آئٹم کا نام درج کریں")

#     requested_unit = str(unit).strip()
#     if not requested_unit:
#         raise HTTPException(status_code=400, detail="⚠️ اکائی ضروری ہے - براہ کرم اکائی منتخب کریں")

#     item_unit = str(item.item_unit).strip()
#     requested_quantity = float(quantity)

#     # ================= UNIT CONVERSION LOGIC =================
#     # Normalize both units to their base form (e.g., "آدھا درجن" -> ("درجن", 0.5))
#     normalized_item_unit, item_factor = converter.normalize_unit(item_unit, 1)
#     normalized_requested_unit, requested_factor = converter.normalize_unit(requested_unit, 1)
    
#     # Calculate base quantity in the normalized unit (e.g., in "درجن")
#     quantity_in_normalized = requested_quantity * requested_factor
    
#     if normalized_requested_unit == normalized_item_unit:
#         # Same unit family (both are dozen-based)
#         # Convert to item's actual unit
#         base_quantity = quantity_in_normalized / item_factor
#         display_quantity = requested_quantity
#         display_unit = requested_unit
#     else:
#         # Different unit families - need compatibility check
#         if not converter.is_compatible(normalized_requested_unit, normalized_item_unit):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"❌ '{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا - یہ اکائیاں مختلف اقسام کی ہیں (مثال: کلو کو درجن میں تبدیل نہیں کر سکتے)"
#             )
        
#         try:
#             # Convert from normalized requested unit to normalized item unit
#             converted_value = converter.convert(
#                 from_unit=normalized_requested_unit,
#                 to_unit=normalized_item_unit,
#                 value=quantity_in_normalized
#             )
#             # Then convert to item's actual unit
#             base_quantity = converted_value / item_factor
#             display_quantity = requested_quantity
#             display_unit = requested_unit
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=f"❌ یونٹ تبدیل نہیں ہو سکتا: {str(e)} - براہ کرم صحیح اکائی منتخب کریں")

#     # ================= STOCK CHECK =================
#     if base_quantity > float(item.stock_quantity):
#         raise HTTPException(
#             status_code=400,
#             detail=f"⚠️ ذخیرہ ناکافی ہے! موجودہ اسٹاک: {item.stock_quantity} {item_unit} - آپ {base_quantity} {item_unit} لینا چاہتے ہیں"
#         )

#     # ================= UPDATE STOCK =================
#     item.stock_quantity -= base_quantity

#     # ================= LOW STOCK ALERT =================
#     if int(item.stock_quantity) <= 9:
#         try:
#             subject = f"⚠️ کم اسٹاک الرٹ: {item.item_name}"
#             body = low_stock_template(
#                 item_name=item.item_name,
#                 stock=item.stock_quantity,
#                 unit=item.item_unit
#             )
#             background_tasks.add_task(
#                 send_email,
#                 current_user.email,
#                 subject,
#                 body
#             )
#         except Exception as e:
#             print(f"⚠️ کم اسٹاک ای میل بھیجنے میں خرابی: {str(e)}")

#     # ================= GET OR CREATE UDHAR RECORD =================
#     res = await db.execute(
#         select(Udhar).where(
#             Udhar.customer_id == customer.customer_id,
#             Udhar.user_id == current_user.user_id,
#             Udhar.status == "unpaid"
#         )
#     )
#     udhar = res.scalar_one_or_none()

#     if not udhar:
#         udhar = Udhar(
#             customer_id=customer.customer_id,
#             user_id=current_user.user_id,
#             status="unpaid"
#         )
#         db.add(udhar)
#         await db.flush()

#     # ================= CALCULATE TOTAL AMOUNT =================
#     # Calculate total based on base quantity (in item's actual unit)
#     total_amount = Decimal(str(base_quantity)) * Decimal(str(item.unit_price))

#     # ================= DATE FOR UDHAR =================
#     now = datetime.now()
#     urdu_udhar = convert_datetime_to_urdu(now, prefix="udhar")
#     urdu_sale = convert_datetime_to_urdu(now, prefix="sale")

#     # ================= CREATE UDHAR ITEM =================
#     new_item = UdharItem(
#         udhar_id=udhar.udhar_id,
#         customer_id=customer.customer_id,
#         item_id=item.item_id,
#         item_name=item.item_name,  # Snapshot stored
#         base_unit=item.item_unit,
#         requested_unit=display_unit,  # User's requested unit
#         user_id=current_user.user_id,
#         quantity=Decimal(str(display_quantity)),  # ✅ User's entered quantity (FIXED)
#         unit_price=float(item.unit_price),
#         total_amount=total_amount,
#         udhar_day=urdu_udhar["udhar_day"],
#         udhar_month=urdu_udhar["udhar_month"],
#         udhar_year=urdu_udhar["udhar_year"],
#         udhar_time=urdu_udhar["udhar_time"],
#         udhar_day_name=urdu_udhar["udhar_day_name"]
#     )

#     db.add(new_item)

#     # ================= ADD TO SALE RECORD =================
#     db.add(Sale(
#         customer_name=customer_name,
#         item_id=item.item_id,
#         item_name=item.item_name,
#         quantity_sold=display_quantity,  # User's entered quantity
#         unit_price=float(item.unit_price),
#         item_unit=display_unit,  # User's requested unit
#         sale_date=date.today(),
#         user_id=current_user.user_id,
#         sale_day=urdu_sale["sale_day"],
#         sale_month=urdu_sale["sale_month"],
#         sale_year=urdu_sale["sale_year"],
#         sale_time=urdu_sale["sale_time"],
#         sale_day_name=urdu_sale["sale_day_name"]
#     ))

#     # ================= UPDATE UDHAR SUMMARY =================
#     await update_udhar_summary(db, customer.customer_id, current_user)
#     await db.commit()

#     # ================= FETCH COMPLETE RECORD =================
#     res = await db.execute(
#         select(UdharItem)
#         .options(selectinload(UdharItem.customer))
#         .where(UdharItem.udharitem_id == new_item.udharitem_id)
#     )
    
#     # Success message
#     print(f"✅ ادھار آئٹم کامیابی سے بن گیا: {display_quantity} {display_unit} {item.item_name} - گاہک: {customer_name} - کل رقم: {total_amount} روپے")

#     return format_item(res.scalar_one())

# # =========================
# # UPDATE
# # =========================
# async def update_udharitem(db: AsyncSession, item_id: int, data, current_user: User):
#     # Get the udhar item
#     res = await db.execute(
#         select(UdharItem).where(
#             UdharItem.udharitem_id == item_id,
#             UdharItem.user_id == current_user.user_id
#         )
#     )
#     udhar_item = res.scalar_one_or_none()

#     if not udhar_item:
#         raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

#     # ❗ IMPORTANT: deleted item check
#     if udhar_item.item_id is None:
#         raise HTTPException(
#             status_code=400,
#             detail="یہ آئٹم ڈیلیٹ ہو چکا ہے، اپڈیٹ ممکن نہیں"
#         )

#     # Get customer info
#     customer_res = await db.execute(
#         select(Customer).where(Customer.customer_id == udhar_item.customer_id)
#     )
#     customer = customer_res.scalar_one_or_none()
#     customer_name = customer.customer_name if customer else "نامعلوم"

#     # Get the old quantity to restore stock
#     old_quantity = float(udhar_item.quantity)
#     old_item_id = udhar_item.item_id
    
#     # Get the old item to restore stock
#     if old_item_id:
#         old_item_res = await db.execute(
#             select(Item).where(Item.item_id == old_item_id)
#         )
#         old_item = old_item_res.scalar_one_or_none()
#         if old_item:
#             # Restore old stock
#             old_item.stock_quantity += old_quantity
#             db.add(old_item)
    
#     # Get the new item
#     db_item = await get_item_by_name(db, data.item_name, current_user)

#     requested_unit = data.unit.strip()
#     item_unit = db_item.item_unit.strip()

#     # Calculate new quantity
#     if requested_unit == item_unit:
#         base_quantity = float(data.quantity)
#     else:
#         if not converter.is_compatible(requested_unit, item_unit):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"'{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا"
#             )

#         base_quantity = converter.convert(
#             from_unit=requested_unit,
#             to_unit=item_unit,
#             value=float(data.quantity)
#         )

#     # Check stock for new item
#     if base_quantity > float(db_item.stock_quantity):
#         raise HTTPException(
#             status_code=400,
#             detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {db_item.stock_quantity} {item_unit}"
#         )

#     # Deduct new stock
#     db_item.stock_quantity -= base_quantity
#     db.add(db_item)

#     # Update udhar item
#     udhar_item.item_id = db_item.item_id
#     udhar_item.item_name = db_item.item_name
#     udhar_item.base_unit = db_item.item_unit
#     udhar_item.quantity = Decimal(str(base_quantity))
#     udhar_item.requested_unit = requested_unit
#     udhar_item.unit_price = db_item.unit_price
#     udhar_item.total_amount = Decimal(str(base_quantity)) * Decimal(str(db_item.unit_price))
    
#     db.add(udhar_item)

#     # ================= UPDATE SALE RECORD =================
#     # Find the corresponding sale record for this udhar item
#     sale_res = await db.execute(
#         select(Sale).where(
#             Sale.customer_name == customer_name,
#             Sale.item_id == old_item_id,  # Old item ID
#             Sale.user_id == current_user.user_id
#         )
#         .order_by(Sale.sale_id.desc())
#         .limit(1)
#     )
#     sale = sale_res.scalar_one_or_none()
    
#     if sale:
#         # Update the existing sale record
#         sale.item_id = db_item.item_id
#         sale.item_name = db_item.item_name
#         sale.quantity_sold = float(data.quantity)  # User entered quantity
#         sale.unit_price = db_item.unit_price
#         sale.item_unit = requested_unit
#         db.add(sale)
#     else:
#         # Create a new sale record if not found
#         now = datetime.now()
#         urdu_sale = convert_datetime_to_urdu(now, prefix="sale")
        
#         new_sale = Sale(
#             customer_name=customer_name,
#             item_id=db_item.item_id,
#             item_name=db_item.item_name,
#             quantity_sold=float(data.quantity),
#             unit_price=db_item.unit_price,
#             item_unit=requested_unit,
#             sale_date=date.today(),
#             user_id=current_user.user_id,
#             sale_day=urdu_sale["sale_day"],
#             sale_month=urdu_sale["sale_month"],
#             sale_year=urdu_sale["sale_year"],
#             sale_time=urdu_sale["sale_time"],
#             sale_day_name=urdu_sale["sale_day_name"]
#         )
#         db.add(new_sale)

#     # Commit changes
#     await db.commit()
#     await db.refresh(udhar_item)
    
#     # Update udhar summary (this will also sync bill)
#     await update_udhar_summary(db, udhar_item.customer_id, current_user)

#     # Refresh again to get latest data
#     await db.refresh(udhar_item)
    
#     # Get fresh udhar item with customer relationship
#     fresh_res = await db.execute(
#         select(UdharItem)
#         .options(selectinload(UdharItem.customer))
#         .where(UdharItem.udharitem_id == udhar_item.udharitem_id)
#     )
#     fresh_item = fresh_res.scalar_one()
    
#     return format_item(fresh_item)

# # =========================
# # DELETE
# # =========================
# async def delete_udharitem(db, item_id, current_user):
#     res = await db.execute(
#         select(UdharItem).where(
#             UdharItem.udharitem_id == item_id,
#             UdharItem.user_id == current_user.user_id
#         )
#     )
#     item = res.scalar_one_or_none()

#     if not item:
#         raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

#     customer_id = item.customer_id

#     await db.execute(
#         delete(UdharItem).where(UdharItem.udharitem_id == item_id)
#     )

#     await db.commit()
#     await update_udhar_summary(db, customer_id, current_user)

#     return {"message": "آئٹم کامیابی سے حذف کر دیا گیا"}


# # =========================
# # LIST
# # =========================
# async def list_udharitems(db, current_user):
#     res = await db.execute(
#         select(UdharItem)
#         .options(selectinload(UdharItem.customer))
#         .where(UdharItem.user_id == current_user.user_id)
#     )

#     items = res.scalars().all()
#     return [format_item(i) for i in items]

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, and_

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

# Cache for customer lookups (simple dict cache)
_customer_cache = {}

# =========================
# FORMAT - OPTIMIZED (no extra processing)
# =========================
def format_item(i: UdharItem):
    return {
        "udharitem_id": i.udharitem_id,
        "customer_id": i.customer_id,
        "customer_name": i.customer.customer_name if i.customer else None,
        "item_id": i.item_id,
        "item_name": i.item_name,
        "unit_price": float(i.unit_price),
        "quantity": float(i.quantity),
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
# HELPERS - OPTIMIZED with eager loading
# =========================
async def get_or_create_customer_optimized(db: AsyncSession, name: str, current_user: User):
    """Optimized customer lookup with cache"""
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="کسٹمر کا نام خالی نہیں ہو سکتا")
    
    # Check cache first
    cache_key = f"{current_user.user_id}_{name}"
    if cache_key in _customer_cache:
        return _customer_cache[cache_key]
    
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
    
    # Store in cache
    _customer_cache[cache_key] = customer
    return customer


async def get_item_by_name_optimized(db: AsyncSession, name: str, current_user: User):
    """Optimized item lookup"""
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
# CREATE - OPTIMIZED with single query for udhar
# =========================
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
        raise HTTPException(status_code=400, detail="⚠️ مقدار صفر یا منفی نہیں ہو سکتی")
    
    # Get or create customer (optimized)
    customer = await get_or_create_customer_optimized(db, customer_name, current_user)
    
    # Get item (optimized)
    item = await get_item_by_name_optimized(db, item_name, current_user)
    
    requested_unit = str(unit).strip()
    if not requested_unit:
        raise HTTPException(status_code=400, detail="⚠️ اکائی ضروری ہے")
    
    item_unit = str(item.item_unit).strip()
    requested_quantity = float(quantity)
    
    # ================= UNIT CONVERSION =================
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
        
        converted_value = converter.convert(
            from_unit=normalized_requested_unit,
            to_unit=normalized_item_unit,
            value=quantity_in_normalized
        )
        base_quantity = converted_value / item_factor
        display_quantity = requested_quantity
        display_unit = requested_unit
    
    # ================= STOCK CHECK =================
    if base_quantity > float(item.stock_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"⚠️ ذخیرہ ناکافی ہے! موجودہ اسٹاک: {item.stock_quantity} {item_unit}"
        )
    
    # ================= UPDATE STOCK =================
    item.stock_quantity -= base_quantity
    
    # ================= LOW STOCK ALERT =================
    if int(item.stock_quantity) <= 9:
        try:
            background_tasks.add_task(
                send_email,
                current_user.email,
                f"⚠️ کم اسٹاک الرٹ: {item.item_name}",
                low_stock_template(item_name=item.item_name, stock=item.stock_quantity, unit=item.item_unit)
            )
        except Exception as e:
            print(f"⚠️ کم اسٹاک ای میل بھیجنے میں خرابی: {str(e)}")
    
    # ================= GET OR CREATE UDHAR RECORD (OPTIMIZED - single query with selectinload) =================
    res = await db.execute(
        select(Udhar)
        .where(
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
        item_name=item.item_name,
        base_unit=item.item_unit,
        requested_unit=display_unit,
        user_id=current_user.user_id,
        quantity=Decimal(str(display_quantity)),
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
    
    # ================= UPDATE UDHAR SUMMARY =================
    await update_udhar_summary(db, customer.customer_id, current_user)
    await db.commit()
    
    # ================= FETCH COMPLETE RECORD (OPTIMIZED with eager loading) =================
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(UdharItem.udharitem_id == new_item.udharitem_id)
    )
    
    return format_item(res.scalar_one())


# =========================
# UPDATE - OPTIMIZED with fewer queries
# =========================
async def update_udharitem(db: AsyncSession, item_id: int, data, current_user: User):
    # Get udhar item with customer in one query
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    udhar_item = res.scalar_one_or_none()
    
    if not udhar_item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")
    
    if udhar_item.item_id is None:
        raise HTTPException(status_code=400, detail="یہ آئٹم ڈیلیٹ ہو چکا ہے")
    
    customer_name = udhar_item.customer.customer_name if udhar_item.customer else "نامعلوم"
    
    # Get old item and restore stock (single query)
    if udhar_item.item_id:
        old_item_res = await db.execute(
            select(Item).where(Item.item_id == udhar_item.item_id)
        )
        old_item = old_item_res.scalar_one_or_none()
        if old_item:
            old_item.stock_quantity += float(udhar_item.quantity)
            db.add(old_item)
    
    # Get new item
    db_item = await get_item_by_name_optimized(db, data.item_name, current_user)
    
    requested_unit = data.unit.strip()
    item_unit = db_item.item_unit.strip()
    
    # Calculate new quantity
    if requested_unit == item_unit:
        base_quantity = float(data.quantity)
    else:
        if not converter.is_compatible(requested_unit, item_unit):
            raise HTTPException(status_code=400, detail=f"'{requested_unit}' کو '{item_unit}' میں تبدیل نہیں کیا جا سکتا")
        
        base_quantity = converter.convert(
            from_unit=requested_unit,
            to_unit=item_unit,
            value=float(data.quantity)
        )
    
    # Check stock
    if base_quantity > float(db_item.stock_quantity):
        raise HTTPException(status_code=400, detail=f"ذخیرہ ناکافی ہے۔ موجودہ: {db_item.stock_quantity} {item_unit}")
    
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
    
    # Update or create sale record (optimized)
    sale_res = await db.execute(
        select(Sale)
        .where(
            Sale.customer_name == customer_name,
            Sale.item_id == udhar_item.item_id,
            Sale.user_id == current_user.user_id
        )
        .order_by(Sale.sale_id.desc())
        .limit(1)
    )
    sale = sale_res.scalar_one_or_none()
    
    if sale:
        sale.quantity_sold = float(data.quantity)
        sale.unit_price = db_item.unit_price
        sale.item_unit = requested_unit
        db.add(sale)
    else:
        now = datetime.now()
        urdu_sale = convert_datetime_to_urdu(now, prefix="sale")
        db.add(Sale(
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
        ))
    
    await db.commit()
    await update_udhar_summary(db, udhar_item.customer_id, current_user)
    await db.refresh(udhar_item)
    
    # Return formatted item with customer data
    return format_item(udhar_item)


# =========================
# DELETE - OPTIMIZED
# =========================
async def delete_udharitem(db: AsyncSession, item_id: int, current_user: User):
    # Get item with customer_id only (no need to load all relationships)
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
    
    # Direct delete without additional query
    await db.execute(
        delete(UdharItem).where(UdharItem.udharitem_id == item_id)
    )
    
    await db.commit()
    await update_udhar_summary(db, customer_id, current_user)
    
    return {"message": "آئٹم کامیابی سے حذف کر دیا گیا"}


# =========================
# LIST - OPTIMIZED with pagination
# =========================
async def list_udharitems(db: AsyncSession, current_user: User, limit: int = 100, offset: int = 0):
    """Optimized list with pagination to prevent loading all records"""
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(UdharItem.user_id == current_user.user_id)
        .order_by(UdharItem.udharitem_id.desc())
        .limit(limit)
        .offset(offset)
    )
    
    items = res.scalars().all()
    return [format_item(i) for i in items]


# =========================
# GET BY CUSTOMER - OPTIMIZED with direct query (NO Python filtering)
# =========================
async def get_udharitems_by_customer_optimized(db: AsyncSession, customer_name: str, current_user: User):
    """Optimized - direct database query instead of filtering in Python"""
    # First get customer
    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == customer_name.strip(),
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()
    
    if not customer:
        return []  # Return empty list instead of 404 for performance
    
    # Direct query for udhar items
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(
            UdharItem.customer_id == customer.customer_id,
            UdharItem.user_id == current_user.user_id
        )
        .order_by(UdharItem.udharitem_id.desc())
    )
    
    items = res.scalars().all()
    return [format_item(i) for i in items]


# =========================
# GET SINGLE - OPTIMIZED
# =========================
async def get_udharitem_by_id_optimized(db: AsyncSession, item_id: int, current_user: User):
    """Optimized single item fetch"""
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")
    
    return format_item(item)


# =========================
# SEARCH - OPTIMIZED with direct query
# =========================
async def search_udharitems_optimized(db: AsyncSession, keyword: str, current_user: User, limit: int = 50):
    """Optimized search - direct database query with LIKE"""
    keyword = f"%{keyword.strip().lower()}%"
    
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer))
        .where(
            UdharItem.user_id == current_user.user_id,
            UdharItem.item_name.ilike(keyword)
        )
        .limit(limit)
    )
    
    items = res.scalars().all()
    return [format_item(i) for i in items]