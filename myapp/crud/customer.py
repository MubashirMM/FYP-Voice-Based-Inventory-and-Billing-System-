
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate
from myapp.models.customer import Customer
from sqlalchemy import select, delete
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.bill import Bill

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from myapp.models.user import User

async def create_customers(db: AsyncSession, customer: CustomerCreate, current_user: User):
    new_customer = Customer(
        customer_name=customer.customer_name,
        user_id=current_user.user_id
    )
    db.add(new_customer)
    try:
        await db.commit()
        await db.refresh(new_customer)
        return new_customer
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="یہ کسٹمر پہلے سے موجود ہے، براہ کرم دوسرا نام منتخب کریں")

async def read_all(db: AsyncSession, current_user: User):
    stmt = select(Customer).where(Customer.user_id == current_user.user_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def read_customer(db: AsyncSession, customer_id: int, current_user: User):
    stmt = select(Customer).where(Customer.customer_id == customer_id, Customer.user_id == current_user.user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def search_customer(db: AsyncSession, customer_name: str, current_user: User):
    stmt = select(Customer).where(Customer.customer_name == customer_name, Customer.user_id == current_user.user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def delete_customer(db: AsyncSession, customer_id: int, current_user: User) -> bool | None:
    res = await db.execute(select(Customer).where(Customer.customer_id == customer_id, Customer.user_id == current_user.user_id))
    cust = res.scalar_one_or_none()
    name=cust.customer_name
    if not cust:
        return None

    # unpaid bills check scoped to user
    res = await db.execute(select(Bill).where(Bill.customer_id == customer_id, Bill.user_id == current_user.user_id, Bill.status == "unpaid"))
    unpaid_bill = res.scalar_one_or_none()
    if unpaid_bill:
        return False

    await db.execute(delete(UdharItem).where(UdharItem.customer_id == customer_id, UdharItem.user_id == current_user.user_id))
    await db.execute(delete(Udhar).where(Udhar.customer_id == customer_id, Udhar.user_id == current_user.user_id))

    await db.delete(cust)
    await db.commit()
    return (True,name)
