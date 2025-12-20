from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.crud.bill import sync_bill_from_udhar

async def update_udhar_summary(db: AsyncSession, customer_id: int):
    # calculate total from all udharitems for this customer ONLY
    res = await db.execute(select(UdharItem).where(UdharItem.customer_id == customer_id))
    items = res.scalars().all()
    total = sum([float(item.total_amount) for item in items])

    # check if udhar record exists
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id))
    udhar = res.scalar_one_or_none()

    if not udhar:
        udhar = Udhar(customer_id=customer_id, total_amount=total)
        db.add(udhar)
    else:
        udhar.total_amount = total

    # update status based on ONLY udhar items total
    udhar.status = "paid" if total == 0 else "unpaid"

    await db.commit()
    await db.refresh(udhar)
    await sync_bill_from_udhar(db, customer_id)
    return udhar

# Functions for updating direct amounts (these won't affect total_amount)
async def update_direct_addition(db: AsyncSession, customer_id: int, amount: float):
    """Update direct addition amount (doesn't change total_amount)"""
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id))
    udhar = res.scalar_one_or_none()
    
    if not udhar:
        udhar = Udhar(customer_id=customer_id, direct_addition=amount, total_amount=0.0)
        db.add(udhar)
    else:
        udhar.direct_addition = udhar.direct_addition+amount  # Set or update direct addition
    
    await db.commit()
    await db.refresh(udhar)
    await sync_bill_from_udhar(db, customer_id)
    return udhar

async def update_direct_deduction(db: AsyncSession, customer_id: int, amount: float):
    """Update direct deduction amount (doesn't change total_amount)"""
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id))
    udhar = res.scalar_one_or_none()
    
    if not udhar:
        udhar = Udhar(customer_id=customer_id, direct_deduction=amount, total_amount=0.0)
        db.add(udhar)
    else:
        udhar.direct_deduction = udhar.direct_deduction+amount  # Set or update direct deduction
    
    await db.commit()
    await db.refresh(udhar)
    await sync_bill_from_udhar(db, customer_id)
    return udhar

async def get_udhar_by_customer(db: AsyncSession, customer_id: int):
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id))
    return res.scalar_one_or_none()

async def list_udhars(db: AsyncSession):
    res = await db.execute(select(Udhar))
    return res.scalars().all()