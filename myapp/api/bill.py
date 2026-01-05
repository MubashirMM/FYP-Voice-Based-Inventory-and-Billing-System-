from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.schemas.bill import BillRead
from myapp.crud.bill import get_bills_by_customer,get_all_bills,pay_bill,delete_bill
from myapp.models.user import User
from myapp.utils.security import get_current_user



router = APIRouter(prefix="/bills", tags=["Bills"])

@router.get("/customer/{customer_id}", response_model=list[BillRead])
async def bill_history(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await get_bills_by_customer(db, customer_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی غیر ادا شدہ بل موجود نہیں")
    return res

@router.get("/", response_model=list[BillRead])
async def get_bills(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await get_all_bills(db, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی غیر ادا شدہ بل موجود نہیں")
    return res

@router.put("/customer/{customer_id}/pay", response_model=BillRead)
async def pay_customer_bill(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    bill = await pay_bill(db, customer_id, current_user)
    if not bill:
        raise HTTPException(status_code=404, detail="اس گاہک کا کوئی غیر ادا شدہ بل موجود نہیں")
    return bill

@router.delete("/{bill_id}")
async def delete_bill_endpoint(bill_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = await delete_bill(db, bill_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"detail": f"Bill {bill_id} deleted successfully"}
