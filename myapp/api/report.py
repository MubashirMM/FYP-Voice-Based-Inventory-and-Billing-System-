# routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract
from myapp.database.session import get_db
from myapp.models.sales import Sale
from myapp.models.item import Item
from myapp.models.user import User
from myapp.utils.security import get_current_user
from myapp.utils.report_charts import generate_charts, generate_interactive_charts
from sqlalchemy.orm import selectinload
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/generate")
async def generate_sales_report(
    item_name: str | None = None,
    year: int | None = None,
    month: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None, 
    frequency: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    stmt = (
        select(Sale)
        .options(selectinload(Sale.item))   # preload related Item
        .where(Sale.user_id == current_user.user_id)
    )

    # 2. Apply filters
    if item_name:
        stmt = stmt.join(Item).where(Item.item_name == item_name)
    if year:
        stmt = stmt.where(extract("year", Sale.sale_date) == year)
    if month:
        stmt = stmt.where(extract("month", Sale.sale_date) == month)
    if start_date and end_date:
        try:
            sd = datetime.fromisoformat(start_date)
            ed = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="تاریخ کا فارمیٹ درست نہیں ہے (YYYY-MM-DD)")
        stmt = stmt.where(Sale.sale_date.between(sd, ed))

    # 3. Execute
    res = await db.execute(stmt)
    sales = res.scalars().all()
    if not sales:
        raise HTTPException(status_code=404, detail="فروخت کا ڈیٹا نہیں ملا")

    # 4. KPIs
    total_quantity = sum(s.quantity_sold for s in sales)
    total_revenue = sum(s.quantity_sold * float(s.item.unit_price) for s in sales)
    kpi_summary = {
        "کل فروخت": total_quantity,
        "کل آمدنی": f"{total_revenue:.2f}",
    }

    # 5. Charts
    charts_static = generate_charts(item_name or "تمام آئٹمز", sales)
    charts_interactive = generate_interactive_charts(item_name or "تمام آئٹمز", sales)

    # 6. Table
    table = [{"تاریخ": str(s.sale_date), "مقدار": s.quantity_sold} for s in sales]

    # 7. Dynamic title
    title = build_dynamic_title(item_name, year, month, start_date, end_date, frequency)

    return {
        "title": title,
        "kpi_summary": kpi_summary,
        "charts_static": charts_static,
        "charts_interactive": charts_interactive,
        "table": table
    }

def build_dynamic_title(item_name, year, month, start_date, end_date, frequency):
    if item_name and year and month:
        return f"{item_name} - {year}/{month} کی فروخت رپورٹ"
    elif item_name and year:
        return f"{item_name} - {year} کی فروخت رپورٹ"
    elif item_name:
        return f"{item_name} کی فروخت رپورٹ"
    elif year and month:
        return f"{year}/{month} کی فروخت رپورٹ"
    elif year:
        return f"{year} کی فروخت رپورٹ"
    elif start_date and end_date:
        return f"فروخت رپورٹ ({start_date} سے {end_date})"
    elif frequency:
        return f"{frequency.capitalize()} فروخت رپورٹ"
    else:
        return "مکمل فروخت رپورٹ"
