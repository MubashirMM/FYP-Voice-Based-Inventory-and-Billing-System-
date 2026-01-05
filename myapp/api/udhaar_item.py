from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.schemas.udhaar_item import UdharCreateRequest, UdharRead
from myapp.crud.udhaar_item import create_udhar, list_udharitems
from myapp.database.session import get_db
from myapp.utils.security import get_current_user
from myapp.models.user import User

router = APIRouter(prefix="/udhar-items", tags=["udhar items"])

@router.post("/", response_model=UdharRead)
async def create_new_udhar(
    udhar_data: UdharCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        udhar = await create_udhar(
            db=db,
            customer_name=udhar_data.customer_name,
            item_name=udhar_data.item_name,
            quantity=udhar_data.quantity,
            unit=udhar_data.unit,
            req_date=udhar_data.date_,
            current_user=current_user
        )
        return udhar
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"سرور خرابی: {str(e)}")

@router.get("/", response_model=list[UdharRead])
async def get_all_udharitems(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    udhar_items = await list_udharitems(db, current_user)
    return udhar_items
