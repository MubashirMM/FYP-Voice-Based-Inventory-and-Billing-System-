from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from myapp.schemas.udhaar_item import UdharCreateRequest, UdharRead
from myapp.models.customer import Customer
from myapp.models.user import User

from myapp.database.session import get_db
from myapp.utils.security import get_current_user
from myapp.crud.udhaar_item import (
    create_udhar,
    update_udharitem,
    delete_udharitem,
    list_udharitems
)

router = APIRouter(prefix="/udhar-items", tags=["udhar items"],redirect_slashes=False)

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/", response_model=UdharRead)
async def create_new_udhar(
    udhar_data: UdharCreateRequest,
    background_tasks: BackgroundTasks,   # ✅ ADDED
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await create_udhar(
            db=db,
            customer_name=udhar_data.customer_name,
            item_name=udhar_data.item_name,
            quantity=udhar_data.quantity,
            unit=udhar_data.unit,
            current_user=current_user,
            background_tasks=background_tasks   # ✅ ADDED
        )

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
    return await list_udharitems(db, current_user)


# =========================
# GET BY CUSTOMER NAME
# =========================
@router.get("/customer/{customer_name}", response_model=list[UdharRead])
async def get_udharitems_by_customer(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(Customer).where(
            Customer.customer_name == customer_name.strip(),
            Customer.user_id == current_user.user_id
        )
    )
    customer = res.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="کسٹمر موجود نہیں ہے")

    # reuse CRUD list and filter
    all_items = await list_udharitems(db, current_user)
    return [i for i in all_items if i["customer_id"] == customer.customer_id]


# =========================
# GET BY ID
# =========================
@router.get("/{item_id}", response_model=UdharRead)
async def get_udharitem(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = await list_udharitems(db, current_user)

    for item in items:
        if item["udharitem_id"] == item_id:
            return item

    raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")


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
        return await update_udharitem(db, item_id, data, current_user)

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
# SEARCH (UPDATED - NO JOIN)
# =========================
@router.get("/search/", response_model=list[UdharRead])
async def search_items(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = await list_udharitems(db, current_user)

    keyword = keyword.lower()

    return [
        i for i in items
        if i["item_name"] and keyword in i["item_name"].lower()
    ]
