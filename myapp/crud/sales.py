from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, or_, update
from datetime import date, datetime
from fastapi import HTTPException, status

from myapp.models.sales import Sale
from myapp.models.user import User
from myapp.models.item import Item
from myapp.utils.urdu_date import get_urdu_date_components


# ✅ CREATE SALE (with snapshot data)
async def create_sale(db: AsyncSession, sale_data: dict, current_user: User):
    # Validate required fields
    if not sale_data.get("customer_name"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="گاہک کا نام درکار ہے۔"
        )
    
    if not sale_data.get("item_name"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="آئٹم کا نام درکار ہے۔"
        )
    
    if sale_data.get("quantity_sold", 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="مقدار صفر سے زیادہ ہونی چاہیے۔"
        )
    
    # If item_id is provided, get item details for snapshot
    if sale_data.get("item_id"):
        stmt = select(Item).where(Item.item_id == sale_data["item_id"])
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if item:
            # Use item details for snapshot
            sale_data["item_name"] = item.item_name
            if not sale_data.get("unit_price"):
                sale_data["unit_price"] = item.unit_price
            if not sale_data.get("item_unit"):
                sale_data["item_unit"] = item.item_unit
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="منتخب کردہ آئٹم موجود نہیں ہے۔"
            )
    
    # Add Urdu date components
    sale_date = sale_data.get("sale_date", date.today())
    urdu_components = get_urdu_date_components(sale_date)
    sale_data.update(urdu_components)
    
    new_sale = Sale(**sale_data, user_id=current_user.user_id)
    db.add(new_sale)
    await db.commit()
    await db.refresh(new_sale)
    return new_sale


# ✅ GET SALES (WITH SEARCH)
async def get_sales(
    db: AsyncSession,
    current_user: User,
    search: str = None,
    start_date: date = None,
    end_date: date = None,
    skip: int = 0,
    limit: int = 100
):
    stmt = select(Sale).where(Sale.user_id == current_user.user_id)
    
    # If search is provided, search in both customer_name and item_name snapshot
    if search and search.strip():
        stmt = stmt.where(
            or_(
                Sale.customer_name.ilike(f"%{search.strip()}%"),
                Sale.item_name.ilike(f"%{search.strip()}%")
            )
        )

    if start_date:
        stmt = stmt.where(Sale.sale_date >= start_date)
    if end_date:
        stmt = stmt.where(Sale.sale_date <= end_date)

    stmt = stmt.order_by(Sale.sale_date.desc(), Sale.sale_time.desc())
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    sales = result.scalars().all()
    
    return sales


# ✅ GET SINGLE SALE
async def get_sale(db: AsyncSession, sale_id: int, current_user: User):
    stmt = select(Sale).where(
        Sale.sale_id == sale_id,
        Sale.user_id == current_user.user_id
    )
    result = await db.execute(stmt)
    sale = result.scalar_one_or_none()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="فروخت موجود نہیں ہے۔"
        )
    return sale


# ✅ SUMMARY
async def get_sales_summary(
    db: AsyncSession,
    current_user: User,
    start_date: date = None,
    end_date: date = None
):
    stmt = select(
        func.count(Sale.sale_id),
        func.sum(Sale.quantity_sold)
    ).where(Sale.user_id == current_user.user_id)

    if start_date:
        stmt = stmt.where(Sale.sale_date >= start_date)
    if end_date:
        stmt = stmt.where(Sale.sale_date <= end_date)

    result = await db.execute(stmt)
    total_sales, total_quantity = result.one()

    return {
        "total_sales": total_sales or 0,
        "total_quantity": float(total_quantity or 0)
    }


# ✅ UPDATE SALE
async def update_sale(db: AsyncSession, sale_id: int, update_data: dict, current_user: User):
    # Get the sale
    sale = await get_sale(db, sale_id, current_user)
    
    # If item_id is being updated, update snapshot data
    if "item_id" in update_data and update_data["item_id"]:
        stmt = select(Item).where(Item.item_id == update_data["item_id"])
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if item:
            # Update snapshot with new item details
            update_data["item_name"] = item.item_name
            if "unit_price" not in update_data:
                update_data["unit_price"] = item.unit_price
            if "item_unit" not in update_data:
                update_data["item_unit"] = item.item_unit
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="منتخب کردہ آئٹم موجود نہیں ہے۔"
            )
    elif "item_id" in update_data and update_data["item_id"] is None:
        # If item_id is being set to None, keep existing snapshot
        pass
    
    # If date is updated, update Urdu components
    if "sale_date" in update_data and update_data["sale_date"]:
        urdu_components = get_urdu_date_components(update_data["sale_date"])
        update_data.update(urdu_components)
    
    # Update the sale
    for key, value in update_data.items():
        if value is not None:
            setattr(sale, key, value)
    
    await db.commit()
    await db.refresh(sale)
    return sale


# ✅ DELETE ONE
async def delete_sale_by_id(db: AsyncSession, sale_id: int, current_user: User):
    sale = await get_sale(db, sale_id, current_user)
    
    await db.delete(sale)
    await db.commit()

    return {"message": "فروخت کامیابی سے حذف کر دی گئی۔"}


# ✅ DELETE ALL
async def delete_all_sales(db: AsyncSession, current_user: User):
    result = await db.execute(
        delete(Sale).where(Sale.user_id == current_user.user_id)
    )
    await db.commit()
    
    count = result.rowcount
    return {"message": f"تمام {count} فروخت کامیابی سے حذف کر دی گئیں۔"}