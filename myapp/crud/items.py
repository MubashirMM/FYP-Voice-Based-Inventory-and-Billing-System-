from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.models.item import Item
from sqlalchemy.exc import IntegrityError
from myapp.schemas.items import ItemCreate, ItemUpdate
from fastapi import HTTPException

# Create
async def create_items(db: AsyncSession, item: ItemCreate):
    new_item = Item(**item.model_dump())
    db.add(new_item)
    try:
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="آئٹم پہلے ہی موجود ہے یا نام دہرایا گیا ہے")

# Read all
async def read_all(db: AsyncSession):
    stmt = select(Item)
    result = await db.execute(stmt)
    return result.scalars().all()

# Read one
async def read_item(db: AsyncSession, item_id: int):
    stmt = select(Item).where(Item.item_id == item_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Search
async def search_item(db: AsyncSession, keywords: str):
    stmt = select(Item).where(Item.item_name.ilike(f"%{keywords}%"))
    result = await db.execute(stmt)
    return result.scalars().all()

# Update
async def update_items(db: AsyncSession, item_id: int, item: ItemUpdate):
    db_item = await read_item(db, item_id)
    if not db_item:
        return None
    for field, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def delete_item(db: AsyncSession, item_id: int):
    stmt = select(Item).where(Item.item_id == item_id)
    result = await db.execute(stmt)
    db_item = result.scalar_one_or_none()
    if not db_item:
        return None
    await db.delete(db_item)
    await db.commit()
    return True
