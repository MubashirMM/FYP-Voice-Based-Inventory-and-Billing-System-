from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate
from myapp.models.customer import Customer

async def create_customers(db: AsyncSession, customer: CustomerCreate):
    new_customer = Customer(**customer.model_dump())
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    return new_customer

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

async def delete_customer(db: AsyncSession, customer_id: int):
    stmt = select(Customer).where(Customer.customer_id == customer_id)
    res = await db.execute(stmt)
    cust = res.scalar_one_or_none()
   
    if not cust:
        return None
    await db.delete(cust)
    await db.commit()
    return True