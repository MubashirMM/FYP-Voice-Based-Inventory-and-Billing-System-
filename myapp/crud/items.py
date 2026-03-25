from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from myapp.models.item import Item
from myapp.models.user import User 
from myapp.schemas.items import ItemCreate, ItemUpdate

# Create
async def create_items(db: AsyncSession, item: ItemCreate, current_user: User):
    new_item = Item(**item.model_dump(), user_id=current_user.user_id)
    db.add(new_item)
    try:
        await db.commit()
        await db.refresh(new_item)


        return new_item
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="آئٹم پہلے ہی موجود ہے یا نام دہرایا گیا ہے")

# Read all
async def read_all(db: AsyncSession, current_user: User):
    stmt = select(Item).where(Item.user_id == current_user.user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# Read one
async def read_item(db: AsyncSession, item_id: int, current_user: User):
    stmt = select(Item).where(Item.item_id == item_id, Item.user_id == current_user.user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Search
async def search_item(db: AsyncSession, keywords: str, current_user: User):
    stmt = select(Item).where(
        Item.user_id == current_user.user_id,
        Item.item_name.ilike(f"%{keywords}%")
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# Update
async def update_items(db: AsyncSession, item_id: int, item: ItemUpdate, current_user: User):
    db_item = await read_item(db, item_id, current_user)
    if not db_item:
        return None

    for field, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)

    try:
        await db.commit()
        await db.refresh(db_item)
        return db_item
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="اپڈیٹ ناکام ہوئی، نام یا ڈیٹا درست نہیں ہے")

# Delete
async def delete_item(db: AsyncSession, item_id: int, current_user: User):
    db_item = await read_item(db, item_id, current_user)
    if not db_item:
        return None
    await db.delete(db_item)
    await db.commit()
    return True
