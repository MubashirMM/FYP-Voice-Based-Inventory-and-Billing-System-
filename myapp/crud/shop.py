from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from myapp.models.shop import Shop
from myapp.models.user import User

async def create_shop(db: AsyncSession, shop_name: str, address: str | None, current_user: User):
    shop = Shop(shop_name=shop_name, address=address, user_id=current_user.user_id)
    db.add(shop)
    await db.commit()
    await db.refresh(shop)
    return shop

async def get_all_shops(db: AsyncSession, current_user: User):
    res = await db.execute(select(Shop).where(Shop.user_id == current_user.user_id))
    return res.scalars().all()

async def get_shop(db: AsyncSession, shop_id: int, current_user: User):
    res = await db.execute(select(Shop).where(Shop.shop_id == shop_id, Shop.user_id == current_user.user_id))
    return res.scalar_one_or_none()

async def update_shop(db: AsyncSession, shop_id: int, shop_data: dict, current_user: User):
    shop = await get_shop(db, shop_id, current_user)
    if not shop:
        return None
    for key, value in shop_data.items():
        if value is not None:
            setattr(shop, key, value)
    await db.commit()
    await db.refresh(shop)
    return shop

async def delete_shop(db: AsyncSession, shop_id: int, current_user: User):
    shop = await get_shop(db, shop_id, current_user)
    if not shop:
        return False
    await db.delete(shop)
    await db.commit()
    return True
