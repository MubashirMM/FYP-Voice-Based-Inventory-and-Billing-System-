import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio


class TestPayUdhaar:
    """Test pay udhaar endpoints"""
    
    async def test_pay_udhaar_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully paying udhaar for a customer"""
        response = client.post(
            f"/udhars/pay?customer_name={create_test_customer.customer_name}", 
            headers=auth_headers
        )
        
        # Your endpoint might return 200 or 404 depending on implementation
        # If it's returning 404, the customer might not have a bill
        if response.status_code == status.HTTP_404_NOT_FOUND:
            # Create a bill first by adding some amount
            client.put(f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=1000", headers=auth_headers)
            response = client.post(f"/udhars/pay?customer_name={create_test_customer.customer_name}", headers=auth_headers)
        
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
        # If no udhar exists, should return 404
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
        # First ensure there's an unpaid udhar by adding some amount
        customer_name = create_test_customer.customer_name
        client.put(f"/udhars/{customer_name}/direct-addition?amount=100", headers=auth_headers)
        
        response = client.get(f"/udhars/{customer_name}", headers=auth_headers)
        
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
        """Test direct addition with negative amount (should return 400)"""
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=-100",
            headers=auth_headers
        )
        # Your CRUD returns 400 for negative amounts
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_direct_addition_customer_auto_created(self, client, auth_headers):
        """Test direct addition creates customer if not exists (current behavior)"""
        response = client.put("/udhars/نیا_کسٹمر/direct-addition?amount=500", headers=auth_headers)
        
        # Your CRUD creates customer if not exists, so should return 200
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["direct_addition"] == 500

    async def test_direct_addition_without_auth(self, client, create_test_customer):
        """Test direct addition without authentication"""
        response = client.put(f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=500")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDirectDeduction:
    """Test direct deduction from udhar"""
    
    async def test_direct_deduction_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully deducting amount from udhar"""
        # First add some amount to deduct from
        client.put(f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=1000", headers=auth_headers)
        
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
        # First add a small amount
        client.put(f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=100", headers=auth_headers)
        
        # Try to deduct very large amount
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=999999",
            headers=auth_headers
        )
        # Should return 400 because amount exceeds total
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_direct_deduction_negative_amount(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test direct deduction with negative amount (should return 400)"""
        response = client.put(
            f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=-100",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_direct_deduction_customer_not_found(self, client, auth_headers):
        """Test direct deduction for non-existent customer"""
        response = client.put("/udhars/غیرموجود/direct-deduction?amount=300", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_direct_deduction_without_auth(self, client, create_test_customer):
        """Test direct deduction without authentication"""
        response = client.put(f"/udhars/{create_test_customer.customer_name}/direct-deduction?amount=300")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUdharSummary:
    """Test udhar summary endpoints"""
    
    async def test_get_udhar_summary_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test getting udhar summary for a customer"""
        # Add some amount to ensure udhar exists
        client.put(f"/udhars/{create_test_customer.customer_name}/direct-addition?amount=500", headers=auth_headers)
        
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
        # Your summary endpoint might create a udhar record if none exists
        # So it could return 200 with zero values
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "total" in data
            assert data["total"] == 0
        else:
            assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_udhar_summary_without_auth(self, client, create_test_customer):
        """Test getting summary without authentication"""
        response = client.get(f"/udhars/{create_test_customer.customer_name}/summary")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteUdhar:
    """Test delete udhar endpoints"""
    
    async def test_delete_udhar_success(self, client, auth_headers, create_test_customer, create_test_udhar):
        """Test successfully deleting an udhar record"""
        # First get udhar ID from the udhar record
        udhar_id = create_test_udhar.udhar_id
        
        # Delete udhar
        delete_response = client.delete(f"/udhars/{udhar_id}", headers=auth_headers)
        
        assert delete_response.status_code == status.HTTP_200_OK
        assert "message" in delete_response.json()
        
        # Verify udhar is deleted - should return 404 when trying to get it
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
        
        # Verify udhaar is paid (status should be "paid" or total should be 0)
        summary_response = client.get(f"/udhars/{customer_name}/summary", headers=auth_headers)
        summary = summary_response.json()
        assert summary["status"] == "paid" or summary["total"] == 0
