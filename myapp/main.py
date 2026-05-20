# from contextlib import asynccontextmanager
# from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from myapp.database.session import engine, Base
# from myapp.api.ai_models import router as ai_router
# from myapp.config import settings
# # Routers 
# from myapp.api.items import router as items
# from myapp.api.customer import router as customers
# from myapp.api.sales import router as sales
# from myapp.api.udhar import router as udhar
# from myapp.api.udhaar_item import router as udhaar_item
# from myapp.api.bill import router as bill
# from myapp.api.user import router as user 
# from myapp.api.shop import router as shop
# from myapp.api.report import router as report
# from myapp.api.forcasting import router as forcast
# from myapp.api.bill_item import router as bill_item
# from myapp.api.bill_item_history import router as bill_item_history
# from myapp.crud.user import preload_voice_model

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # STARTUP - Everything here runs before the app starts
#     print("🔄 Starting up...")
    
#     # Create database tables
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
    
#     # Preload voice model (moved before yield)
#     await preload_voice_model()
    
#     print("✅ Startup complete!")
    
#     yield  # The app runs here
    
#     # SHUTDOWN - Everything here runs when the app is shutting down
#     print("🔄 Shutting down...")
#     await engine.dispose()
#     print("✅ Shutdown complete!")

# # Create app
# app = FastAPI(lifespan=lifespan)


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,    
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Error handlers
# from myapp.utils.errors import error_map
# from fastapi.exceptions import RequestValidationError

# @app.exception_handler(HTTPException)
# async def custom_http_exception_handler(request: Request, exc: HTTPException):
#     error_label = error_map.get(exc.status_code, "نامعلوم مسئلہ")
#     return JSONResponse(status_code=exc.status_code, content={"error": error_label, "detail": exc.detail})

# @app.exception_handler(ValueError)
# async def value_error_handler(request: Request, exc: ValueError):
#     return JSONResponse(status_code=400, content={"error": "غلط ویلیو", "detail": str(exc)})

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     cleaned_errors = []
#     for err in exc.errors():
#         if "ctx" in err:
#             err["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
#         cleaned_errors.append(err)
#     return JSONResponse(status_code=422, content={"error": "غلط ڈیٹا", "detail": cleaned_errors})

# @app.exception_handler(Exception)
# async def custom_general_exception_handler(request: Request, exc: Exception):
#     return JSONResponse(status_code=500, content={"error": "سرور کی خرابی", "detail": str(exc)})

# app.include_router(ai_router)
# app.include_router(user)
# app.include_router(shop) 
# app.include_router(items)
# app.include_router(customers)
# app.include_router(udhaar_item)
# app.include_router(bill_item)
# app.include_router(sales)
# app.include_router(udhar)
# app.include_router(bill)
# app.include_router(bill_item_history)
# app.include_router(report)
# app.include_router(forcast)

# # myapp/main.py - Performance optimized
# myapp/main.py - Performance optimized (FIXED)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
from myapp.crud.user import preload_voice_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 STARTUP
    print("🚀 Starting Shop Management System...")
    
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Preload voice model only (keep it simple like old working code)
        await preload_voice_model()
        
        # Lazy initialize AI model clients (don't fail if there's an issue)
        try:
            from myapp.crud.ai_models.ai_models_base import AiohttpSessionManager, ClientPool
            
            # Initialize HTTP session
            await AiohttpSessionManager.get_session()
            
            # Pre-initialize all module clients (with error handling per module)
            for module in ["items", "udhaar_items", "udhaars", "bills"]:
                try:
                    client = ClientPool.get_client(module)
                    print(f"📦 Module '{module}': {len(client.api_keys)} API keys loaded")
                except Exception as e:
                    print(f"⚠️  Warning: Module '{module}' initialization failed: {e}")
        except ImportError as e:
            print(f"⚠️  Warning: AI models base not available: {e}")
        except Exception as e:
            print(f"⚠️  Warning: AI models initialization failed: {e}")
        
        print("✅ System ready!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        # Don't raise - let the app start anyway
    
    yield  # App runs here
    
    # 🔄 SHUTDOWN
    print("🔄 Shutting down...")
    try:
        from myapp.crud.ai_models.ai_models_base import AiohttpSessionManager
        await AiohttpSessionManager.close()
    except:
        pass
    
    await engine.dispose()
    print("✅ Shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="Shop Management System",
    version="2.0.0",
    lifespan=lifespan,
)

# Performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers (same order as old working code)
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