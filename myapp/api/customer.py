from fastapi import HTTPException, APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate, CustomerRead
from myapp.database.session import get_db
from myapp.crud import customer as crud
from typing import List

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_customers(db, customer)

@router.get("/search", response_model=CustomerRead)
async def search(customer_name: str, db: AsyncSession = Depends(get_db)):
    res = await crud.search_customer(db, customer_name)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="کسٹمر نہیں ملا"
        )
    return res

@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    res = await crud.read_customer(db, customer_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="کسٹمر نہیں ملا"
        )
    return res

@router.get("/", response_model=List[CustomerRead])
async def get_all(db: AsyncSession = Depends(get_db)):
    return await crud.read_all(db)

@router.delete("/{customer_id}")
async def delete_customer_endpoint(customer_id: int, db: AsyncSession = Depends(get_db)):
    res = await crud.delete_customer(db, customer_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="کسٹمر نہیں ملا"
        )
    return {'message': "کسٹمر کامیابی سے حذف ہو گیا"}