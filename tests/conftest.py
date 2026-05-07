
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from myapp.main import app
from myapp.database.session import Base, get_db

# Test database URL - UPDATE THIS WITH YOUR PASSWORD
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_db"

# Create engine for testing
test_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

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

@pytest_asyncio.fixture
async def create_test_customer(db_session: AsyncSession, create_test_user):
    """Create a test customer for udhar tests"""
    from myapp.crud.customer import create_customer
    
    customer = await create_customer(
        db_session,
        customer_name="کسٹمر",
        phone_number="03001234567",
        address="ٹیسٹ ایڈریس",
        current_user=create_test_user
    )
    return customer

@pytest_asyncio.fixture
async def create_test_customer(db_session: AsyncSession, create_test_user):
    """Create a test customer for udhar tests"""
    from myapp.crud.customer import create_customer
    
    customer = await create_customer(
        db_session,
        customer_name="کسٹمر",
        phone_number="03001234567",
        address="ٹیسٹ ایڈریس",
        current_user=create_test_user
    )
    return customer

@pytest_asyncio.fixture
async def create_test_bill(db_session: AsyncSession, create_test_customer, create_test_user):
    """Create a test bill for tests"""
    from myapp.models.bill import Bill
    from myapp.crud.bill import create_bill
    
    # Create a bill
    bill = Bill(
        customer_id=create_test_customer.customer_id,
        total_amount=5000.00,
        status="unpaid",
        user_id=create_test_user.user_id
    )
    db_session.add(bill)
    await db_session.commit()
    await db_session.refresh(bill)
    return bill

@pytest.fixture
def verified_user(db_session, test_user_data):
    """Create a verified test user"""
    from myapp.models.user import User
    from myapp.utils.security import hash_password
      
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=hash_password(test_user_data["password"]),
        is_verified=True,  # Key: auto-verified for tests
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user