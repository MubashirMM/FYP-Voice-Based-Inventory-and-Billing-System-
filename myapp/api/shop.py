
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.shop import ShopCreate, ShopUpdate, ShopRead
from myapp.crud import shop as crud
from myapp.utils.security import get_current_user
from myapp.models.user import User
from typing import List

router = APIRouter(prefix="/shops", tags=["shops"])

@router.post("/", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
async def create_shop(shop: ShopCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # crud.create_shop will raise Urdu HTTPExceptions on errors
    return await crud.create_shop(db, shop, current_user)

@router.get("/", response_model=List[ShopRead])
async def get_shops(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await crud.get_all_shops(db, current_user)

@router.get("/{shop_id}", response_model=ShopRead)
async def get_shop(shop_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await crud.get_shop(db, shop_id, current_user)

@router.patch("/{shop_id}", response_model=ShopRead)
async def update_shop(shop_id: int, shop: ShopUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await crud.update_shop(db, shop_id, shop.dict(exclude_unset=True), current_user)

@router.delete("/{shop_id}")
async def delete_shop(shop_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await crud.delete_shop(db, shop_id, current_user)
    return {"detail": f"دکان {shop_id} کامیابی سے حذف ہو گئی"}
