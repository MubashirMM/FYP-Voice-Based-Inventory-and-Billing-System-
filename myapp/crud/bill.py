from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from myapp.models.bill import Bill
from myapp.models.bill_item_history import BillItemHistory
from myapp.models.udhar import Udhar
from myapp.models.udhaar_item import UdharItem

async def sync_bill_from_udhar(db: AsyncSession, customer_id: int) -> Bill:
    # ---- fetch udhar
    res = await db.execute(select(Udhar).where(Udhar.customer_id == customer_id))
    udhar = res.scalar_one_or_none()

    # ---- fetch udhar items (with relationship eager load!)
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.item))  # ✅ avoid MissingGreenlet
        .where(UdharItem.customer_id == customer_id)
    )
    items = res.scalars().all()

    items_total = sum(float(i.total_amount) for i in items)
    direct_add = udhar.direct_addition if udhar else 0.0
    direct_ded = udhar.direct_deduction if udhar else 0.0
    effective_total = items_total + direct_add - direct_ded

    # ---- fetch or create bill
    res = await db.execute(select(Bill).where(Bill.customer_id == customer_id,Bill.status=='unpaid'))
    bill = res.scalar_one_or_none()

    if not bill:
        bill = Bill(customer_id=customer_id, status="unpaid")
        db.add(bill)
        await db.flush()
    elif bill.status == "paid":
        # if last bill is paid, create a new unpaid bill
        bill = Bill(customer_id=customer_id, status="unpaid")
        db.add(bill)
        await db.flush()


    # ---- update bill totals
    bill.udhar_items_total = items_total
    bill.direct_addition = direct_add
    bill.direct_deduction = direct_ded
    bill.effective_total = effective_total
    bill.status = "paid" if effective_total == 0 else "unpaid"

    # ---- rebuild bill items
    await db.execute(delete(BillItemHistory).where(BillItemHistory.bill_id == bill.bill_id))
    for item in items:
        db.add(BillItemHistory(
            bill_id=bill.bill_id,
            item_name=item.item.item_name,  # ✅ safe now with selectinload
            unit_price=item.unit_price,
            quantity=item.quantity,
            requested_unit=item.requested_unit,
            total_amount=item.total_amount,
        ))

    # ---- if paid → clear udhar tables
    if bill.status == "paid":
        await db.execute(delete(UdharItem).where(UdharItem.customer_id == customer_id))
        await db.execute(delete(Udhar).where(Udhar.customer_id == customer_id))

    await db.commit()
    await db.refresh(bill)
    return bill

async def get_bills_by_customer(db: AsyncSession, customer_id: int):
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))   
        .where(Bill.customer_id == customer_id)
    )
    if not res:
        return None
    return res.scalars().all()

async def get_all_bills(db: AsyncSession):
    res = await db.execute(
        select(Bill)
        .options(selectinload(Bill.items))  
    )
    if not res:
        return None
    return res.scalars().all()

async def pay_bill(db: AsyncSession, customer_id: int) -> Bill:
    # fetch bill for customer
    res = await db.execute(select(Bill).where(Bill.customer_id == customer_id))
    bill = res.scalar_one_or_none()
    if not bill:
        return None

    # mark as paid (keep effective_total and items intact)
    bill.status = "paid"

    # clear udhar tables for this customer
    await db.execute(delete(UdharItem).where(UdharItem.customer_id == customer_id))
    await db.execute(delete(Udhar).where(Udhar.customer_id == customer_id))

    await db.commit()
    await db.refresh(bill)
    return bill


async def delete_bill(db: AsyncSession, bill_id: int) -> bool:
    # fetch bill
    res = await db.execute(select(Bill).where(Bill.bill_id == bill_id))
    bill = res.scalar_one_or_none()
    if not bill:
        return False

    # delete related item history
    await db.execute(delete(BillItemHistory).where(BillItemHistory.bill_id == bill_id))

    # delete the bill itself
    await db.execute(delete(Bill).where(Bill.bill_id == bill_id))

    await db.commit()
    return True

