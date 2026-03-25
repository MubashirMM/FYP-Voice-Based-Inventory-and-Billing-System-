import pytest
from fastapi import HTTPException
from myapp.models.user import User
from myapp.schemas.shop import ShopCreate
from myapp.crud.shop import (
    create_shop,
    get_all_shops,
    get_shop,
    update_shop,
    delete_shop,
)

# ---------------------------
# Create Shop
# ---------------------------
@pytest.mark.asyncio
async def test_create_shop_success(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    shop_data = ShopCreate(shop_name="My Shop", address="123 Street")
    new_shop = await create_shop(db_session, shop_data, current_user)

    assert new_shop.shop_id is not None
    assert new_shop.shop_name == "My Shop"
    assert new_shop.user_id == current_user.user_id


@pytest.mark.asyncio
async def test_create_shop_duplicate_name(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    shop_data = ShopCreate(shop_name="Duplicate Shop", address="Addr")
    await create_shop(db_session, shop_data, current_user)

    with pytest.raises(HTTPException) as exc:
        await create_shop(db_session, shop_data, current_user)

    assert exc.value.status_code == 400
    assert "یہ دکان پہلے سے موجود ہے" in exc.value.detail

# ---------------------------
# Get Shops
# ---------------------------
@pytest.mark.asyncio
async def test_get_all_shops(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    await create_shop(db_session, ShopCreate(shop_name="Shop1", address="Addr1"), current_user)
    await create_shop(db_session, ShopCreate(shop_name="Shop2", address="Addr2"), current_user)

    shops = await get_all_shops(db_session, current_user)
    assert len(shops) == 2
    assert {s.shop_name for s in shops} == {"Shop1", "Shop2"}


@pytest.mark.asyncio
async def test_get_shop_success(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    new_shop = await create_shop(db_session, ShopCreate(shop_name="Target", address="Addr"), current_user)
    shop = await get_shop(db_session, new_shop.shop_id, current_user)
    assert shop.shop_name == "Target"


@pytest.mark.asyncio
async def test_get_shop_not_found(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    with pytest.raises(HTTPException) as exc:
        await get_shop(db_session, 999, current_user)

    assert exc.value.status_code == 404
    assert "دکان نہیں ملی" in exc.value.detail

# ---------------------------
# Update Shop
# ---------------------------
@pytest.mark.asyncio
async def test_update_shop_success(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    new_shop = await create_shop(db_session, ShopCreate(shop_name="Old", address="Addr"), current_user)
    updated = await update_shop(db_session, new_shop.shop_id, {"shop_name": "New"}, current_user)
    assert updated.shop_name == "New"

# ---------------------------
# Delete Shop
# ---------------------------
@pytest.mark.asyncio
async def test_delete_shop_success(db_session):
    current_user = User(user_id=1, username="Ali")
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)

    new_shop = await create_shop(db_session, ShopCreate(shop_name="DeleteMe", address="Addr"), current_user)
    result = await delete_shop(db_session, new_shop.shop_id, current_user)
    assert result is True

    with pytest.raises(HTTPException) as exc:
        await get_shop(db_session, new_shop.shop_id, current_user)
    assert exc.value.status_code == 404
    assert "دکان نہیں ملی" in exc.value.detail
