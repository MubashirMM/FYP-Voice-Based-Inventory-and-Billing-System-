from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from myapp.models.bill import Bill
from myapp.models.bill_item_history import BillItemHistory
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem
from myapp.models.user import User
from myapp.utils.urdu_date import convert_datetime_to_urdu

async def sync_bill_from_udhar(db: AsyncSession, customer_id: int, current_user: User) -> Bill:
    # fetch udhar scoped to user
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id, Udhar.user_id == current_user.user_id))
    udhar = res.scalar_one_or_none()

    # fetch udhar items scoped to user
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.item))
        .where(UdharItem.customer_id == customer_id, UdharItem.user_id == current_user.user_id)
    )
    items = res.scalars().all()

    items_total = sum(float(i.total_amount) for i in items)
    direct_add = udhar.direct_addition if udhar else 0.0
    direct_ded = udhar.direct_deduction if udhar else 0.0
    effective_total = items_total + direct_add - direct_ded

    # fetch or create bill scoped to user
    res = await db.execute(select(Bill).where(Bill.customer_id == customer_id, Bill.user_id == current_user.user_id, Bill.status == 'unpaid'))
    bill = res.scalar_one_or_none()

    # Get current datetime for Urdu date/time
    now = datetime.now()
    bill_urdu = convert_datetime_to_urdu(now, "bill")

    if not bill:
        bill = Bill(
            customer_id=customer_id, 
            status="unpaid", 
            user_id=current_user.user_id,
            bill_day=bill_urdu["bill_day"],
            bill_month=bill_urdu["bill_month"],
            bill_year=bill_urdu["bill_year"],
            bill_time=bill_urdu["bill_time"],
            bill_day_name=bill_urdu["bill_day_name"]
        )
        db.add(bill)
        await db.flush()
    elif bill.status == "paid":
        bill = Bill(
            customer_id=customer_id, 
            status="unpaid", 
            user_id=current_user.user_id,
            bill_day=bill_urdu["bill_day"],
            bill_month=bill_urdu["bill_month"],
            bill_year=bill_urdu["bill_year"],
            bill_time=bill_urdu["bill_time"],
            bill_day_name=bill_urdu["bill_day_name"]
        )
        db.add(bill)
        await db.flush()

    # update bill totals
    bill.udhar_items_total = items_total
    bill.direct_addition = direct_add
    bill.direct_deduction = direct_ded
    bill.effective_total = effective_total
    bill.status = "paid" if effective_total == 0 else "unpaid"

    # rebuild bill items
    await db.execute(delete(BillItemHistory).where(BillItemHistory.bill_id == bill.bill_id, BillItemHistory.user_id == current_user.user_id))
    for item in items:
        db.add(BillItemHistory(
            bill_id=bill.bill_id,
            user_id=current_user.user_id,
            item_name=item.item.item_name,
            unit_price=item.unit_price,
            quantity=item.quantity,
            requested_unit=item.requested_unit,
            total_amount=item.total_amount,
        ))

    # Update udhar status to paid instead of deleting
    if bill.status == "paid" and udhar:
        udhar.status = "paid"
        await db.execute(delete(UdharItem).where(UdharItem.customer_id == customer_id, UdharItem.user_id == current_user.user_id))

    await db.commit()
    await db.refresh(bill)
    return bill


async def get_bills_by_customer(db: AsyncSession, customer_id: int, current_user: User):
    """Get all bills for a specific customer scoped to the logged-in user"""
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .where(Bill.customer_id == customer_id, Bill.user_id == current_user.user_id)
    )
    return res.scalars().all()

async def get_all_bills(db: AsyncSession, current_user: User):
    """Get all bills for the logged-in user"""
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .where(Bill.user_id == current_user.user_id)
    )
    return res.scalars().all()

async def pay_bill(db: AsyncSession, customer_id: int, current_user: User) -> Bill | None:
    """Mark a bill as paid for a specific customer scoped to the logged-in user"""
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))
        .where(Bill.customer_id == customer_id, Bill.user_id == current_user.user_id)
    )
    bill = res.scalar_one_or_none()
    if not bill:
        return None

    bill.status = "paid"
    
    # Update Urdu date/time fields when paying
    now = datetime.now()
    bill_urdu = convert_datetime_to_urdu(now, "bill")
    bill.bill_day = bill_urdu["bill_day"]
    bill.bill_month = bill_urdu["bill_month"]
    bill.bill_year = bill_urdu["bill_year"]
    bill.bill_time = bill_urdu["bill_time"]
    bill.bill_day_name = bill_urdu["bill_day_name"]

    # Update udhar status to "paid" instead of deleting
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id, Udhar.user_id == current_user.user_id))
    udhar = res.scalar_one_or_none()
    if udhar:
        udhar.status = "paid"
    
    # Clear udhar items for this customer scoped to user
    await db.execute(delete(UdharItem).where(UdharItem.customer_id == customer_id, UdharItem.user_id == current_user.user_id))

    await db.commit()
    await db.refresh(bill)
    return bill

async def delete_bill(db: AsyncSession, bill_id: int, current_user: User):
    """Delete a bill scoped to the logged-in user. Returns True if deleted, 'unpaid' if bill is unpaid, False if not found."""
    res = await db.execute(select(Bill).where(Bill.bill_id == bill_id, Bill.user_id == current_user.user_id))
    bill = res.scalar_one_or_none()
    
    if not bill:
        return False
    
    # Check if bill is unpaid - don't allow deletion of unpaid bills
    if bill.status == "unpaid":
        return "unpaid"

    # Delete related item history scoped to user
    await db.execute(delete(BillItemHistory).where(BillItemHistory.bill_id == bill_id, BillItemHistory.user_id == current_user.user_id))

    # Delete the bill itself
    await db.execute(delete(Bill).where(Bill.bill_id == bill_id, Bill.user_id == current_user.user_id))

    await db.commit()
    return True
