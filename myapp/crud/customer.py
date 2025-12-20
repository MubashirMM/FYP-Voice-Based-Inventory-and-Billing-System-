
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate
from myapp.models.customer import Customer
from sqlalchemy import select, delete
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.bill import Bill

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

async def create_customers(db: AsyncSession, customer: CustomerCreate):
    new_customer = Customer(**customer.model_dump())
    db.add(new_customer)
    try:
        await db.commit()
        await db.refresh(new_customer)
        return new_customer
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="یہ کسٹمر پہلے سے موجود ہے، براہ کرم دوسرا نام منتخب کریں")


async def read_all(db: AsyncSession):
    stmt = select(Customer)
    res = await db.execute(stmt)
    return res.scalars().all()

async def read_customer(db: AsyncSession, customer_id: int):
    stmt = select(Customer).where(Customer.customer_id == customer_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def search_customer(db: AsyncSession, customer_name: str):
    stmt = select(Customer).where(Customer.customer_name == customer_name)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def delete_customer(db: AsyncSession, customer_id: int) -> bool:
    # fetch customer
    res = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
    cust = res.scalar_one_or_none()
    if not cust:
        return None

    # check if customer has unpaid bills
    res = await db.execute(select(Bill).where(Bill.customer_id == customer_id, Bill.status == "unpaid"))
    unpaid_bill = res.scalar_one_or_none()
    if unpaid_bill:
        # block deletion if unpaid bills exist
        return False

    # delete udhar items and udhar records
    await db.execute(delete(UdharItem).where(UdharItem.customer_id == customer_id))
    await db.execute(delete(Udhar).where(Udhar.customer_id == customer_id))

    # delete customer itself
    await db.delete(cust)
    await db.commit()
    return True
