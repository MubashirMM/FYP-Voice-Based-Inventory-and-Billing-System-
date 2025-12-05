from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.items import ItemCreate, ItemUpdate, ItemRead
from myapp.crud import items as crud
# from fastapi import Query

router = APIRouter(prefix="/items", tags=["items"])

# Create
@router.post("/", response_model=ItemRead)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_items(db, item)


@router.get("/search", response_model=list[ItemRead])
async def search(
     keywords: str,db: AsyncSession = Depends(get_db) ):
    res=await crud.search_item(db, keywords)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return res

 

# Get one
@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    res = await crud.read_item(db, item_id)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return res

# Get all
@router.get("/", response_model=list[ItemRead])
async def get_all(db: AsyncSession = Depends(get_db)):
    return await crud.read_all(db)


# Update
@router.put("/{item_id}", response_model=ItemRead)
async def update_item(item_id: int, item: ItemUpdate, db: AsyncSession = Depends(get_db)):
    res = await crud.update_items(db, item_id, item)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return res

# Delete
@router.delete("/{item_id}")
async def delete_item_endpoint(item_id: int, db: AsyncSession = Depends(get_db)):
    res = await crud.delete_item(db, item_id)
    if not res:
        raise HTTPException(status_code=404, detail="آئٹم موجود نہیں ہے")
    return {"message": "آئٹم کامیابی سے حذف کر دیا گیا"}
