from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from myapp.database.session import engine, Base
from myapp.api.ai_models import router as ai_router
from myapp.config import settings
# Routers 
from myapp.api.items import router as items
from myapp.api.customer import router as customers
from myapp.api.sales import router as sales
from myapp.api.udhar import router as udhar
from myapp.api.udhaar_item import router as udhaar_item
from myapp.api.bill import router as bill
from myapp.api.user import router as user 
from myapp.api.shop import router as shop
from myapp.api.report import router as report
from myapp.api.forcasting import router as forcast
from myapp.api.bill_item import router as bill_item
from myapp.api.bill_item_history import router as bill_item_history



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

# Create app
app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
from myapp.utils.errors import error_map
from fastapi.exceptions import RequestValidationError

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    error_label = error_map.get(exc.status_code, "نامعلوم مسئلہ")
    return JSONResponse(status_code=exc.status_code, content={"error": error_label, "detail": exc.detail})

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "غلط ویلیو", "detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cleaned_errors = []
    for err in exc.errors():
        if "ctx" in err:
            err["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        cleaned_errors.append(err)
    return JSONResponse(status_code=422, content={"error": "غلط ڈیٹا", "detail": cleaned_errors})

@app.exception_handler(Exception)
async def custom_general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "سرور کی خرابی", "detail": str(exc)})

app.include_router(ai_router)
app.include_router(user)
app.include_router(shop) 
app.include_router(items)
app.include_router(customers)
app.include_router(udhaar_item)
app.include_router(bill_item)
app.include_router(sales)
app.include_router(udhar)
app.include_router(bill)
app.include_router(bill_item_history)
app.include_router(report)
app.include_router(forcast)
