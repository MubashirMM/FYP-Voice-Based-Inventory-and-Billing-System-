# routers/items.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.items import ItemCreate, ItemUpdate, ItemRead
from myapp.crud import items as crud
from myapp.models.user import User
from myapp.utils.security import get_current_user  # your JWT dependency

router = APIRouter(prefix="/items", tags=["items"])
# Create
@router.post("/", response_model=ItemRead)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await crud.create_items(db, item, current_user)

# Search

@router.get("/search", response_model=list[ItemRead])

async def search(
    keywords: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await crud.search_item(db, keywords, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return res

# Get one
@router.get("/{item_id}", response_model=ItemRead)
 
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await crud.read_item(db, item_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return res

# Get all
@router.get("/", response_model=list[ItemRead])

async def get_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await crud.read_all(db, current_user)

# Update
@router.patch("/{item_id}", response_model=ItemRead)
 
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await crud.update_items(db, item_id, item, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return res

# Delete
@router.delete("/{item_id}")

async def delete_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await crud.delete_item(db, item_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return {"message": "آئٹم کامیابی سے حذف کر دیا گیا"}
