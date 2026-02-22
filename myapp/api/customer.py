from fastapi import HTTPException, APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate, CustomerRead
from myapp.database.session import get_db
from myapp.crud import customer as crud
from typing import List
from myapp.utils.security import get_current_user
from myapp.models.user import User

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await crud.create_customers(db, customer, current_user)

@router.get("/search", response_model=CustomerRead)
async def search(customer_name: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await crud.search_customer(db, customer_name, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="کسٹمر نہیں ملا")
    return res

@router.get("/", response_model=List[CustomerRead])
async def get_all(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await crud.read_all(db, current_user)

@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await crud.read_customer(db, customer_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="کسٹمر نہیں ملا")
    return res

@router.delete("/{customer_id}")
async def delete_customer_endpoint(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await crud.delete_customer(db, customer_id, current_user)
    result1=result[0]
    customer_name=result[1]
    if result1 is None:
        raise HTTPException(status_code=404, detail="کسٹمر نہیں ملا")
    if result1 is False:
        raise HTTPException(status_code=400, detail="کسٹمر کے پاس غیر ادا شدہ بل موجود ہیں، پہلے بل ادا کریں")
    return {"detail": f"کسٹمر {customer_name} کامیابی سے ڈیلیٹ کر دیا گیا"}
