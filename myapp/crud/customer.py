from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.customer import CustomerCreate, CustomerUpdate
from myapp.models.customer import Customer
from sqlalchemy import select, delete, or_
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem  # ✅ Fixed: udhar_item not udhaar_item
from myapp.models.bill import Bill

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from myapp.models.user import User


async def create_customers(db: AsyncSession, customer: CustomerCreate, current_user: User):
    # Check if customer already exists for this user
    stmt = select(Customer).where(
        Customer.user_id == current_user.user_id,
        Customer.customer_name.ilike(customer.customer_name.strip())
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{customer.customer_name}' نام کا کسٹمر پہلے سے موجود ہے۔ براہ کرم دوسرا نام منتخب کریں۔"
        )
    
    new_customer = Customer(
        customer_name=customer.customer_name.strip(),
        user_id=current_user.user_id
    )
    db.add(new_customer)
    try:
        await db.commit()
        await db.refresh(new_customer)
        return new_customer
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کسٹمر بنانے میں خرابی ہوئی۔ براہ کرم دوبارہ کوشش کریں۔"
        )


async def read_all(db: AsyncSession, current_user: User):
    stmt = select(Customer).where(
        Customer.user_id == current_user.user_id
    ).order_by(Customer.customer_name)
    res = await db.execute(stmt)
    return res.scalars().all()


async def read_customer(db: AsyncSession, customer_id: int, current_user: User):
    stmt = select(Customer).where(
        Customer.customer_id == customer_id,
        Customer.user_id == current_user.user_id
    )
    res = await db.execute(stmt)
    customer = res.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کسٹمر موجود نہیں ہے۔"
        )
    return customer


async def search_customer(db: AsyncSession, customer_name: str, current_user: User):
    if not customer_name or not customer_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تلاش کے لیے کم از کم ایک لفظ درکار ہے۔"
        )
    
    # ✅ Case-insensitive partial match search
    stmt = select(Customer).where(
        Customer.user_id == current_user.user_id,
        Customer.customer_name.ilike(f"%{customer_name.strip()}%")
    ).order_by(Customer.customer_name)
    
    res = await db.execute(stmt)
    customers = res.scalars().all()
    
    if not customers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{customer_name}' سے ملتا جلتا کوئی کسٹمر نہیں ملا۔"
        )
    return customers


async def update_customer(db: AsyncSession, customer_id: int, update_data: CustomerUpdate, current_user: User):
    # Get existing customer
    customer = await read_customer(db, customer_id, current_user)
    
    # Check for duplicate name if name is being updated
    if update_data.customer_name is not None:
        stmt = select(Customer).where(
            Customer.user_id == current_user.user_id,
            Customer.customer_name.ilike(update_data.customer_name.strip()),
            Customer.customer_id != customer_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{update_data.customer_name}' نام کا کسٹمر پہلے سے موجود ہے۔ براہ کرم دوسرا نام منتخب کریں۔"
            )
        customer.customer_name = update_data.customer_name.strip()
    
    await db.commit()
    await db.refresh(customer)
    return customer


async def delete_customer(db: AsyncSession, customer_id: int, current_user: User):
    # Get customer
    stmt = select(Customer).where(
        Customer.customer_id == customer_id,
        Customer.user_id == current_user.user_id
    )
    res = await db.execute(stmt)
    cust = res.scalar_one_or_none()
    
    if not cust:
        return {
            "success": False,
            "customer_name": None,
            "message": "کسٹمر موجود نہیں ہے۔"
        }
    
    customer_name = cust.customer_name
    
    # Check for unpaid bills
    stmt = select(Bill).where(
        Bill.customer_id == customer_id,
        Bill.user_id == current_user.user_id,
        Bill.status == "unpaid"
    )
    res = await db.execute(stmt)
    unpaid_bill = res.scalar_one_or_none()
    
    if unpaid_bill:
        return {
            "success": False,
            "customer_name": customer_name,
            "message": "کسٹمر کے پاس غیر ادا شدہ بل موجود ہیں، پہلے بل ادا کریں۔"
        }
    
    # Delete related records
    await db.execute(
        delete(UdharItem).where(
            UdharItem.customer_id == customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    
    await db.execute(
        delete(Udhar).where(
            Udhar.customer_id == customer_id,
            Udhar.user_id == current_user.user_id
        )
    )
    
    # Delete customer
    await db.delete(cust)
    await db.commit()
    
    return {
        "success": True,
        "customer_name": customer_name,
        "message": f"کسٹمر {customer_name} کامیابی سے حذف کر دیا گیا۔"
    }