from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from myapp.models.shop import Shop
from myapp.models.user import User
from myapp.schemas.shop import ShopCreate
from myapp.utils.errors import http_error

async def create_shop(db: AsyncSession, shop: ShopCreate, current_user: User):
    # validation already handled by Pydantic, but enforce unique name per user
    stmt = select(Shop).where(Shop.user_id == current_user.user_id, Shop.shop_name == shop.shop_name)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise http_error(400, "یہ دکان پہلے سے موجود ہے")

    shop_obj = Shop(shop_name=shop.shop_name, address=shop.address, user_id=current_user.user_id)
    db.add(shop_obj)
    await db.commit()
    await db.refresh(shop_obj)
    return shop_obj

async def get_all_shops(db: AsyncSession, current_user: User):
    res = await db.execute(select(Shop).where(Shop.user_id == current_user.user_id))
    return res.scalars().all()

async def get_shop(db: AsyncSession, shop_id: int, current_user: User):
    res = await db.execute(
        select(Shop).where(Shop.shop_id == shop_id, Shop.user_id == current_user.user_id)
    )
    shop = res.scalar_one_or_none()
    if shop is None:
        raise http_error(404, "دکان نہیں ملی")
    return shop

async def update_shop(db: AsyncSession, shop_id: int, shop_data: dict, current_user: User):
    shop = await get_shop(db, shop_id, current_user)
    # get_shop already raises 404 if missing
    for key, value in shop_data.items():
        if value is not None:
            setattr(shop, key, value)
    await db.commit()
    await db.refresh(shop)
    return shop

async def delete_shop(db: AsyncSession, shop_id: int, current_user: User):
    shop = await get_shop(db, shop_id, current_user)
    # get_shop raises 404 if not found
    await db.delete(shop)
    await db.commit()
    return True
