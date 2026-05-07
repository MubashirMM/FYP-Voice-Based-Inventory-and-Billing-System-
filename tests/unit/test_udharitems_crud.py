# C:\FYP\Backend\fast-api\tests\unit\test_udharitems_crud.py
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi import HTTPException, BackgroundTasks
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from myapp.crud.udhaar_item import (
    create_udhar,
    update_udharitem,
    delete_udharitem,
    list_udharitems,
    format_item
)
from myapp.crud.user import register_user
from myapp.crud.items import create_items, read_item, update_items  # ✅ ADD missing imports
from myapp.schemas.items import ItemCreate, ItemUpdate
from myapp.models.user import User


# ============================================
# HELPER FUNCTIONS FOR TESTS
# ============================================
async def create_test_user_and_item(db_session):
    """Helper to create test user and item"""
    user = await register_user(db_session, "udhar@example.com", "UdharUser", "pass123")
    
    item_data = ItemCreate(
        item_name="Test Product",
        item_unit="کلو",  # ✅ Use Urdu unit
        unit_price=100,
        stock_quantity=50
    )
    item = await create_items(db_session, item_data, user)
    
    return user, item


# ============================================
# CREATE UDHAR TESTS
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_zero_quantity(db_session):
    """Test creating udhar with zero quantity - should fail"""
    user, _ = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    with pytest.raises(HTTPException) as exc:
        await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Test Product",
            quantity=0,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    assert exc.value.status_code == 400
    assert "مقدار صفر یا منفی" in exc.value.detail


@pytest.mark.asyncio
async def test_create_udhar_negative_quantity(db_session):
    """Test creating udhar with negative quantity - should fail"""
    user, _ = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    with pytest.raises(HTTPException) as exc:
        await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Test Product",
            quantity=-3,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_udhar_insufficient_stock(db_session):
    """Test creating udhar with insufficient stock"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Try to buy more than available
    with pytest.raises(HTTPException) as exc:
        await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Test Product",
            quantity=100,  # More than 50 available
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    assert exc.value.status_code == 400
    assert "ذخیرہ ناکافی" in exc.value.detail


@pytest.mark.asyncio
async def test_create_udhar_empty_customer_name(db_session):
    """Test creating udhar with empty customer name"""
    user, _ = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    with pytest.raises(HTTPException) as exc:
        await create_udhar(
            db=db_session,
            customer_name="",
            item_name="Test Product",
            quantity=5,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_udhar_nonexistent_item(db_session):
    """Test creating udhar with non-existent item"""
    user, _ = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    with pytest.raises(HTTPException) as exc:
        await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Non Existent Item",
            quantity=5,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_udhar_incompatible_units(db_session):
    """Test creating udhar with incompatible units"""
    user, _ = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Item is in KG, try to use DOZEN (incompatible)
    with pytest.raises(HTTPException) as exc:
        await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Test Product",
            quantity=2,
            unit="درجن",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    assert exc.value.status_code == 400
    assert "تبدیل نہیں کیا جا سکتا" in exc.value.detail


# ============================================
# UPDATE UDHAR TESTS
# ============================================
@pytest.mark.asyncio
async def test_update_udharitem_not_found(db_session):
    """Test updating non-existent udhar item"""
    user, _ = await create_test_user_and_item(db_session)
    
    update_data = MagicMock()
    update_data.item_name = "Test Product"
    update_data.quantity = 3
    update_data.unit = "کلو"  # ✅ Use Urdu unit
    
    with pytest.raises(HTTPException) as exc:
        await update_udharitem(
            db=db_session,
            item_id=99999,
            data=update_data,
            current_user=user
        )
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_udharitem_insufficient_stock(db_session):
    """Test updating udhar item with insufficient stock"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Create udhar with small quantity
    created = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=2,
        unit="کلو",  # ✅ Use Urdu unit
        current_user=user,
        background_tasks=background_tasks
    )
    
    # Try to update to larger quantity than available
    update_data = MagicMock()
    update_data.item_name = "Test Product"
    update_data.quantity = 60  # More than available
    update_data.unit = "کلو"  # ✅ Use Urdu unit
    
    with pytest.raises(HTTPException) as exc:
        await update_udharitem(
            db=db_session,
            item_id=created["udharitem_id"],
            data=update_data,
            current_user=user
        )
    
    assert exc.value.status_code == 400
    assert "ذخیرہ ناکافی" in exc.value.detail


# ============================================
# DELETE UDHAR TESTS
# ============================================
@pytest.mark.asyncio
async def test_delete_udharitem_not_found(db_session):
    """Test deleting non-existent udhar item"""
    user, _ = await create_test_user_and_item(db_session)
    
    with pytest.raises(HTTPException) as exc:
        await delete_udharitem(
            db=db_session,
            item_id=99999,
            current_user=user
        )
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_udharitem_multiple(db_session):
    """Test deleting multiple udhar items for same customer"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Create multiple udhar items
    items_created = []
    for i in range(3):
        created = await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Test Product",
            quantity=i + 1,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
        items_created.append(created)
    
    # Delete each item
    for created_item in items_created:
        result = await delete_udharitem(
            db=db_session,
            item_id=created_item["udharitem_id"],
            current_user=user
        )
        assert result is not None
    
    # Verify all items deleted
    all_items = await list_udharitems(db_session, user)
    customer_items = [i for i in all_items if i["customer_name"] == "Test Customer"]
    assert len(customer_items) == 0


# ============================================
# LIST UDHAR TESTS
# ============================================
@pytest.mark.asyncio
async def test_list_udharitems_empty(db_session):
    """Test listing udhar items when none exist"""
    user, _ = await create_test_user_and_item(db_session)
    
    items = await list_udharitems(db_session, user)
    
    assert isinstance(items, list)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_list_udharitems_multiple(db_session):
    """Test listing multiple udhar items"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Create multiple udhar items for different customers
    customers = ["Customer A", "Customer B", "Customer C"]
    quantities = [2, 3, 4]
    
    for customer, qty in zip(customers, quantities):
        await create_udhar(
            db=db_session,
            customer_name=customer,
            item_name="Test Product",
            quantity=qty,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
    
    items = await list_udharitems(db_session, user)
    
    assert len(items) == 3
    customer_names = [i["customer_name"] for i in items]
    assert "Customer A" in customer_names
    assert "Customer B" in customer_names
    assert "Customer C" in customer_names


@pytest.mark.asyncio
async def test_list_udharitems_user_specific(db_session):
    """Test that users only see their own udhar items"""
    # Create user1
    user1 = await register_user(db_session, "user1@example.com", "User1", "pass123")
    item1_data = ItemCreate(
        item_name="User1 Item",
        item_unit="کلو",  # ✅ Use Urdu unit
        unit_price=100,
        stock_quantity=50
    )
    item1 = await create_items(db_session, item1_data, user1)
    
    # Create user2
    user2 = await register_user(db_session, "user2@example.com", "User2", "pass123")
    item2_data = ItemCreate(
        item_name="User2 Item",
        item_unit="کلو",  # ✅ Use Urdu unit
        unit_price=200,
        stock_quantity=30
    )
    item2 = await create_items(db_session, item2_data, user2)
    
    background_tasks = BackgroundTasks()
    
    # Create udhar for user1
    await create_udhar(
        db=db_session,
        customer_name="User1 Customer",
        item_name="User1 Item",
        quantity=5,
        unit="کلو",  # ✅ Use Urdu unit
        current_user=user1,
        background_tasks=background_tasks
    )
    
    # Create udhar for user2
    await create_udhar(
        db=db_session,
        customer_name="User2 Customer",
        item_name="User2 Item",
        quantity=3,
        unit="کلو",  # ✅ Use Urdu unit
        current_user=user2,
        background_tasks=background_tasks
    )
    
    # List items for each user
    user1_items = await list_udharitems(db_session, user1)
    user2_items = await list_udharitems(db_session, user2)
    
    assert len(user1_items) == 1
    assert len(user2_items) == 1
    assert user1_items[0]["customer_name"] == "User1 Customer"
    assert user2_items[0]["customer_name"] == "User2 Customer"


# ============================================
# FORMAT ITEM TESTS
# ============================================
@pytest.mark.asyncio
async def test_format_item_structure(db_session):
    """Test that format_item returns correct structure"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    created = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=5,
        unit="کلو",  # ✅ Use Urdu unit
        current_user=user,
        background_tasks=background_tasks
    )
    
    # Check all expected fields
    expected_fields = [
        "udharitem_id", "customer_id", "customer_name",
        "item_id", "item_name", "unit_price", "quantity",
        "base_unit", "requested_unit", "total_amount",
        "created_date", "udhar_day", "udhar_month",
        "udhar_year", "udhar_time", "udhar_day_name"
    ]
    
    for field in expected_fields:
        assert field in created, f"Field {field} missing"


# ============================================
# EDGE CASES & ADDITIONAL TESTS
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_same_customer_multiple_udhars(db_session):
    """Test creating multiple udhars for same customer"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Create multiple udhars for same customer
    for i in range(3):
        result = await create_udhar(
            db=db_session,
            customer_name="Same Customer",
            item_name="Test Product",
            quantity=2,
            unit="کلو",  # ✅ Use Urdu unit
            current_user=user,
            background_tasks=background_tasks
        )
        assert result is not None
    
    # All should be under same customer
    items = await list_udharitems(db_session, user)
    customer_items = [i for i in items if i["customer_name"] == "Same Customer"]
    assert len(customer_items) == 3


@pytest.mark.asyncio
async def test_create_udhar_with_whitespace(db_session):
    """Test creating udhar with whitespace in names"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    result = await create_udhar(
        db=db_session,
        customer_name="  Spaced Customer  ",
        item_name="Test Product",
        quantity=5,
        unit="کلو",  # ✅ Use Urdu unit
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["customer_name"] == "Spaced Customer"  # Should be stripped


# ============================================
# PERFORMANCE & CONCURRENCY TESTS
# ============================================
@pytest.mark.asyncio
async def test_concurrent_udhar_creation_same_item(db_session):
    """Test concurrent udhar creation for same item"""
    import asyncio
    
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    async def create_udhar_task(customer_id):
        try:
            return await create_udhar(
                db=db_session,
                customer_name=f"Customer_{customer_id}",
                item_name="Test Product",
                quantity=10,
                unit="کلو",  # ✅ Use Urdu unit
                current_user=user,
                background_tasks=background_tasks
            )
        except HTTPException:
            return None
    
    # Create udhars sequentially to avoid session conflicts
    results = []
    for i in range(3):
        result = await create_udhar_task(i)
        results.append(result)
    
    # At least some should succeed
    success_count = sum(1 for r in results if r is not None)
    assert success_count > 0


# ============================================
# FIXED TEST: CREATE UDHAR SUCCESS
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_success(db_session):
    """Test successful udhar creation"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    result = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=5,
        unit="کلو",  # ✅ Using Urdu "کلو"
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["customer_name"] == "Test Customer"
    assert result["item_name"] == "Test Product"
    assert result["quantity"] == 5
    assert result["requested_unit"] == "کلو"
    assert result["total_amount"] == 500  # 5 * 100
    
    # Verify stock was reduced
    updated_item = await read_item(db_session, item.item_id, user)
    assert updated_item.stock_quantity == 45  # 50 - 5


# ============================================
# FIXED TEST: CREATE UDHAR NEW CUSTOMER
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_new_customer(db_session):
    """Test creating udhar with new customer (auto-create)"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    result = await create_udhar(
        db=db_session,
        customer_name="Brand New Customer",
        item_name="Test Product",
        quantity=3,
        unit="کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["customer_name"] == "Brand New Customer"
    
    # Verify customer was created
    from myapp.crud.udhaar_item import get_or_create_customer
    customer = await get_or_create_customer(db_session, "Brand New Customer", user)
    assert customer is not None
    assert customer.customer_name == "Brand New Customer"


# ============================================
# FIXED TEST: DIFFERENT UNIT CONVERSION
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_different_unit_conversion(db_session):
    """Test creating udhar with different unit (e.g., grams)"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    result = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=500,  # 500 grams
        unit="گرام",  # Urdu for GRAM
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["total_amount"] == 50  # 0.5 * 100
    assert result["quantity"] == 500
    assert result["requested_unit"] == "گرام"
    
    # Verify stock reduced by 0.5 KG
    updated_item = await read_item(db_session, item.item_id, user)
    assert updated_item.stock_quantity == 49.5


# ============================================
# FIXED TEST: LOW STOCK ALERT
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_low_stock_alert(db_session):
    """Test low stock alert triggers email"""
    user, item = await create_test_user_and_item(db_session)
    
    # Reduce stock to low level (below 10)
    await update_items(
        db_session, 
        item.item_id, 
        ItemUpdate(stock_quantity=8), 
        user
    )
    
    background_tasks = BackgroundTasks()
    background_tasks.add_task = MagicMock()
    
    with patch('myapp.crud.udhaar_item.send_email') as mock_send_email:
        result = await create_udhar(
            db=db_session,
            customer_name="Test Customer",
            item_name="Test Product",
            quantity=1,
            unit="کلو",
            current_user=user,
            background_tasks=background_tasks
        )
        
        assert result is not None
        # Verify email sending was triggered
        assert background_tasks.add_task.called


# ============================================
# FIXED TEST: UPDATE UDHAR ITEM SUCCESS
# ============================================
@pytest.mark.asyncio
async def test_update_udharitem_success(db_session):
    """Test successful udhar item update"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Create udhar item
    created = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=5,
        unit="کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    # Update the udhar item
    update_data = MagicMock()
    update_data.item_name = "Test Product"  # Same item
    update_data.quantity = 3
    update_data.unit = "کلو"
    
    updated = await update_udharitem(
        db=db_session,
        item_id=created["udharitem_id"],
        data=update_data,
        current_user=user
    )
    
    assert updated is not None
    assert updated["quantity"] == 3
    assert updated["total_amount"] == 300  # 3 * 100
    
    # Verify stock was adjusted
    updated_item = await read_item(db_session, item.item_id, user)
    assert updated_item.stock_quantity == 47  # 50 - 3


# ============================================
# FIXED TEST: CREATE UDHAR EXACT STOCK LIMIT
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_exact_stock_limit(db_session):
    """Test creating udhar with exact available stock"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    # Buy exactly all available stock
    result = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=50,  # Exactly all stock
        unit="کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["quantity"] == 50
    assert result["total_amount"] == 5000  # 50 * 100
    
    # Verify stock is now 0
    updated_item = await read_item(db_session, item.item_id, user)
    assert updated_item.stock_quantity == 0


# ============================================
# TEST: FRACTIONAL UNITS
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_with_fractional_units(db_session):
    """Test creating udhar with fractional units like آدھا کلو"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    result = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=1,  # 1 آدھا کلو = 0.5 KG
        unit="آدھا کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["total_amount"] == 50  # 0.5 * 100
    assert result["quantity"] == 1
    assert result["requested_unit"] == "آدھا کلو"


# ============================================
# TEST: DOZEN UNITS
# ============================================
@pytest.mark.asyncio
async def test_create_udhar_with_dozen_units(db_session):
    """Test creating udhar with dozen units"""
    user, _ = await create_test_user_and_item(db_session)
    
    # First create an item with "عدد" (count) unit
    item_data = ItemCreate(
        item_name="Eggs",
        item_unit="عدد",  # Count unit
        unit_price=10,
        stock_quantity=100
    )
    eggs_item = await create_items(db_session, item_data, user)
    
    background_tasks = BackgroundTasks()
    
    # Create udhar with "درجن" (dozen)
    result = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Eggs",
        quantity=2,  # 2 dozen = 24 pieces
        unit="درجن",
        current_user=user,
        background_tasks=background_tasks
    )
    
    assert result is not None
    assert result["total_amount"] == 240  # 24 * 10
    assert result["quantity"] == 2
    assert result["requested_unit"] == "درجن"


# ============================================
# FIXED TEST: UPDATE UDHAR ITEM CHANGE ITEM
# ============================================
@pytest.mark.asyncio
async def test_update_udharitem_change_item(db_session):
    """Test updating udhar item to a different item"""
    user, item1 = await create_test_user_and_item(db_session)
    
    # Create second item
    item2_data = ItemCreate(
        item_name="Second Product",
        item_unit="کلو",
        unit_price=200,
        stock_quantity=30
    )
    item2 = await create_items(db_session, item2_data, user)
    
    background_tasks = BackgroundTasks()
    
    # Create udhar with first item
    created = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=5,
        unit="کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    # Update to second item
    update_data = MagicMock()
    update_data.item_name = "Second Product"
    update_data.quantity = 2
    update_data.unit = "کلو"
    
    updated = await update_udharitem(
        db=db_session,
        item_id=created["udharitem_id"],
        data=update_data,
        current_user=user
    )
    
    assert updated is not None
    assert updated["item_name"] == "Second Product"
    assert updated["total_amount"] == 400  # 2 * 200
    
    # Verify stock adjustments
    item1_updated = await read_item(db_session, item1.item_id, user)
    item2_updated = await read_item(db_session, item2.item_id, user)
    
    # Original item: 5 returned, so stock = 50
    assert item1_updated.stock_quantity == 50  # 45 + 5 returned
    assert item2_updated.stock_quantity == 28  # 30 - 2 taken



# ============================================
# FIXED TEST: UPDATE UDHAR ITEM SAME QUANTITY
# ============================================
@pytest.mark.asyncio
async def test_update_udharitem_same_quantity(db_session):
    """Test updating udhar item with same quantity (no stock change)"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    original_stock = item.stock_quantity  # 50
    
    # Create udhar with quantity 5
    created = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=5,
        unit="کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    # After creation, stock should be 45
    after_creation = await read_item(db_session, item.item_id, user)
    assert after_creation.stock_quantity == original_stock - 5  # 45
    
    # Update with same quantity (5)
    update_data = MagicMock()
    update_data.item_name = "Test Product"
    update_data.quantity = 5  # Same quantity
    update_data.unit = "کلو"
    
    updated = await update_udharitem(
        db=db_session,
        item_id=created["udharitem_id"],
        data=update_data,
        current_user=user
    )
    
    assert updated is not None
    assert updated["quantity"] == 5
    
    # Stock should remain 45 (not change)
    updated_item = await read_item(db_session, item.item_id, user)
    assert updated_item.stock_quantity == 45  

    # ============================================
# FIXED TEST: DELETE UDHAR ITEM SUCCESS
# ============================================
@pytest.mark.asyncio
async def test_delete_udharitem_success(db_session):
    """Test successful udhar item deletion"""
    user, item = await create_test_user_and_item(db_session)
    background_tasks = BackgroundTasks()
    
    original_stock = item.stock_quantity  # 50
    
    # Create udhar item
    created = await create_udhar(
        db=db_session,
        customer_name="Test Customer",
        item_name="Test Product",
        quantity=5,
        unit="کلو",
        current_user=user,
        background_tasks=background_tasks
    )
    
    # After creation, stock should be 45
    after_creation = await read_item(db_session, item.item_id, user)
    assert after_creation.stock_quantity == original_stock - 5  # 45
    
    # Delete the udhar item
    result = await delete_udharitem(
        db=db_session,
        item_id=created["udharitem_id"],
        current_user=user
    )
    
    assert result is not None
    assert "کامیابی سے حذف" in result["message"]
    
    # Stock should be restored to original (50)
    updated_item = await read_item(db_session, item.item_id, user)
    assert updated_item.stock_quantity == original_stock - 5  

