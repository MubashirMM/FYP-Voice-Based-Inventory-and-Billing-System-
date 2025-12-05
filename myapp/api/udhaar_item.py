# routers/udharitem.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.schemas.udhaar_item import UdharCreateRequest, UdharRead
from myapp.crud.udhaar_item import create_udhar, list_udharitems
from myapp.database.session import get_db

router = APIRouter(prefix="/udhar-items", tags=["udhar items"])

@router.post("/", response_model=UdharRead)
async def create_new_udhar(
    udhar_data: UdharCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new udhar transaction"""
    try:
        udhar = await create_udhar(
            db=db,
            customer_name=udhar_data.customer_name,
            item_name=udhar_data.item_name,
            quantity=udhar_data.quantity,
            unit=udhar_data.unit,
            req_date=udhar_data.date_
        )
        return udhar
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")

@router.get("/", response_model=list[UdharRead])
async def get_all_udharitems(db: AsyncSession = Depends(get_db)):
    """Get all udhar transactions"""
    udhar_items = await list_udharitems(db)
    return udhar_items