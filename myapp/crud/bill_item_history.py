from sqlalchemy import select
from fastapi import HTTPException
from myapp.models.bill_item_history import BillItemHistory


async def get_all_bill_items(db, current_user):
    try:
        result = await db.execute(
            select(BillItemHistory)
            .where(BillItemHistory.user_id == current_user.user_id)
            .order_by(BillItemHistory.history_id.desc())
        )

        items = result.scalars().all()

        if not items:
            raise HTTPException(
                status_code=404,
                detail="کوئی ریکارڈ موجود نہیں ہے"
            )

        return items  # ✅ direct return (model_config handles it)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"سرور خرابی: {str(e)}"
        )
    
async def search_bill_items(db, current_user, item_name: str):
    try:
        result = await db.execute(
            select(BillItemHistory)
            .where(
                BillItemHistory.user_id == current_user.user_id,
                BillItemHistory.item_name.ilike(f"%{item_name}%")
            )
            .order_by(BillItemHistory.history_id.desc())
        )

        items = result.scalars().all()

        if not items:
            raise HTTPException(
                status_code=404,
                detail="اس نام کا کوئی آئٹم نہیں ملا"
            )

        return items  # ✅ clean

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"سرچ خرابی: {str(e)}"
        )