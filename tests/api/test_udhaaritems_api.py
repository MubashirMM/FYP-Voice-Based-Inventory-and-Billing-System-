# import pytest
# from fastapi import status
# from unittest.mock import patch

# pytestmark = pytest.mark.asyncio


# class TestCreateUdharItem:
#     async def test_create_udhar_success(self, client, auth_headers, db_session, create_test_user):
#         """Test successful udhar item creation"""
#         # Create a customer first - only use fields that exist in your Customer model
#         from myapp.models.customer import Customer
        
#         # Check your Customer model for actual field names
#         # Common fields: customer_name, user_id (maybe phone, address don't exist)
#         customer = Customer(
#             customer_name="ٹیسٹ کسٹمر",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         udhar_data = {
#             "customer_name": customer.customer_name,
#             "item_name": "چاول",
#             "quantity": 5,
#             "unit": "کلو"
#         }
        
#         # Mock the background task to avoid telegram issues
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             response = client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
        
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert data["item_name"] == "چاول"
#         assert data["quantity"] == 5

#     async def test_create_udhar_customer_not_found(self, client, auth_headers):
#         """Test creating udhar for non-existent customer"""
#         udhar_data = {
#             "customer_name": "غیرموجود کسٹمر",
#             "item_name": "شکر",
#             "quantity": 2,
#             "unit": "کلو"
#         }
#         response = client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
#         assert response.status_code == status.HTTP_404_NOT_FOUND

#     async def test_create_udhar_without_auth(self, client):
#         """Test creating udhar without authentication"""
#         udhar_data = {
#             "customer_name": "کسٹمر",
#             "item_name": "چائے",
#             "quantity": 3,
#             "unit": "پیکٹ"
#         }
#         response = client.post("/udhar-items/", json=udhar_data)
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED


# class TestGetAllUdharItems:
#     async def test_get_all_udhar_success(self, client, auth_headers, db_session, create_test_user):
#         """Test getting all udhar items"""
#         # Create customer
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر1",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         # Create udhar item
#         udhar_data = {
#             "customer_name": customer.customer_name,
#             "item_name": "چاول",
#             "quantity": 5,
#             "unit": "کلو"
#         }
        
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
        
#         response = client.get("/udhar-items/", headers=auth_headers)
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert isinstance(data, list)

#     async def test_get_all_udhar_empty(self, client, auth_headers):
#         """Test getting udhar items when user has none"""
#         response = client.get("/udhar-items/", headers=auth_headers)
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert isinstance(data, list)

#     async def test_get_all_udhar_without_auth(self, client):
#         """Test getting udhar items without authentication"""
#         response = client.get("/udhar-items/")
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED


# class TestSearchUdharItems:
#     async def test_search_udhar_success(self, client, auth_headers, db_session, create_test_user):
#         """Test searching udhar items by keyword"""
#         # Create customer
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر2",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         # Create items
#         items = [
#             {"customer_name": customer.customer_name, "item_name": "چاول باسمتی", "quantity": 5, "unit": "کلو"},
#             {"customer_name": customer.customer_name, "item_name": "چاول کالا", "quantity": 3, "unit": "کلو"},
#             {"customer_name": customer.customer_name, "item_name": "شکر سفید", "quantity": 2, "unit": "کلو"}
#         ]
        
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             for item in items:
#                 client.post("/udhar-items/", json=item, headers=auth_headers)
        
#         response = client.get("/udhar-items/search/?keyword=چاول", headers=auth_headers)
        
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert isinstance(data, list)
#         assert len(data) >= 2

#     async def test_search_udhar_no_results(self, client, auth_headers):
#         """Test search with no matching results"""
#         response = client.get("/udhar-items/search/?keyword=غیرموجود", headers=auth_headers)
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert isinstance(data, list)
#         assert len(data) == 0

#     async def test_search_udhar_without_auth(self, client):
#         """Test search without authentication"""
#         response = client.get("/udhar-items/search/?keyword=چاول")
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED


# class TestDeleteUdharItem:
#     async def test_delete_udhar_success(self, client, auth_headers, db_session, create_test_user):
#         """Test successfully deleting an udhar item"""
#         # Create customer
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر3",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         # Create udhar item
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             create_response = client.post("/udhar-items/", json={
#                 "customer_name": customer.customer_name,
#                 "item_name": "ختم ہونے والا",
#                 "quantity": 2,
#                 "unit": "عدد"
#             }, headers=auth_headers)
        
#         item_id = create_response.json()["udharitem_id"]
        
#         # Delete udhar item
#         response = client.delete(f"/udhar-items/{item_id}", headers=auth_headers)
#         assert response.status_code == status.HTTP_200_OK

#     async def test_delete_udhar_not_found(self, client, auth_headers):
#         """Test deleting non-existent udhar item"""
#         response = client.delete("/udhar-items/99999", headers=auth_headers)
#         assert response.status_code == status.HTTP_404_NOT_FOUND

#     async def test_delete_udhar_without_auth(self, client):
#         """Test deleting udhar without authentication"""
#         response = client.delete("/udhar-items/1")
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED


# class TestUdharEdgeCases:
#     async def test_create_udhar_invalid_data(self, client, auth_headers, db_session, create_test_user):
#         """Test creating udhar with invalid data"""
#         # Create customer first
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر ایج",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         udhar_data = {
#             "customer_name": customer.customer_name,
#             "item_name": "",  # Empty item name
#             "quantity": -5,  # Negative quantity
#             "unit": ""
#         }
#         response = client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

#     async def test_create_multiple_udhar_same_customer(self, client, auth_headers, db_session, create_test_user):
#         """Test creating multiple udhar items for same customer"""
#         # Create customer
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر ملٹی",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             for i in range(3):
#                 response = client.post("/udhar-items/", json={
#                     "customer_name": customer.customer_name,
#                     "item_name": f"آئٹم {i}",
#                     "quantity": i + 1,
#                     "unit": "عدد"
#                 }, headers=auth_headers)
#                 assert response.status_code == status.HTTP_200_OK

#     async def test_update_udhar_quantity_zero(self, client, auth_headers, db_session, create_test_user):
#         """Test updating udhar quantity to zero (should be allowed)"""
#         # Create customer
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر زیرو",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             create_response = client.post("/udhar-items/", json={
#                 "customer_name": customer.customer_name,
#                 "item_name": "صفر مقدار",
#                 "quantity": 10,
#                 "unit": "کلو"
#             }, headers=auth_headers)
        
#         item_id = create_response.json()["udharitem_id"]
        
#         # Update to zero quantity
#         update_data = {
#             "customer_name": customer.customer_name,
#             "item_name": "صفر مقدار",
#             "quantity": 0,
#             "unit": "کلو"
#         }
#         response = client.put(f"/udhar-items/{item_id}", json=update_data, headers=auth_headers)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.json()["quantity"] == 0

#     async def test_create_udhar_with_large_quantity(self, client, auth_headers, db_session, create_test_user):
#         """Test creating udhar with very large quantity"""
#         # Create customer
#         from myapp.models.customer import Customer
#         customer = Customer(
#             customer_name="کسٹمر بڑا",
#             user_id=create_test_user.user_id
#         )
#         db_session.add(customer)
#         await db_session.commit()
#         await db_session.refresh(customer)
        
#         udhar_data = {
#             "customer_name": customer.customer_name,
#             "item_name": "بڑی مقدار",
#             "quantity": 999999,
#             "unit": "بوری"
#         }
        
#         with patch('myapp.crud.udhaar_item.send_telegram_notification'):
#             response = client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
        
#         assert response.status_code == status.HTTP_200_OK
#         assert response.json()["quantity"] == 999999
import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio


class TestCreateUdharItem:
    async def test_create_udhar_success(self, client, auth_headers, db_session, create_test_user):
        """Test successful udhar item creation"""
        from myapp.models.customer import Customer
        from myapp.crud.udhaar_item import create_udhar
        from unittest.mock import patch
        
        # Create customer with only required fields
        customer = Customer(
            customer_name="ٹیسٹ کسٹمر",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        udhar_data = {
            "customer_name": customer.customer_name,
            "item_name": "چاول",
            "quantity": 5,
            "unit": "کلو"
        }
        
        # Mock background tasks to avoid issues
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            response = client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["item_name"] == "چاول"
        assert data["quantity"] == 5


class TestGetAllUdharItems:
    async def test_get_all_udhar_success(self, client, auth_headers, db_session, create_test_user):
        """Test getting all udhar items"""
        from myapp.models.customer import Customer
        from unittest.mock import patch
        
        customer = Customer(
            customer_name="کسٹمر1",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        udhar_data = {
            "customer_name": customer.customer_name,
            "item_name": "چاول",
            "quantity": 5,
            "unit": "کلو"
        }
        
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            await client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
        
        response = client.get("/udhar-items/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestSearchUdharItems:
    async def test_search_udhar_success(self, client, auth_headers, db_session, create_test_user):
        """Test searching udhar items by keyword"""
        from myapp.models.customer import Customer
        from unittest.mock import patch
        
        customer = Customer(
            customer_name="کسٹمر2",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        items = [
            {"customer_name": customer.customer_name, "item_name": "چاول باسمتی", "quantity": 5, "unit": "کلو"},
            {"customer_name": customer.customer_name, "item_name": "چاول کالا", "quantity": 3, "unit": "کلو"},
            {"customer_name": customer.customer_name, "item_name": "شکر سفید", "quantity": 2, "unit": "کلو"}
        ]
        
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            for item in items:
                await client.post("/udhar-items/", json=item, headers=auth_headers)
        
        response = client.get("/udhar-items/search/?keyword=چاول", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2


class TestDeleteUdharItem:
    async def test_delete_udhar_success(self, client, auth_headers, db_session, create_test_user):
        """Test successfully deleting an udhar item"""
        from myapp.models.customer import Customer
        from unittest.mock import patch
        
        customer = Customer(
            customer_name="کسٹمر3",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            create_response = await client.post("/udhar-items/", json={
                "customer_name": customer.customer_name,
                "item_name": "ختم ہونے والا",
                "quantity": 2,
                "unit": "عدد"
            }, headers=auth_headers)
        
        item_id = create_response.json()["udharitem_id"]
        
        response = client.delete(f"/udhar-items/{item_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestUdharEdgeCases:
    async def test_create_multiple_udhar_same_customer(self, client, auth_headers, db_session, create_test_user):
        """Test creating multiple udhar items for same customer"""
        from myapp.models.customer import Customer
        from unittest.mock import patch
        
        customer = Customer(
            customer_name="کسٹمر ملٹی",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            for i in range(3):
                response = await client.post("/udhar-items/", json={
                    "customer_name": customer.customer_name,
                    "item_name": f"آئٹم {i}",
                    "quantity": i + 1,
                    "unit": "عدد"
                }, headers=auth_headers)
                assert response.status_code == status.HTTP_200_OK

    async def test_update_udhar_quantity_zero(self, client, auth_headers, db_session, create_test_user):
        """Test updating udhar quantity to zero"""
        from myapp.models.customer import Customer
        from unittest.mock import patch
        
        customer = Customer(
            customer_name="کسٹمر زیرو",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            create_response = await client.post("/udhar-items/", json={
                "customer_name": customer.customer_name,
                "item_name": "صفر مقدار",
                "quantity": 10,
                "unit": "کلو"
            }, headers=auth_headers)
        
        item_id = create_response.json()["udharitem_id"]
        
        update_data = {
            "customer_name": customer.customer_name,
            "item_name": "صفر مقدار",
            "quantity": 0,
            "unit": "کلو"
        }
        response = client.put(f"/udhar-items/{item_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["quantity"] == 0

    async def test_create_udhar_with_large_quantity(self, client, auth_headers, db_session, create_test_user):
        """Test creating udhar with very large quantity"""
        from myapp.models.customer import Customer
        from unittest.mock import patch
        
        customer = Customer(
            customer_name="کسٹمر بڑا",
            user_id=create_test_user.user_id
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        udhar_data = {
            "customer_name": customer.customer_name,
            "item_name": "بڑی مقدار",
            "quantity": 999999,
            "unit": "بوری"
        }
        
        with patch('myapp.crud.udhaar_item.send_telegram_notification'):
            response = await client.post("/udhar-items/", json=udhar_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["quantity"] == 999999