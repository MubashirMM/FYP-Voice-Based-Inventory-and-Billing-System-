# routers/forecast.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from myapp.database.session import get_db
from myapp.models.sales import Sale
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt
from fastapi.responses import JSONResponse
import base64
from io import BytesIO

router = APIRouter(prefix="/forecast", tags=["Forecast"])

@router.get("/")
async def forecast_sales(db: AsyncSession = Depends(get_db), periods: int = 3):
    # 1. Query sales data
    result = await db.execute(select(Sale))
    sales = result.scalars().all()

    df = pd.DataFrame([{"ds": s.sale_date, "y": s.quantity_sold} for s in sales])
    if df.empty:
        return {"error": "No sales data available"}

    # 2. Fit Prophet
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(df)

    # 3. Forecast
    future = model.make_future_dataframe(periods=periods, freq="W")
    forecast = model.predict(future)

    # 4. Prepare JSON report (convert Timestamp to string)
    report = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    report["ds"] = report["ds"].astype(str)   # <-- key fix
    report = report.to_dict(orient="records")

    # 5. Generate graph
    fig = model.plot(forecast)
    plt.title("Sales Forecast (Prophet)")
    plt.xlabel("Date")
    plt.ylabel("Predicted Sales")

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    # 6. Return both JSON + graph
    return JSONResponse(content={
        "forecast": report,
        "graph": f"data:image/png;base64,{img_base64}"
    })
