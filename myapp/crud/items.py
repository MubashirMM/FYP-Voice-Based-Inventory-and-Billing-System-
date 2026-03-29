from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from myapp.models.item import Item
from myapp.models.user import User 
from myapp.schemas.items import ItemCreate, ItemUpdate


# ============================
# CREATE ITEM
# ============================
async def create_items(db: AsyncSession, item: ItemCreate, current_user: User):
    # Check if item with same name exists for this user
    stmt = select(Item).where(
        Item.user_id == current_user.user_id,
        Item.item_name.ilike(item.item_name.strip())
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{item.item_name}' نام کا آئٹم پہلے سے موجود ہے۔ براہ کرم مختلف نام استعمال کریں۔"
        )
    
    # Create new item
    new_item = Item(
        item_name=item.item_name.strip(),
        item_unit=item.item_unit.strip(),
        unit_price=item.unit_price,
        stock_quantity=item.stock_quantity,
        user_id=current_user.user_id
    )
    
    db.add(new_item)
    try:
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="آئٹم بنانے میں خرابی ہوئی۔ براہ کرم دوبارہ کوشش کریں۔"
        )


# ============================
# READ ALL ITEMS
# ============================
async def read_all(db: AsyncSession, current_user: User):
    stmt = select(Item).where(
        Item.user_id == current_user.user_id
    ).order_by(Item.item_name)
    
    result = await db.execute(stmt)
    return result.scalars().all()


# ============================
# READ ONE ITEM
# ============================
async def read_item(db: AsyncSession, item_id: int, current_user: User):
    stmt = select(Item).where(
        Item.item_id == item_id,
        Item.user_id == current_user.user_id
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="آئٹم موجود نہیں ہے۔"
        )
    return item


# ============================
# SEARCH ITEMS
# ============================
async def search_item(db: AsyncSession, keywords: str, current_user: User):
    if not keywords or not keywords.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تلاش کے لیے کم از کم ایک لفظ درکار ہے۔"
        )
    
    stmt = select(Item).where(
        Item.user_id == current_user.user_id,
        Item.item_name.ilike(f"%{keywords.strip()}%")
    ).order_by(Item.item_name)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{keywords}' سے ملتا جلتا کوئی آئٹم نہیں ملا۔"
        )
    return items


# ============================
# UPDATE ITEM
# ============================
async def update_items(db: AsyncSession, item_id: int, item: ItemUpdate, current_user: User):
    # Get existing item
    db_item = await read_item(db, item_id, current_user)
    
    # Check for duplicate name if name is being updated
    if item.item_name is not None:
        stmt = select(Item).where(
            Item.user_id == current_user.user_id,
            Item.item_name.ilike(item.item_name.strip()),
            Item.item_id != item_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{item.item_name}' نام کا آئٹم پہلے سے موجود ہے۔ براہ کرم مختلف نام استعمال کریں۔"
            )
        db_item.item_name = item.item_name.strip()
    
    # Update other fields
    if item.item_unit is not None:
        db_item.item_unit = item.item_unit.strip()
    
    if item.unit_price is not None:
        if item.unit_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="قیمت مثبت ہونی چاہیے۔"
            )
        db_item.unit_price = item.unit_price
    
    if item.stock_quantity is not None:
        if item.stock_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="اسٹاک منفی نہیں ہو سکتا۔"
            )
        db_item.stock_quantity = item.stock_quantity
    
    try:
        await db.commit()
        await db.refresh(db_item)
        return db_item
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="آئٹم اپ ڈیٹ کرنے میں خرابی ہوئی۔ براہ کرم دوبارہ کوشش کریں۔"
        )


# ============================
# DELETE ITEM
# ============================
async def delete_item(db: AsyncSession, item_id: int, current_user: User):
    # Get existing item
    db_item = await read_item(db, item_id, current_user)
    
    # Delete the item - related records will have item_id set to NULL
    # because of ondelete="SET NULL" in foreign key constraints
    await db.delete(db_item)
    await db.commit()
    
    return True