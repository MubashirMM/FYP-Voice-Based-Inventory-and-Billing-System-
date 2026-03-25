from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from myapp.schemas.udhaar_item import UdharCreateRequest, UdharRead
from myapp.models.udhaar_item import UdharItem
from myapp.models.customer import Customer
from myapp.models.item import Item
from myapp.models.user import User

from myapp.database.session import get_db
from myapp.utils.security import get_current_user
from myapp.crud.udhaar_item import (
    create_udhar,
    update_udharitem,
    delete_udharitem,
    list_udharitems,          # ← Add this import if you want to use the CRUD version
)

router = APIRouter(prefix="/udhar-items", tags=["udhar items"])


# =========================
# CREATE
# =========================
@router.post("/", response_model=UdharRead)
async def create_new_udhar(
    udhar_data: UdharCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # create_udhar now returns a properly loaded ORM object + dict via format_item
        created = await create_udhar(
            db=db,
            customer_name=udhar_data.customer_name,
            item_name=udhar_data.item_name,
            quantity=udhar_data.quantity,
            unit=udhar_data.unit,
            current_user=current_user
        )
        return created   # ← Just return it (no extra query needed)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# GET ALL
# =========================
@router.get("/", response_model=list[UdharRead])
async def get_all_udharitems(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(UdharItem.user_id == current_user.user_id)
    )
    items = res.scalars().all()
    return [format_udhar_item(i) for i in items]   # or use list_udharitems from CRUD


# =========================
# GET BY CUSTOMER NAME
# =========================
@router.get("/customer/{customer_name}", response_model=list[UdharRead])
async def get_udharitems_by_customer(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Reuse helper or move get_or_create if needed, but here we expect existing
    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == customer_name.strip(),
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے")

    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(
            UdharItem.customer_id == customer.customer_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    items = res.scalars().all()
    return [format_udhar_item(i) for i in items]


# =========================
# GET BY ID
# =========================
@router.get("/{item_id}", response_model=UdharRead)
async def get_udharitem(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(UdharItem)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(
            UdharItem.udharitem_id == item_id,
            UdharItem.user_id == current_user.user_id
        )
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

    return format_udhar_item(item)


# =========================
# UPDATE
# =========================
@router.put("/{item_id}", response_model=UdharRead)
async def update_udharitem_api(
    item_id: int,
    data: UdharCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        updated = await update_udharitem(db, item_id, data, current_user)
        return updated                     # ← Just return what CRUD gives

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# DELETE
# =========================
@router.delete("/{item_id}")
async def delete_udharitem_api(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await delete_udharitem(db, item_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# SEARCH
# =========================
@router.get("/search/", response_model=list[UdharRead])
async def search_items(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(UdharItem)
        .join(Item)
        .options(selectinload(UdharItem.customer), selectinload(UdharItem.item))
        .where(
            Item.item_name.ilike(f"%{keyword}%"),
            UdharItem.user_id == current_user.user_id
        )
    )
    items = res.scalars().all()
    return [format_udhar_item(i) for i in items]


# =========================
# FORMAT (kept here for GET endpoints)
# =========================
def format_udhar_item(i: UdharItem):
    """Safe formatter - works with ORM object"""
    if not i:
        return None
    return {
        "udharitem_id": i.udharitem_id,
        "customer_id": i.customer_id,
        "customer_name": getattr(i.customer, "customer_name", None) if getattr(i, "customer", None) else None,
        "item_id": i.item_id,
        "item_name": getattr(i.item, "item_name", None) if getattr(i, "item", None) else None,
        "unit_price": float(i.unit_price) if i.unit_price else None,
        "quantity": float(i.quantity) if i.quantity else None,
        "requested_unit": i.requested_unit,
        "total_amount": float(i.total_amount) if i.total_amount else None,
        "created_date": i.created_date,
        "udhar_day": i.udhar_day,
        "udhar_month": i.udhar_month,
        "udhar_year": i.udhar_year,
        "udhar_time": i.udhar_time,
        "udhar_day_name": i.udhar_day_name,
    }