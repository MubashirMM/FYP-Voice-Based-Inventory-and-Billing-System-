from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.database.session import get_db
from myapp.schemas.bill_item import BillItemCreate, BillItemRead
from myapp.crud.bill_item import (
    list_bill_items,
    get_bill_item_by_id,
    delete_bill_item,
    search_bill_items
)
from myapp.models.user import User
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession


from myapp.utils.security import get_current_user
from myapp.crud.bill_item import (
    add_to_cart,
    get_cart_items,
    remove_from_cart,
    clear_cart,
    generate_bill_from_cart
)

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/add", response_model=BillItemRead)
async def add_item_to_cart(
    item_name: str,           # ← Like Udhaar
    quantity: float,          # ← Like Udhaar  
    requested_unit: str,      # ← Like Udhaar
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add item to cart (same style as Udhaar)"""
    data = {
        "item_name": item_name,
        "quantity": quantity,
        "requested_unit": requested_unit
    }
    return await add_to_cart(db, data, current_user, background_tasks)



@router.get("/items")
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items in cart"""
    return await get_cart_items(db, current_user)


@router.delete("/item/{cart_item_id}")
async def remove_cart_item(
    cart_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove item from cart"""
    return await remove_from_cart(db, cart_item_id, current_user)


@router.delete("/clear")
async def clear_cart_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all items from cart"""
    return await clear_cart(db, current_user)


@router.post("/generate-bill")
async def generate_bill(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate bill from all cart items"""
    return await generate_bill_from_cart(db, current_user, background_tasks)

# =========================
# LIST ALL
# =========================
@router.get("/", response_model=list[BillItemRead])
async def get_all_bill_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await list_bill_items(db, current_user)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# GET BY ID
# =========================
@router.get("/{billitem_id}", response_model=BillItemRead)
async def get_bill_item(
    billitem_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await get_bill_item_by_id(db, billitem_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# DELETE
# =========================
@router.delete("/{billitem_id}")
async def delete_bill_item_endpoint(
    billitem_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await delete_bill_item(db, billitem_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")


# =========================
# SEARCH
# =========================
@router.get("/search/", response_model=list[BillItemRead])
async def search_bill_items_endpoint(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if not keyword or not keyword.strip():
            raise HTTPException(status_code=400, detail="سرچ کی ورڈ درکار ہے")

        return await search_bill_items(db, keyword, current_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")