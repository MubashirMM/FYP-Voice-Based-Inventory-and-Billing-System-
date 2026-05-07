import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from myapp.main import app
from myapp.database.session import Base, get_db

# Test database URL - UPDATE THIS WITH YOUR PASSWORD
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_db"

# Create engine for testing
test_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

# Override database dependency
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

# ============ Database Fixtures ============
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Create tables before each test and drop after"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for tests"""
    async with TestingSessionLocal() as session:
        yield session

# ============ Client Fixtures ============
@pytest.fixture(scope="function")
def client() -> Generator:
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

# ============ User Data Fixtures ============
@pytest.fixture
def test_user_data():
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "TestPassword123!"
    }

@pytest.fixture
def test_user_data_2():
    return {
        "email": "testuser2@example.com",
        "username": "testuser2",
        "password": "TestPassword456!"
    }

# ============ User Creation Fixtures ============
@pytest_asyncio.fixture
async def create_test_user(db_session: AsyncSession, test_user_data):
    """Create a test user in database"""
    from myapp.crud.user import register_user
    
    user = await register_user(
        db_session,
        test_user_data["email"],
        test_user_data["username"],
        test_user_data["password"]
    )
    return user

# ============ Authentication Fixtures ============
@pytest.fixture
def auth_token(create_test_user):
    """Create authentication token for test user"""
    from myapp.utils.security import create_access_token
    token = create_access_token({"sub": str(create_test_user.user_id)})
    return token

@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}

# ============ Customer Creation Fixtures ============
@pytest_asyncio.fixture
async def create_test_customer(db_session: AsyncSession, create_test_user):
    """Create a test customer using the correct CRUD function"""
    from myapp.schemas.customer import CustomerCreate
    from myapp.crud.customer import create_customers  # ✅ Note: plural "create_customers"
    
    customer_data = CustomerCreate(
        customer_name="کسٹمر",  # Test customer name
        phone_number="03001234567",
        address="ٹیسٹ ایڈریس"
    )
    
    customer = await create_customers(
        db_session,
        customer_data,
        create_test_user
    )
    return customer

# ============ Udhar Creation Fixtures ============
@pytest_asyncio.fixture
async def create_test_udhar(db_session: AsyncSession, create_test_customer, create_test_user):
    """Create a test udhar record"""
    from myapp.crud.udhar import get_or_create_unpaid_udhar
    
    udhar = await get_or_create_unpaid_udhar(
        db_session,
        create_test_customer.customer_id,
        create_test_user
    )
    
    # Add initial amount for testing
    udhar.subtotal = 1000.0
    udhar.total = 1000.0
    await db_session.commit()
    await db_session.refresh(udhar)
    
    return udhar

# ============ Bill Creation Fixtures ============
@pytest_asyncio.fixture
async def create_test_bill(db_session: AsyncSession, create_test_customer, create_test_user):
    """Create a test bill for tests"""
    from myapp.models.bill import Bill
    from datetime import datetime
    
    # Create a bill
    bill = Bill(
        customer_id=create_test_customer.customer_id,
        total_amount=5000.00,
        effective_total=5000.00,
        status="unpaid",
        user_id=create_test_user.user_id,
        created_at=datetime.now()
    )
    db_session.add(bill)
    await db_session.commit()
    await db_session.refresh(bill)
    return bill

# ============ Verified User Fixture ============
@pytest_asyncio.fixture
async def verified_user(db_session: AsyncSession, test_user_data):
    """Create a verified test user (async version)"""
    from myapp.models.user import User
    from myapp.utils.security import hash_password
    
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=hash_password(test_user_data["password"]),
        is_verified=True,  # Auto-verified for tests
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

# Corrected create_test_bill fixture for conftest.py

@pytest_asyncio.fixture
async def create_test_bill(db_session: AsyncSession, create_test_customer, create_test_user):
    """Create a test bill for tests"""
    from myapp.models.bill import Bill
    from datetime import date
    from myapp.utils.urdu_date import convert_date_to_urdu
    
    # Get current date and convert to Urdu format
    today = date.today()
    urdu_date = convert_date_to_urdu(today, "bill")
    
    bill = Bill(
        customer_id=create_test_customer.customer_id,
        user_id=create_test_user.user_id,
        customer_name=create_test_customer.customer_name,
        udhar_items_total=5000.00,
        direct_addition=0.0,
        direct_deduction=0.0,
        effective_total=5000.00,
        status="unpaid",
        bill_date=today,
        bill_day=urdu_date["bill_day"],      # Note: key is "bill_day" not "day"
        bill_month=urdu_date["bill_month"],
        bill_year=urdu_date["bill_year"],
        bill_day_name=urdu_date["bill_day_name"],
        bill_time=""  # You're not using time in Bill model
    )
    
    db_session.add(bill)
    await db_session.commit()
    await db_session.refresh(bill)
    return bill