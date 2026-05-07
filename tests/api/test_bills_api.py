import pytest
from fastapi import status
from datetime import date

pytestmark = pytest.mark.asyncio


class TestGetBillByCustomerId:
    """Test get bills by customer ID endpoints"""
    
    async def test_get_bills_by_customer_id_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting bills for a customer by ID"""
        response = client.get(
            f"/bills/customer/{create_test_customer.customer_id}", 
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_bills_by_customer_id_not_found(self, client, auth_headers):
        """Test getting bills for non-existent customer"""
        response = client.get("/bills/customer/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_id_no_bills(self, client, auth_headers, create_test_customer):
        """Test getting bills when customer has no bills"""
        response = client.get(
            f"/bills/customer/{create_test_customer.customer_id}", 
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_id_without_auth(self, client, create_test_customer):
        """Test getting bills without authentication"""
        response = client.get(f"/bills/customer/{create_test_customer.customer_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetBillByCustomerName:
    """Test get bills by customer name endpoints"""
    
    async def test_get_bills_by_customer_name_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting bills for a customer by name"""
        response = client.get(
            f"/bills/customer/name/{create_test_customer.customer_name}", 
            headers=auth_headers
        )
        
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
        response = client.get(
            f"/bills/customer/name/{create_test_customer.customer_name}", 
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_bills_by_customer_name_without_auth(self, client, create_test_customer):
        """Test getting bills without authentication"""
        response = client.get(f"/bills/customer/name/{create_test_customer.customer_name}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetAllBills:
    """Test get all bills endpoints"""
    
    async def test_get_all_bills_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test getting all bills"""
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
        
        # Your endpoint returns 404 when no bills exist
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_all_bills_without_auth(self, client):
        """Test getting bills without authentication"""
        response = client.get("/bills/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPayBill:
    """Test pay bill endpoints"""
    
  
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

    async def test_delete_unpaid_bill(self, client, auth_headers, create_test_bill):
        """Test deleting an unpaid bill - should fail"""
        # Delete without paying first
        response = client.delete(f"/bills/{create_test_bill.bill_id}", headers=auth_headers)
        
        # Cannot delete unpaid bill - returns 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_bill_not_found(self, client, auth_headers):
        """Test deleting non-existent bill"""
        response = client.delete("/bills/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_bill_without_auth(self, client, create_test_bill):
        """Test deleting bill without authentication"""
        response = client.delete(f"/bills/{create_test_bill.bill_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSearchBills:
    """Test search bills endpoints"""
    
    async def test_search_bills_success(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test searching bills by customer name"""
        # Your endpoint uses GET with query param
        response = client.get(
            f"/bills/search/?keyword={create_test_customer.customer_name[:3]}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_search_bills_no_results(self, client, auth_headers):
        """Test searching with no matching results"""
        response = client.get("/bills/search/?keyword=غیرموجودنام", headers=auth_headers)
        
        # Returns 404 when no results found
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_search_bills_empty_keyword(self, client, auth_headers):
        """Test searching with empty keyword"""
        response = client.get("/bills/search/?keyword=", headers=auth_headers)
        
        # Returns 400 for empty keyword
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_search_bills_case_insensitive(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test case-insensitive search"""
        # Search with uppercase
        response = client.get(
            f"/bills/search/?keyword={create_test_customer.customer_name[:3].upper()}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK

    async def test_search_bills_without_auth(self, client):
        """Test searching bills without authentication"""
        response = client.get("/bills/search/?keyword=test")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBillEdgeCases:
    """Test bill edge cases and scenarios"""
    
    async def test_multiple_bills_same_customer(self, client, auth_headers, create_test_customer, create_test_user, db_session):
        """Test multiple bills for same customer"""
        from myapp.models.bill import Bill
        from datetime import date
        
        today = date.today()
        
        # Create first bill (unpaid)
        bill1 = Bill(
            customer_id=create_test_customer.customer_id,
            user_id=create_test_user.user_id,
            customer_name=create_test_customer.customer_name,
            udhar_items_total=1000.00,
            direct_addition=0.0,
            direct_deduction=0.0,
            effective_total=1000.00,
            status="unpaid",
            bill_date=today
        )
        
        # Create second bill (paid)
        bill2 = Bill(
            customer_id=create_test_customer.customer_id,
            user_id=create_test_user.user_id,
            customer_name=create_test_customer.customer_name,
            udhar_items_total=2000.00,
            direct_addition=0.0,
            direct_deduction=0.0,
            effective_total=2000.00,
            status="paid",
            bill_date=today
        )
        
        db_session.add_all([bill1, bill2])
        await db_session.commit()
        
        # Test get bills by customer ID
        response = client.get(f"/bills/customer/{create_test_customer.customer_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
        
        # Verify both bills are returned
        statuses = [bill["status"] for bill in data]
        assert "unpaid" in statuses
        assert "paid" in statuses

    async def test_search_with_special_characters(self, client, auth_headers, create_test_customer, create_test_bill):
        """Test searching with special characters in keyword"""
        # Test with various special characters
        special_keywords = ["@#$%", "test!", "customer 123", "   spaces   "]
        
        for keyword in special_keywords:
            response = client.get(f"/bills/search/?keyword={keyword}", headers=auth_headers)
            # Should return 404 for no results or 400 for invalid
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]