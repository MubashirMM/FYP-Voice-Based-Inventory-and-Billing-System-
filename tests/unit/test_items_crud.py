# C:\FYP\Backend\fast-api\tests\unit\test_item_crud.py
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi import HTTPException
from unittest.mock import patch

from myapp.crud.items import (
    create_items,
    read_all,
    read_item,
    search_item,
    update_items,
    delete_item
)
from myapp.schemas.items import ItemCreate, ItemUpdate
from myapp.crud.user import register_user


# # ============================================
# # CREATE ITEM TESTS
# # ============================================

@pytest.mark.asyncio
async def test_create_item_success(db_session):
    """Test successful item creation"""
    # First create a user
    user = await register_user(db_session, "itemuser@example.com", "ItemUser", "pass123")
    
    # Create item
    item_data = ItemCreate(
        item_name="Laptop",
        item_unit="Piece",
        unit_price=50000,
        stock_quantity=10
    )
    
    item = await create_items(db_session, item_data, user)
    
    assert item is not None
    assert item.item_name == "Laptop"
    assert item.item_unit == "Piece"
    assert item.unit_price == 50000
    assert item.stock_quantity == 10
    assert item.user_id == user.user_id


@pytest.mark.asyncio
async def test_create_item_duplicate_name(db_session):
    """Test creating item with duplicate name for same user"""
    user = await register_user(db_session, "itemuser2@example.com", "ItemUser2", "pass123")
    
    # Create first item
    item_data1 = ItemCreate(
        item_name="Mouse",
        item_unit="Piece",
        unit_price=1000,
        stock_quantity=20
    )
    await create_items(db_session, item_data1, user)
    
    # Try to create duplicate item
    item_data2 = ItemCreate(
        item_name="Mouse",  # Same name
        item_unit="Piece",
        unit_price=1500,
        stock_quantity=15
    )
    
    with pytest.raises(HTTPException) as exc:
        await create_items(db_session, item_data2, user)
    
    assert exc.value.status_code == 400
    assert "پہلے سے موجود" in exc.value.detail


@pytest.mark.asyncio
async def test_create_item_case_insensitive_duplicate(db_session):
    """Test that duplicate check is case insensitive"""
    user = await register_user(db_session, "itemuser3@example.com", "ItemUser3", "pass123")
    
    # Create item with uppercase
    item_data1 = ItemCreate(
        item_name="KEYBOARD",
        item_unit="Piece",
        unit_price=2000,
        stock_quantity=5
    )
    await create_items(db_session, item_data1, user)
    
    # Try to create with lowercase (should fail)
    item_data2 = ItemCreate(
        item_name="keyboard",  # Same name different case
        item_unit="Piece",
        unit_price=2500,
        stock_quantity=3
    )
    
    with pytest.raises(HTTPException) as exc:
        await create_items(db_session, item_data2, user)
    
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_item_with_whitespace(db_session):
    """Test creating item with whitespace in name (should be stripped)"""
    user = await register_user(db_session, "itemuser4@example.com", "ItemUser4", "pass123")
    
    item_data = ItemCreate(
        item_name="  Monitor  ",  # With spaces
        item_unit="  Piece  ",     # With spaces
        unit_price=30000,
        stock_quantity=8
    )
    
    item = await create_items(db_session, item_data, user)
    
    assert item.item_name == "Monitor"  # Should be stripped
    assert item.item_unit == "Piece"    # Should be stripped


@pytest.mark.asyncio
async def test_create_item_zero_stock(db_session):
    """Test creating item with zero stock quantity"""
    user = await register_user(db_session, "itemuser5@example.com", "ItemUser5", "pass123")
    
    item_data = ItemCreate(
        item_name="Cable",
        item_unit="Meter",
        unit_price=50,
        stock_quantity=0
    )
    
    item = await create_items(db_session, item_data, user)
    assert item.stock_quantity == 0


# ============================================
# READ ALL ITEMS TESTS
# ============================================
@pytest.mark.asyncio
async def test_read_all_items_empty(db_session):
    """Test reading all items when none exist"""
    user = await register_user(db_session, "readuser1@example.com", "ReadUser1", "pass123")
    
    items = await read_all(db_session, user)
    
    assert isinstance(items, list)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_read_all_items_multiple(db_session):
    """Test reading multiple items"""
    user = await register_user(db_session, "readuser2@example.com", "ReadUser2", "pass123")
    
    # Create multiple items
    items_data = [
        ItemCreate(item_name="Apple", item_unit="KG", unit_price=200, stock_quantity=50),
        ItemCreate(item_name="Banana", item_unit="Dozen", unit_price=120, stock_quantity=30),
        ItemCreate(item_name="Orange", item_unit="KG", unit_price=180, stock_quantity=40),
    ]
    
    for item_data in items_data:
        await create_items(db_session, item_data, user)
    
    items = await read_all(db_session, user)
    
    assert len(items) == 3
    item_names = [item.item_name for item in items]
    assert "Apple" in item_names
    assert "Banana" in item_names
    assert "Orange" in item_names


@pytest.mark.asyncio
async def test_read_all_items_ordered_by_name(db_session):
    """Test that items are returned in alphabetical order"""
    user = await register_user(db_session, "readuser3@example.com", "ReadUser3", "pass123")
    
    # Create items in random order
    items_data = [
        ItemCreate(item_name="Zebra", item_unit="Piece", unit_price=100, stock_quantity=1),
        ItemCreate(item_name="Apple", item_unit="Piece", unit_price=100, stock_quantity=1),
        ItemCreate(item_name="Mango", item_unit="Piece", unit_price=100, stock_quantity=1),
    ]
    
    for item_data in items_data:
        await create_items(db_session, item_data, user)
    
    items = await read_all(db_session, user)
    
    # Should be ordered by name: Apple, Mango, Zebra
    assert items[0].item_name == "Apple"
    assert items[1].item_name == "Mango"
    assert items[2].item_name == "Zebra"


@pytest.mark.asyncio
async def test_read_all_items_user_specific(db_session):
    """Test that users only see their own items"""
    # Create two users
    user1 = await register_user(db_session, "user1@example.com", "User1", "pass123")
    user2 = await register_user(db_session, "user2@example.com", "User2", "pass123")
    
    # Create items for user1
    item1 = ItemCreate(item_name="User1Item", item_unit="Piece", unit_price=100, stock_quantity=1)
    await create_items(db_session, item1, user1)
    
    # Create items for user2
    item2 = ItemCreate(item_name="User2Item", item_unit="Piece", unit_price=200, stock_quantity=2)
    await create_items(db_session, item2, user2)
    
    # User1 should only see their item
    user1_items = await read_all(db_session, user1)
    assert len(user1_items) == 1
    assert user1_items[0].item_name == "User1Item"
    
    # User2 should only see their item
    user2_items = await read_all(db_session, user2)
    assert len(user2_items) == 1
    assert user2_items[0].item_name == "User2Item"


# ============================================
# READ ONE ITEM TESTS
# ============================================
@pytest.mark.asyncio
async def test_read_item_success(db_session):
    """Test reading a single item successfully"""
    user = await register_user(db_session, "readone@example.com", "ReadOne", "pass123")
    
    item_data = ItemCreate(
        item_name="Test Item",
        item_unit="Piece",
        unit_price=500,
        stock_quantity=10
    )
    created_item = await create_items(db_session, item_data, user)
    
    fetched_item = await read_item(db_session, created_item.item_id, user)
    
    assert fetched_item is not None
    assert fetched_item.item_id == created_item.item_id
    assert fetched_item.item_name == "Test Item"


@pytest.mark.asyncio
async def test_read_item_not_found(db_session):
    """Test reading non-existent item"""
    user = await register_user(db_session, "readnotfound@example.com", "ReadNotFound", "pass123")
    
    with pytest.raises(HTTPException) as exc:
        await read_item(db_session, 99999, user)
    
    assert exc.value.status_code == 404
    assert "موجود نہیں" in exc.value.detail


@pytest.mark.asyncio
async def test_read_item_other_user_item(db_session):
    """Test that user cannot read another user's item"""
    user1 = await register_user(db_session, "userA@example.com", "UserA", "pass123")
    user2 = await register_user(db_session, "userB@example.com", "UserB", "pass123")
    
    # User1 creates an item
    item_data = ItemCreate(
        item_name="UserA Item",
        item_unit="Piece",
        unit_price=1000,
        stock_quantity=5
    )
    user1_item = await create_items(db_session, item_data, user1)
    
    # User2 tries to read User1's item (should fail)
    with pytest.raises(HTTPException) as exc:
        await read_item(db_session, user1_item.item_id, user2)
    
    assert exc.value.status_code == 404


# ============================================
# SEARCH ITEMS TESTS
# ============================================
@pytest.mark.asyncio
async def test_search_item_success(db_session):
    """Test searching items by keyword"""
    user = await register_user(db_session, "search@example.com", "SearchUser", "pass123")
    
    # Create items
    items_data = [
        ItemCreate(item_name="Dell Laptop", item_unit="Piece", unit_price=50000, stock_quantity=5),
        ItemCreate(item_name="HP Laptop", item_unit="Piece", unit_price=45000, stock_quantity=3),
        ItemCreate(item_name="Apple Mouse", item_unit="Piece", unit_price=2000, stock_quantity=10),
    ]
    
    for item_data in items_data:
        await create_items(db_session, item_data, user)
    
    # Search for "Laptop"
    results = await search_item(db_session, "Laptop", user)
    
    assert len(results) == 2
    item_names = [item.item_name for item in results]
    assert "Dell Laptop" in item_names
    assert "HP Laptop" in item_names
    assert "Apple Mouse" not in item_names


@pytest.mark.asyncio
async def test_search_item_case_insensitive(db_session):
    """Test that search is case insensitive"""
    user = await register_user(db_session, "searchcase@example.com", "SearchCase", "pass123")
    
    item_data = ItemCreate(
        item_name="SAMSUNG TV",
        item_unit="Piece",
        unit_price=60000,
        stock_quantity=2
    )
    await create_items(db_session, item_data, user)
    
    # Search with lowercase
    results = await search_item(db_session, "samsung", user)
    assert len(results) == 1
    assert results[0].item_name == "SAMSUNG TV"


@pytest.mark.asyncio
async def test_search_item_no_results(db_session):
    """Test search with no matching items"""
    user = await register_user(db_session, "searchno@example.com", "SearchNo", "pass123")
    
    item_data = ItemCreate(
        item_name="Keyboard",
        item_unit="Piece",
        unit_price=1000,
        stock_quantity=5
    )
    await create_items(db_session, item_data, user)
    
    with pytest.raises(HTTPException) as exc:
        await search_item(db_session, "NonExistent", user)
    
    assert exc.value.status_code == 404
    assert "کوئی آئٹم نہیں ملا" in exc.value.detail


@pytest.mark.asyncio
async def test_search_item_empty_keyword(db_session):
    """Test search with empty keyword"""
    user = await register_user(db_session, "searchempty@example.com", "SearchEmpty", "pass123")
    
    with pytest.raises(HTTPException) as exc:
        await search_item(db_session, "", user)
    
    assert exc.value.status_code == 400
    assert "کم از کم ایک لفظ درکار ہے" in exc.value.detail


@pytest.mark.asyncio
async def test_search_item_whitespace_only(db_session):
    """Test search with only whitespace"""
    user = await register_user(db_session, "searchspace@example.com", "SearchSpace", "pass123")
    
    with pytest.raises(HTTPException) as exc:
        await search_item(db_session, "   ", user)
    
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_search_item_partial_match(db_session):
    """Test search with partial keyword"""
    user = await register_user(db_session, "searchpartial@example.com", "SearchPartial", "pass123")
    
    item_data = ItemCreate(
        item_name="Wireless Bluetooth Headphones",
        item_unit="Piece",
        unit_price=3000,
        stock_quantity=8
    )
    await create_items(db_session, item_data, user)
    
    # Search for partial word
    results = await search_item(db_session, "Bluetooth", user)
    assert len(results) == 1
    
    results = await search_item(db_session, "Head", user)
    assert len(results) == 1
    
    results = await search_item(db_session, "less", user)
    assert len(results) == 1


# ============================================
# UPDATE ITEM TESTS
# ============================================
@pytest.mark.asyncio
async def test_update_item_name_success(db_session):
    """Test updating item name"""
    user = await register_user(db_session, "update@example.com", "UpdateUser", "pass123")
    
    # Create item
    item_data = ItemCreate(
        item_name="Old Name",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=10
    )
    item = await create_items(db_session, item_data, user)
    
    # Update name
    update_data = ItemUpdate(item_name="New Name")
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    
    assert updated_item.item_name == "New Name"
    assert updated_item.item_unit == "Piece"  # Unchanged
    assert updated_item.unit_price == 100     # Unchanged
    assert updated_item.stock_quantity == 10  # Unchanged


@pytest.mark.asyncio
async def test_update_item_unit_success(db_session):
    """Test updating item unit"""
    user = await register_user(db_session, "updateunit@example.com", "UpdateUnit", "pass123")
    
    item_data = ItemCreate(
        item_name="Sugar",
        item_unit="KG",
        unit_price=80,
        stock_quantity=20
    )
    item = await create_items(db_session, item_data, user)
    
    # Update unit
    update_data = ItemUpdate(item_unit="Gram")
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    
    assert updated_item.item_unit == "Gram"
    assert updated_item.item_name == "Sugar"


@pytest.mark.asyncio
async def test_update_item_price_success(db_session):
    """Test updating item price"""
    user = await register_user(db_session, "updateprice@example.com", "UpdatePrice", "pass123")
    
    item_data = ItemCreate(
        item_name="Rice",
        item_unit="KG",
        unit_price=120,
        stock_quantity=15
    )
    item = await create_items(db_session, item_data, user)
    
    # Update price
    update_data = ItemUpdate(unit_price=150)
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    
    assert updated_item.unit_price == 150
    assert updated_item.item_name == "Rice"


@pytest.mark.asyncio
async def test_update_item_stock_success(db_session):
    """Test updating stock quantity"""
    user = await register_user(db_session, "updatestock@example.com", "UpdateStock", "pass123")
    
    item_data = ItemCreate(
        item_name="Oil",
        item_unit="Liter",
        unit_price=200,
        stock_quantity=10
    )
    item = await create_items(db_session, item_data, user)
    
    # Update stock
    update_data = ItemUpdate(stock_quantity=25)
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    
    assert updated_item.stock_quantity == 25


@pytest.mark.asyncio
async def test_update_item_multiple_fields(db_session):
    """Test updating multiple fields at once"""
    user = await register_user(db_session, "updatemulti@example.com", "UpdateMulti", "pass123")
    
    item_data = ItemCreate(
        item_name="Old Product",
        item_unit="Box",
        unit_price=500,
        stock_quantity=8
    )
    item = await create_items(db_session, item_data, user)
    
    # Update multiple fields
    update_data = ItemUpdate(
        item_name="New Product",
        item_unit="Pack",
        unit_price=600,
        stock_quantity=12
    )
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    
    assert updated_item.item_name == "New Product"
    assert updated_item.item_unit == "Pack"
    assert updated_item.unit_price == 600
    assert updated_item.stock_quantity == 12


@pytest.mark.asyncio
async def test_update_item_duplicate_name(db_session):
    """Test updating item name to an existing name"""
    user = await register_user(db_session, "updatedup@example.com", "UpdateDup", "pass123")
    
    # Create two items
    item1_data = ItemCreate(
        item_name="Item One",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    item1 = await create_items(db_session, item1_data, user)
    
    item2_data = ItemCreate(
        item_name="Item Two",
        item_unit="Piece",
        unit_price=200,
        stock_quantity=3
    )
    item2 = await create_items(db_session, item2_data, user)
    
    # Try to rename item2 to item1's name (should fail)
    update_data = ItemUpdate(item_name="Item One")
    
    with pytest.raises(HTTPException) as exc:
        await update_items(db_session, item2.item_id, update_data, user)
    
    assert exc.value.status_code == 400
    assert "پہلے سے موجود" in exc.value.detail



@pytest.mark.asyncio
async def test_update_item_not_found(db_session):
    """Test updating non-existent item"""
    user = await register_user(db_session, "updatenotfound@example.com", "UpdateNotFound", "pass123")
    
    update_data = ItemUpdate(item_name="New Name")
    
    with pytest.raises(HTTPException) as exc:
        await update_items(db_session, 99999, update_data, user)
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_item_other_user_item(db_session):
    """Test that user cannot update another user's item"""
    user1 = await register_user(db_session, "userX@example.com", "UserX", "pass123")
    user2 = await register_user(db_session, "userY@example.com", "UserY", "pass123")
    
    # User1 creates item
    item_data = ItemCreate(
        item_name="UserX Item",
        item_unit="Piece",
        unit_price=500,
        stock_quantity=3
    )
    user1_item = await create_items(db_session, item_data, user1)
    
    # User2 tries to update User1's item (should fail)
    update_data = ItemUpdate(item_name="Hacked")
    
    with pytest.raises(HTTPException) as exc:
        await update_items(db_session, user1_item.item_id, update_data, user2)
    
    assert exc.value.status_code == 404


# ============================================
# DELETE ITEM TESTS
# ============================================
@pytest.mark.asyncio
async def test_delete_item_success(db_session):
    """Test successful item deletion"""
    user = await register_user(db_session, "delete@example.com", "DeleteUser", "pass123")
    
    item_data = ItemCreate(
        item_name="To Delete",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    item = await create_items(db_session, item_data, user)
    
    # Delete the item
    result = await delete_item(db_session, item.item_id, user)
    assert result is True
    
    # Verify item no longer exists
    with pytest.raises(HTTPException) as exc:
        await read_item(db_session, item.item_id, user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_not_found(db_session):
    """Test deleting non-existent item"""
    user = await register_user(db_session, "deletenotfound@example.com", "DeleteNotFound", "pass123")
    
    with pytest.raises(HTTPException) as exc:
        await delete_item(db_session, 99999, user)
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_other_user_item(db_session):
    """Test that user cannot delete another user's item"""
    user1 = await register_user(db_session, "userDelete1@example.com", "UserDelete1", "pass123")
    user2 = await register_user(db_session, "userDelete2@example.com", "UserDelete2", "pass123")
    
    # User1 creates item
    item_data = ItemCreate(
        item_name="User1 Item",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    user1_item = await create_items(db_session, item_data, user1)
    
    # User2 tries to delete User1's item (should fail)
    with pytest.raises(HTTPException) as exc:
        await delete_item(db_session, user1_item.item_id, user2)
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_item_same_name_different_users(db_session):
    """Test that different users can have items with same name"""
    user1 = await register_user(db_session, "user_diff1@example.com", "UserDiff1", "pass123")
    user2 = await register_user(db_session, "user_diff2@example.com", "UserDiff2", "pass123")
    
    # Both users create item with same name
    item_data = ItemCreate(
        item_name="Common Name",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    
    item1 = await create_items(db_session, item_data, user1)
    item2 = await create_items(db_session, item_data, user2)
    
    assert item1.item_name == "Common Name"
    assert item2.item_name == "Common Name"
    assert item1.user_id != item2.user_id


@pytest.mark.asyncio
async def test_update_item_no_changes(db_session):
    """Test updating item with same values (should work)"""
    user = await register_user(db_session, "nochange@example.com", "NoChange", "pass123")
    
    item_data = ItemCreate(
        item_name="Same Name",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    item = await create_items(db_session, item_data, user)
    
    # Update with same values
    update_data = ItemUpdate(
        item_name="Same Name",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    
    assert updated_item.item_name == "Same Name"
    assert updated_item.item_unit == "Piece"
    assert updated_item.unit_price == 100
    assert updated_item.stock_quantity == 5


@pytest.mark.asyncio
async def test_search_item_special_characters(db_session):
    """Test searching with special characters"""
    user = await register_user(db_session, "searchspecial@example.com", "SearchSpecial", "pass123")
    
    item_data = ItemCreate(
        item_name="C++ Programmer",
        item_unit="Piece",
        unit_price=5000,
        stock_quantity=2
    )
    await create_items(db_session, item_data, user)
    
    results = await search_item(db_session, "C++", user)
    assert len(results) == 1


# ============================================
# FIXED TEST CASE 1
# ============================================
@pytest.mark.asyncio
async def test_create_item_negative_stock(db_session):
    """Test creating item with negative stock - should raise validation error"""
    from pydantic import ValidationError
    
    user = await register_user(db_session, "itemuser6@example.com", "ItemUser6", "pass123")
    
    with pytest.raises(ValidationError) as exc_info:
        ItemCreate(
            item_name="Test",
            item_unit="Piece",
            unit_price=100,
            stock_quantity=-5
        )
    assert "اسٹاک منفی نہیں ہو سکتا" in str(exc_info.value)


# ============================================
# FIXED TEST CASE 2
# ============================================
@pytest.mark.asyncio
async def test_update_item_negative_price(db_session):
    """Test updating with negative price - should raise validation error"""
    from pydantic import ValidationError
    
    user = await register_user(db_session, "updateneg@example.com", "UpdateNeg", "pass123")
    
    item_data = ItemCreate(
        item_name="Test",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    await create_items(db_session, item_data, user)
    
    with pytest.raises(ValidationError) as exc_info:
        ItemUpdate(unit_price=-50)
    assert "قیمت مثبت ہونی چاہیے" in str(exc_info.value)


# ============================================
# FIXED TEST CASE 3
# ============================================
@pytest.mark.asyncio
async def test_update_item_negative_stock(db_session):
    """Test updating with negative stock - should raise validation error"""
    from pydantic import ValidationError
    
    user = await register_user(db_session, "updatenegstock@example.com", "UpdateNegStock", "pass123")
    
    item_data = ItemCreate(
        item_name="Test",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=5
    )
    await create_items(db_session, item_data, user)
    
    with pytest.raises(ValidationError) as exc_info:
        ItemUpdate(stock_quantity=-10)
    assert "اسٹاک منفی نہیں ہو سکتا" in str(exc_info.value)


# ============================================
# FIXED TEST CASE 4
# ============================================
@pytest.mark.asyncio
async def test_delete_multiple_items_sequential(db_session):
    """Test deleting multiple items one after another"""
    user = await register_user(db_session, "deletemulti@example.com", "DeleteMulti", "pass123")
    
    items = []
    for i in range(3):
        item_data = ItemCreate(
            item_name=f"Item {i}",
            item_unit="Piece",
            unit_price=100 * (i + 1),  # Positive prices: 100, 200, 300
            stock_quantity=i + 1  # Positive stock: 1, 2, 3
        )
        item = await create_items(db_session, item_data, user)
        items.append(item)
    
    for item in items:
        result = await delete_item(db_session, item.item_id, user)
        assert result is True
    
    remaining_items = await read_all(db_session, user)
    assert len(remaining_items) == 0


# ============================================
# FIXED TEST CASE 5 (split into 2 tests)
# ============================================
@pytest.mark.asyncio
async def test_create_item_max_length_name(db_session):
    """Test creating item with maximum allowed name length (50 chars)"""
    user = await register_user(db_session, "longname@example.com", "LongName", "pass123")
    
    long_name = "A" * 50
    item_data = ItemCreate(
        item_name=long_name,
        item_unit="Piece",
        unit_price=100,
        stock_quantity=1
    )
    
    item = await create_items(db_session, item_data, user)
    assert item.item_name == long_name
    assert len(item.item_name) == 50


@pytest.mark.asyncio
async def test_create_item_exceeds_name_limit(db_session):
    """Test creating item with name exceeding 50 chars - should fail"""
    user = await register_user(db_session, "longname2@example.com", "LongName2", "pass123")
    
    long_name = "A" * 51
    item_data = ItemCreate(
        item_name=long_name,
        item_unit="Piece",
        unit_price=100,
        stock_quantity=1
    )
    
    with pytest.raises(Exception) as exc_info:
        await create_items(db_session, item_data, user)
    assert "value too long" in str(exc_info.value).lower()

#     ============================================
# EDGE CASES & ADDITIONAL TESTS
# ============================================


@pytest.mark.asyncio
async def test_create_item_max_length_name(db_session):
    """Test creating item with exactly 50 characters (maximum allowed)"""
    user = await register_user(db_session, "maxlength@example.com", "MaxLength", "pass123")
    
    # Create a name with exactly 50 characters
    max_length_name = "A" * 50
    item_data = ItemCreate(
        item_name=max_length_name,
        item_unit="Piece",
        unit_price=100,
        stock_quantity=1
    )
    
    item = await create_items(db_session, item_data, user)
    assert item.item_name == max_length_name
    assert len(item.item_name) == 50


@pytest.mark.asyncio
async def test_create_item_boundary_49_characters(db_session):
    """Test creating item with 49 characters (should work)"""
    user = await register_user(db_session, "boundary@example.com", "Boundary", "pass123")
    
    # Create a name with 49 characters
    name_49 = "A" * 49
    item_data = ItemCreate(
        item_name=name_49,
        item_unit="Piece",
        unit_price=100,
        stock_quantity=1
    )
    
    item = await create_items(db_session, item_data, user)
    assert item.item_name == name_49
    assert len(item.item_name) == 49



@pytest.mark.asyncio
async def test_update_item_to_max_length_name(db_session):
    """Test updating item to exactly 50 characters (maximum allowed)"""
    user = await register_user(db_session, "updatemax@example.com", "UpdateMax", "pass123")
    
    # Create initial item
    item_data = ItemCreate(
        item_name="Original Item",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=1
    )
    item = await create_items(db_session, item_data, user)
    
    # Update with exactly 50 characters
    max_length_name = "C" * 50
    update_data = ItemUpdate(item_name=max_length_name)
    
    updated_item = await update_items(db_session, item.item_id, update_data, user)
    assert updated_item.item_name == max_length_name
    assert len(updated_item.item_name) == 50



@pytest.mark.asyncio
async def test_pydantic_validation_rejects_long_name(db_session):
    """Test that Pydantic schema rejects long names before reaching database"""
    long_name = "A" * 51
    
    # This should fail at Pydantic level
    with pytest.raises(ValueError) as exc_info:
        ItemCreate(
            item_name=long_name,
            item_unit="Piece",
            unit_price=100,
            stock_quantity=1
        )
    
    assert "50 حروف" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_item_very_long_name(db_session):
    """Test creating item with very long name - SHOULD FAIL AT SCHEMA LEVEL"""
    from pydantic import ValidationError
    from myapp.crud.user import register_user
    
    user = await register_user(db_session, "longname@example.com", "LongName", "pass123")
    long_name = "A" * 51  # 51 characters
    
    # We must wrap the creation of ItemCreate because that is where it fails
    with pytest.raises(ValidationError) as exc_info:
        item_data = ItemCreate(
            item_name=long_name,
            item_unit="Piece",
            unit_price=100,
            stock_quantity=1
        )
    
    # Pydantic errors are stored in a specific way, so we check the string representation
    assert "50 حروف" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_item_to_very_long_name(db_session):
    """Test updating item to very long name - SHOULD FAIL"""
    user = await register_user(db_session, "updatelong@example.com", "UpdateLong", "pass123")
    
    # Create initial item
    item_data = ItemCreate(
        item_name="Original Item",
        item_unit="Piece",
        unit_price=100,
        stock_quantity=1
    )
    item = await create_items(db_session, item_data, user)
    
    # Try to update with 51-character name
    long_name = "B" * 51
    
    # This should FAIL validation
    with pytest.raises(ValueError) as exc_info:
        update_data = ItemUpdate(item_name=long_name)  # Fails here
        await update_items(db_session, item.item_id, update_data, user)
    
    assert "50 حروف" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_item_with_very_long_unit(db_session):
    """Test creating item with very long unit - SHOULD FAIL"""
    user = await register_user(db_session, "longunit@example.com", "LongUnit", "pass123")
    
    long_unit = "U" * 51
    
    # This should FAIL validation
    with pytest.raises(ValueError) as exc_info:
        item_data = ItemCreate(
            item_name="Test Item",
            item_unit=long_unit,
            unit_price=100,
            stock_quantity=1
        )
    
    assert "50 حروف" in str(exc_info.value)