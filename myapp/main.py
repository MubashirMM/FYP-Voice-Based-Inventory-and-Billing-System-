from contextlib import asynccontextmanager
from fastapi import FastAPI
from myapp.database.session import engine, Base
from myapp.api.items import router as items
from myapp.api.customer import router as customers
from myapp.api.sales import router as sales
from myapp.api.udhar import router as udhar
from myapp.api.udhaar_item import router as udhaar_item
from myapp.api.bill import router as bill
from myapp.api.user import router as user
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware 
from transformers import pipeline 
from myapp.api.shop import router as shop
from myapp.api.bill_item import router as bill_item
from fastapi import FastAPI, Request, HTTPException 
from fastapi.responses import JSONResponse

import torch 
import io

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

myapp = FastAPI(lifespan=lifespan)

# @myapp.exception_handler(HTTPException)
# async def custom_http_exception_handler(request: Request, exc: HTTPException):
#     if exc.status_code == 401:
#         return JSONResponse(status_code=401, content={"detail": "آپ کو اجازت نہیں ہے، براہ کرم پہلے لاگ ان کریں"})
#     elif exc.status_code == 404:
#         return JSONResponse(status_code=404, content={"detail": "ریکارڈ نہیں ملا"})
#     elif exc.status_code == 500:
#         return JSONResponse( status_code=500, content={ "detail": f"اندرونی سرور کی خرابی: {str(exc)}" } )
#     return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})



origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173"
]

myapp.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     
    allow_credentials=True,
    allow_methods=["*"],       # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],       # Allows common headers
)

myapp.include_router(user)
myapp.include_router(shop)
myapp.include_router(items)
myapp.include_router(customers)
myapp.include_router(udhaar_item)
myapp.include_router(bill_item)
myapp.include_router(sales)
myapp.include_router(udhar)
myapp.include_router(bill)

