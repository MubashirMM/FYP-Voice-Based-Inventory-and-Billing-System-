from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from myapp.database.session import get_db
from myapp.schemas.shop import ShopCreate, ShopUpdate, ShopRead
from myapp.crud import shop as crud
from myapp.utils.security import get_current_user
from myapp.models.user import User

router = APIRouter(prefix="/shops", tags=["shops"])

@router.post("/", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
async def create_shop(
    shop: ShopCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # crud.create_shop will raise Urdu HTTPExceptions on errors
    return await crud.create_shop(db, shop, current_user)

@router.get("/", response_model=List[ShopRead])
async def get_shops(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return await crud.get_all_shops(db, current_user)

@router.get("/{shop_id}", response_model=ShopRead)
async def get_shop(
    shop_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    shop = await crud.get_shop(db, shop_id, current_user)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

@router.patch("/{shop_id}", response_model=ShopRead)
async def update_shop(
    shop_id: int, 
    shop: ShopUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    
    update_data = shop.model_dump(exclude_unset=True)
    return await crud.update_shop(db, shop_id, update_data, current_user)

@router.delete("/{shop_id}", status_code=status.HTTP_200_OK)
async def delete_shop(
    shop_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    await crud.delete_shop(db, shop_id, current_user)
    return {"detail": f"دکان {shop_id} کامیابی سے حذف ہو گئی"}