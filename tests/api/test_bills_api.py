import pytest
from fastapi import status
from unittest.mock import patch

pytestmark = pytest.mark.asyncio


class TestGetBillByCustomerId:
    """Test get bills by customer ID endpoints"""
    
    async def test_get_bills_by_customer_id_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting bills for a specific customer by ID"""
        response = client.get(f"/bills/customer/{create_test_customer.customer_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "bill_id" in data[0]

    async def test_get_bills_by_customer_id_not_found(self, client, auth_headers):
        """Test getting bills for non-existent customer"""
        response = client.get("/bills/customer/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_id_no_bills(self, client, auth_headers, create_test_customer):
        """Test getting bills when customer has no bills"""
        response = client.get(f"/bills/customer/{create_test_customer.customer_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_id_without_auth(self, client, create_test_customer):
        """Test getting bills without authentication"""
        response = client.get(f"/bills/customer/{create_test_customer.customer_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetBillByCustomerName:
    """Test get bills by customer name endpoints"""
    
    async def test_get_bills_by_customer_name_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting bills for a specific customer by name"""
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_bills_by_customer_name_not_found(self, client, auth_headers):
        """Test getting bills for non-existent customer name"""
        response = client.get("/bills/customer/name/غیرموجود", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_name_no_bills(self, client, auth_headers, create_test_customer):
        """Test getting bills when customer has no bills"""
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_name_without_auth(self, client, create_test_customer):
        """Test getting bills without authentication"""
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetAllBills:
    """Test get all bills endpoints"""
    
    async def test_get_all_bills_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting all bills for authenticated user"""
        response = client.get("/bills/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_all_bills_with_status_filter(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting bills with status filter"""
        response = client.get("/bills/?status=unpaid", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_all_bills_empty(self, client, auth_headers):
        """Test getting bills when none exist"""
        response = client.get("/bills/", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_all_bills_without_auth(self, client):
        """Test getting bills without authentication"""
        response = client.get("/bills/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPayBill:
    """Test pay bill endpoints"""
    
    async def test_pay_bill_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test successfully paying a bill"""
        response = client.put(f"/bills/pay/{create_test_customer.customer_name}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    async def test_pay_bill_customer_not_found(self, client, auth_headers):
        """Test paying bill for non-existent customer"""
        response = client.put("/bills/pay/غیرموجود", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_pay_bill_without_auth(self, client, create_test_customer):
        """Test paying bill without authentication"""
        response = client.put(f"/bills/pay/{create_test_customer.customer_name}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteBill:
    """Test delete bill endpoints"""
    
    async def test_delete_bill_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test successfully deleting a bill"""
        # First pay the bill
        client.put(f"/bills/pay/{create_test_customer.customer_name}", headers=auth_headers)
        
        # Get bill ID
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}", headers=auth_headers)
        bill_id = response.json()[0]["bill_id"]
        
        # Delete bill
        delete_response = client.delete(f"/bills/{bill_id}", headers=auth_headers)
        
        assert delete_response.status_code == status.HTTP_200_OK
        assert "message" in delete_response.json()

    async def test_delete_unpaid_bill(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test deleting an unpaid bill (should fail)"""
        # Get bill ID
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}", headers=auth_headers)
        bill_id = response.json()[0]["bill_id"]
        
        # Try to delete unpaid bill
        delete_response = client.delete(f"/bills/{bill_id}", headers=auth_headers)
        
        assert delete_response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_bill_not_found(self, client, auth_headers):
        """Test deleting non-existent bill"""
        response = client.delete("/bills/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_bill_without_auth(self, client):
        """Test deleting bill without authentication"""
        response = client.delete("/bills/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSearchBills:
    """Test search bills endpoints"""
    
    async def test_search_bills_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test searching bills by keyword"""
        response = client.get(f"/bills/search/?keyword={create_test_customer.customer_name[:3]}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_search_bills_no_results(self, client, auth_headers):
        """Test search with no matching results"""
        response = client.get("/bills/search/?keyword=غیرموجود", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_search_bills_empty_keyword(self, client, auth_headers):
        """Test search with empty keyword"""
        response = client.get("/bills/search/?keyword=", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_search_bills_case_insensitive(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test case-insensitive search"""
        # Search with uppercase
        response = client.get(f"/bills/search/?keyword={create_test_customer.customer_name.upper()[:3]}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_search_bills_without_auth(self, client):
        """Test search without authentication"""
        response = client.get("/bills/search/?keyword=test")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBillEdgeCases:
    """Test edge cases and error scenarios"""
    
    async def test_multiple_bills_same_customer(self, client, auth_headers, create_test_customer):
        """Test creating and retrieving multiple bills for same customer"""
        from myapp.models.bill import Bill
        
        # Create multiple bills directly
        for i in range(3):
            bill = Bill(
                customer_id=create_test_customer.customer_id,
                total_amount=1000 * (i + 1),
                status="unpaid",
                user_id=create_test_customer.user_id
            )
            client.db_session.add(bill)
        await client.db_session.commit()
        
        response = client.get(f"/bills/customer/{create_test_customer.customer_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3

    async def test_pay_bill_twice(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test paying same bill twice"""
        # First payment
        response1 = client.put(f"/bills/pay/{create_test_customer.customer_name}", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second payment (should be handled gracefully)
        response2 = client.put(f"/bills/pay/{create_test_customer.customer_name}", headers=auth_headers)
        assert response2.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    async def test_bill_owner_isolation(self, client, auth_headers, create_test_customer, create_test_bill, test_user_data_2):
        """Test that users cannot see each other's bills"""
        # Get first user's bills
        response1 = client.get("/bills/", headers=auth_headers)
        first_user_count = len(response1.json())
        
        # Create second user
        client.post("/auth/register", json=test_user_data_2)
        login_response = client.post("/auth/login", data={
            "username": test_user_data_2["username"],
            "password": test_user_data_2["password"]
        })
        second_token = login_response.json()["access_token"]
        second_headers = {"Authorization": f"Bearer {second_token}"}
        
        # Second user should see different bills
        response2 = client.get("/bills/", headers=second_headers)
        assert response2.status_code == status.HTTP_404_NOT_FOUND or len(response2.json()) != first_user_count

    async def test_bill_status_after_payment(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test bill status changes to paid after payment"""
        # Check initial status
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}", headers=auth_headers)
        assert response.json()[0]["status"] == "unpaid"
        
        # Pay bill
        client.put(f"/bills/pay/{create_test_customer.customer_name}", headers=auth_headers)
        
        # Check updated status
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}", headers=auth_headers)
        assert response.json()[0]["status"] == "paid"

    async def test_search_with_special_characters(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test search with special characters in keyword"""
        response = client.get("/bills/search/?keyword=test@123", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND