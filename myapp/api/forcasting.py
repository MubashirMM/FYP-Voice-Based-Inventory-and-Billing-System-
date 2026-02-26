# routers/forecast.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from myapp.database.session import get_db
from myapp.models.sales import Sale
from myapp.models.user import User
from myapp.utils.security import get_current_user
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt
from fastapi.responses import JSONResponse
import base64
from io import BytesIO

router = APIRouter(prefix="/forecast", tags=["Forecast"])

@router.get("/")
async def forecast_sales(
    periods: int = 3,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Query sales data for the logged-in user
    result = await db.execute(
        select(Sale).where(Sale.user_id == current_user.user_id)  # ✅ fixed here
    )
    sales = result.scalars().all()

    if not sales:
        raise HTTPException(status_code=404, detail="اس صارف کے لئے کوئی سیلز ڈیٹا موجود نہیں ہے")

    # 2. Prepare DataFrame
    df = pd.DataFrame([{"ds": s.sale_date, "y": s.quantity_sold} for s in sales])
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df = df.dropna(subset=["ds", "y"])
    if df.empty:
        raise HTTPException(status_code=400, detail="سیلز ڈیٹا درست نہیں ہے")

    # 3. Fit Prophet
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(df)

    # 4. Forecast
    future = model.make_future_dataframe(periods=periods, freq="W")
    forecast = model.predict(future)

    # 5. Prepare JSON report
    report = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    report["ds"] = report["ds"].astype(str)
    report = report.to_dict(orient="records")

    # 6. Generate graph
    fig = model.plot(forecast)
    plt.title(f"Sales Forecast for User {current_user.user_id}")
    plt.xlabel("Date")
    plt.ylabel("Predicted Sales")

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return JSONResponse(content={
        "forecast": report,
        "graph": f"data:image/png;base64,{img_base64}"
    })