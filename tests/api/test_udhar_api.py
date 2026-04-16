import pytest
from fastapi import status
from unittest.mock import patch

pytestmark = pytest.mark.asyncio


class TestPayUdhaar:
    """Test pay udhaar endpoints"""
    
    async def test_pay_udhaar_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully paying udhaar for a customer"""
        response = client.post(
            f"/udhars/pay?customer_name={create_test_customer.customer_name}", 
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "paid" in data["message"].lower() or "ادا" in data["message"]

    async def test_pay_udhaar_customer_not_found(self, client, auth_headers):
        """Test paying udhaar for non-existent customer"""
        response = client.post("/udhars/pay?customer_name=غیرموجود", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_pay_udhaar_no_udhar_found(self, client, auth_headers, create_test_customer):
        """Test paying udhaar when customer has no udhar record"""
        response = client.post(
            f"/udhars/pay?customer_name={create_test_customer.customer_name}", 
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_pay_udhaar_without_auth(self, client, create_test_customer):
        """Test paying udhaar without authentication"""
        response = client.post(f"/udhars/pay?customer_name={create_test_customer.customer_name}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetAllUdhar:
    """Test get all udhar endpoints"""
    
    async def test_get_all_udhar_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test getting all udhar records"""
        response = client.get("/udhars/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_all_udhar_empty(self, client, auth_headers):
        """Test getting udhar when none exist"""
        response = client.get("/udhars/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_all_udhar_without_auth(self, client):
        """Test getting udhar without authentication"""
        response = client.get("/udhars/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUdharByCustomer:
    """Test get udhar by customer name endpoints"""
    
    async def test_get_udhar_by_customer_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test getting udhar for specific customer"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "customer_name" in data or "total" in data

    async def test_get_udhar_by_customer_not_found(self, client, auth_headers):
        """Test getting udhar for non-existent customer"""
        response = client.get("/udhars/غیرموجود", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_udhar_by_customer_no_record(self, client, auth_headers, create_test_customer):
        """Test getting udhar when customer has no udhar record"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_udhar_by_customer_without_auth(self, client, create_test_customer):
        """Test getting udhar without authentication"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDirectAddition:
    """Test direct addition to udhar"""
    
    async def test_direct_addition_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully adding direct amount to udhar"""
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=500",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["direct_addition"] == 500

    async def test_direct_addition_negative_amount(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test direct addition with negative amount"""
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=-100",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_direct_addition_customer_not_found(self, client, auth_headers):
        """Test direct addition for non-existent customer"""
        response = client.put("/udhars/غیرموجود/direct-addition?amount=500", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_direct_addition_without_auth(self, client, create_test_customer):
        """Test direct addition without authentication"""
        response = client.put(f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=500")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDirectDeduction:
    """Test direct deduction from udhar"""
    
    async def test_direct_deduction_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully deducting amount from udhar"""
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=300",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["direct_deduction"] == 300

    async def test_direct_deduction_exceeding_total(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test deducting more than total amount"""
        # Try to deduct very large amount
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=999999",
            headers=auth_headers
        )
        # Should either succeed or return bad request
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    async def test_direct_deduction_negative_amount(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test direct deduction with negative amount"""
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=-100",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_direct_deduction_without_auth(self, client, create_test_customer):
        """Test direct deduction without authentication"""
        response = client.put(f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=300")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUdharSummary:
    """Test udhar summary endpoints"""
    
    async def test_get_udhar_summary_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test getting udhar summary for a customer"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "subtotal" in data
        assert "direct_addition" in data
        assert "direct_deduction" in data
        assert "total" in data
        assert "status" in data

    async def test_get_udhar_summary_customer_not_found(self, client, auth_headers):
        """Test getting summary for non-existent customer"""
        response = client.get("/udhars/غیرموجود/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_udhar_summary_no_record(self, client, auth_headers, create_test_customer):
        """Test getting summary when customer has no udhar record"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_udhar_summary_without_auth(self, client, create_test_customer):
        """Test getting summary without authentication"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}/summary")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteUdhar:
    """Test delete udhar endpoints"""
    
    async def test_delete_udhar_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully deleting an udhar record"""
        # First get udhar ID
        response = client.get(f"/udhars/{create_test_customer.customer_name}", headers=auth_headers)
        udhar_id = response.json()["udhar_id"]
        
        # Delete udhar
        delete_response = client.delete(f"/udhars/{udhar_id}", headers=auth_headers)
        
        assert delete_response.status_code == status.HTTP_200_OK
        assert "message" in delete_response.json()
        
        # Verify udhar is deleted
        get_response = client.get(f"/udhars/{create_test_customer.customer_name}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_udhar_not_found(self, client, auth_headers):
        """Test deleting non-existent udhar"""
        response = client.delete("/udhars/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_udhar_without_auth(self, client):
        """Test deleting udhar without authentication"""
        response = client.delete("/udhars/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUdharEdgeCases:
    """Test edge cases and calculations"""
    
    async def test_direct_addition_then_deduction(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test adding then deducting amounts"""
        customer_name = create_test_customer.customer_name
        
        # Add amount
        add_response = client.put(f"/udhars/{customer_name}/direct-addition?amount=1000", headers=auth_headers)
        assert add_response.status_code == status.HTTP_200_OK
        
        # Deduct amount
        deduct_response = client.put(f"/udhars/{customer_name}/direct-deduction?amount=500", headers=auth_headers)
        assert deduct_response.status_code == status.HTTP_200_OK
        
        # Check summary
        summary_response = client.get(f"/udhars/{customer_name}/summary", headers=auth_headers)
        summary = summary_response.json()
        assert summary["direct_addition"] == 1000
        assert summary["direct_deduction"] == 500

    async def test_multiple_direct_additions(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test multiple direct additions"""
        customer_name = create_test_customer.customer_name
        amounts = [100, 200, 300, 400]
        
        for amount in amounts:
            response = client.put(f"/udhars/{customer_name}/direct-addition?amount={amount}", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
        
        summary_response = client.get(f"/udhars/{customer_name}/summary", headers=auth_headers)
        summary = summary_response.json()
        assert summary["direct_addition"] == sum(amounts)

    async def test_pay_after_direct_additions(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test paying udhaar after direct additions"""
        customer_name = create_test_customer.customer_name
        
        # Add amount
        client.put(f"/udhars/{customer_name}/direct-addition?amount=500", headers=auth_headers)
        
        # Pay udhaar
        pay_response = client.post(f"/udhars/pay?customer_name={customer_name}", headers=auth_headers)
        assert pay_response.status_code == status.HTTP_200_OK
        
        # Verify udhaar is paid
        summary_response = client.get(f"/udhars/{customer_name}/summary", headers=auth_headers)
        assert summary_response.json()["status"] == "paid" or summary_response.json()["total"] == 0

    async def test_user_udhar_isolation(self, client, auth_headers, create_test_customer, create_test_udhar, test_user_data_2):
        """Test that users cannot see each other's udhar records"""
        # Get first user's udhar
        response1 = client.get("/udhars/", headers=auth_headers)
        first_user_count = len(response1.json())
        
        # Create second user
        client.post("/auth/register", json=test_user_data_2)
        login_response = client.post("/auth/login", data={
            "username": test_user_data_2["username"],
            "password": test_user_data_2["password"]
        })
        second_token = login_response.json()["access_token"]
        second_headers = {"Authorization": f"Bearer {second_token}"}
        
        # Second user should see different udhar records
        response2 = client.get("/udhars/", headers=second_headers)
        # Their udhar count should be 0 or different
        assert len(response2.json()) != first_user_count or len(response2.json()) == 0

    async def test_summary_after_multiple_operations(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test summary calculation after multiple operations"""
        customer_name = create_test_customer.customer_name
        
        # Get initial summary
        initial = client.get(f"/udhars/{customer_name}/summary", headers=auth_headers).json()
        initial_total = initial["total"]
        
        # Add amount
        client.put(f"/udhars/{customer_name}/direct-addition?amount=1000", headers=auth_headers)
        
        # Deduct amount
        client.put(f"/udhars/{customer_name}/direct-deduction?amount=300", headers=auth_headers)
        
        # Get updated summary
        updated = client.get(f"/udhars/{customer_name}/summary", headers=auth_headers).json()
        
        # Verify calculation
        expected_total = initial_total + 1000 - 300
        assert updated["total"] == expected_total