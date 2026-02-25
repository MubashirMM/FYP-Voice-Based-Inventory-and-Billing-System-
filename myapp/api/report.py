from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from myapp.database.session import get_db
from myapp.crud import report as crud_report
from myapp.schemas.report import ReportGenerateRequest, ReportResponse, ReportListResponse
from myapp.models.sales import Sale
from myapp.models.item import Item
from myapp.utils.security import get_current_user
from myapp.models.user import User
from myapp.utils.report_charts import generate_charts

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_sales_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch item for this user
    stmt_item = select(Item).where(Item.item_name == request.item_name, Item.user_id == current_user.user_id)
    res_item = await db.execute(stmt_item)
    item = res_item.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="آئٹم نہیں ملا")

    # 2. Fetch sales data
    stmt_sales = select(Sale).where(Sale.item_id == item.item_id, Sale.user_id == current_user.user_id)
    res_sales = await db.execute(stmt_sales)
    sales = res_sales.scalars().all()
    if not sales:
        raise HTTPException(status_code=404, detail="اس آئٹم کی فروخت نہیں ملی")

    # 3. Compute KPIs
    total_quantity = sum(s.quantity_sold for s in sales)
    total_revenue = sum(s.quantity_sold * float(item.unit_price) for s in sales)
    kpi_summary = {
        "کل فروخت": total_quantity,
        "کل آمدنی": f"{total_revenue:.2f}",
        "مصنوعات کی اکائی": item.item_unit,
        "فی اکائی قیمت": f"{item.unit_price:.2f}",
        "اسٹاک میں باقی مقدار": item.stock_quantity,
    }

    # 4. Generate real charts
    charts_paths = generate_charts(request.item_name, sales)

    # 5. Save report metadata
    report = await crud_report.create_report_async(
        db=db,
        user_id=current_user.user_id,
        item_name=request.item_name,
        kpi_summary=kpi_summary,
        charts_paths=charts_paths,
        filters_applied=request.filters_applied
    )

    return report
