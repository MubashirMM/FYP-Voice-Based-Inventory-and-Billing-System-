from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from fastapi import HTTPException
from myapp.models.sales import Sale
from myapp.models.user import User

async def delete_sale_by_id(db: AsyncSession, sale_id: int, current_user: User):
    # Find the sale by id scoped to user
    res = await db.execute(
        select(Sale).where(
            Sale.sale_id == sale_id,
            Sale.user_id == current_user.user_id
        )
    )
    sale = res.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="یہ فروخت موجود نہیں ہے")

    # Delete the sale
    await db.execute(
        delete(Sale).where(
            Sale.sale_id == sale.sale_id,
            Sale.user_id == current_user.user_id
        )
    )

    await db.commit()
    return {"message": "فروخت کامیابی سے حذف کر دی گئی"}
