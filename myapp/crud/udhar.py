from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.crud.bill import sync_bill_from_udhar
from myapp.models.user import User
from myapp.models.customer import Customer

async def update_udhar_summary(db: AsyncSession, customer_id: int, current_user: User):
    # calculate total from all udharitems for this customer ONLY
    res = await db.execute(
        select(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    items = res.scalars().all()
    total = sum([float(item.total_amount) for item in items])

    # If no items, don't create udhar record
    if not items:
        # Check if there's an existing udhar and update it to paid
        res = await db.execute(
            select(Udhar).where(
                Udhar.customer_id == customer_id,
                Udhar.user_id == current_user.user_id
            )
        )
        udhar = res.scalar_one_or_none()
        if udhar:
            udhar.total_amount = 0
            udhar.status = "paid"
            await db.commit()
            await db.refresh(udhar)
            await sync_bill_from_udhar(db, customer_id, current_user)
        return None

    # Check if there's an existing UNPAID udhar record
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    existing_unpaid = res.scalar_one_or_none()
    
    if existing_unpaid:
        # Update existing unpaid udhar
        existing_unpaid.total_amount = total
        existing_unpaid.status = "paid" if total == 0 else "unpaid"
        udhar = existing_unpaid
    else:
        # Create new unpaid udhar (don't reuse old paid one)
        udhar = Udhar(
            customer_id=customer_id,
            total_amount=total,
            status="unpaid",
            user_id=current_user.user_id
        )
        db.add(udhar)

    await db.commit()
    await db.refresh(udhar)

    # sync bill (pass current_user object!)
    await sync_bill_from_udhar(db, customer_id, current_user)

    return udhar

async def update_direct_addition(db: AsyncSession, customer_id: int, amount: float, current_user: User):
    # First check if customer exists for this user
    cust_res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id,
            Customer.user_id == current_user.user_id
        )
    )
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے، اس کا کوئی اُدھار نہیں ہے")

    # Get unpaid udhar record (create one if doesn't exist)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()
    
    if not udhar:
        # Create new unpaid udhar if none exists
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid",
            total_amount=0.0
        )
        db.add(udhar)
        await db.flush()

    # Update direct addition
    udhar.direct_addition += amount

    await db.commit()
    await db.refresh(udhar)

    await sync_bill_from_udhar(db, customer_id, current_user)
    return udhar


async def update_direct_deduction(db: AsyncSession, customer_id: int, amount: float, current_user: User):
    # First check if customer exists for this user
    cust_res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id,
            Customer.user_id == current_user.user_id
        )
    )
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے، اس کا کوئی اُدھار نہیں ہے")

    # Get unpaid udhar record (create one if doesn't exist)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    udhar = res.scalar_one_or_none()
    
    if not udhar:
        # Create new unpaid udhar if none exists
        udhar = Udhar(
            customer_id=customer_id,
            user_id=current_user.user_id,
            status="unpaid",
            total_amount=0.0
        )
        db.add(udhar)
        await db.flush()

    # Update direct deduction
    udhar.direct_deduction += amount

    await db.commit()
    await db.refresh(udhar)

    await sync_bill_from_udhar(db, customer_id, current_user)
    return udhar


async def get_udhar_by_customer(db: AsyncSession, customer_id: int, current_user: User):
    # First, try to get unpaid udhar (most common case for active transactions)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id,
            Udhar.status == "unpaid"
        )
    )
    unpaid_udhar = res.scalar_one_or_none()
    if unpaid_udhar:
        return unpaid_udhar
    
    # If no unpaid udhar, return the latest one (could be paid)
    res = await db.execute(
        select(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id
        ).order_by(Udhar.udhar_id.desc())
    )
    return res.scalar_one_or_none()


async def list_udhars(db: AsyncSession, current_user: User):
    res = await db.execute(
        select(Udhar).where(Udhar.user_id == current_user.user_id)
    )
    return res.scalars().all()
