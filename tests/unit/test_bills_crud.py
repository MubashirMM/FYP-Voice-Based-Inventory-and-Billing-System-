# C:\FYP\Backend\fast-api\tests\unit\test_bill_crud.py
import sys
from pathlib import Path

from tests.unit.test_udharitems_crud import create_test_user_and_item

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from myapp.crud.bill import (
    get_customer_by_name,
    sync_bill_from_udhar,
    format_bill,
    get_all_bills,
    get_bills_by_customer,
    pay_bill,
    pay_bill_by_customer_name,
    delete_bill
)
from myapp.crud.user import register_user
from myapp.crud.items import create_items
from myapp.crud.udhaar_item import create_udhar
from myapp.crud.udhar import (
    update_direct_addition, 
    update_direct_deduction,
    get_or_create_customer_by_name
)
from myapp.schemas.items import ItemCreate


# # ============================================
# # HELPER FUNCTIONS
# # ============================================
# async def create_test_user_and_item(db_session):
#     """Helper to create test user and item"""
#     user = await register_user(db_session, "bill@example.com", "BillUser", "pass123")
    
#     item_data = ItemCreate(
#         item_name="Test Product",
#         item_unit="KG",
#         unit_price=100,
#         stock_quantity=50
#     )
#     item = await create_items(db_session, item_data, user)
    
#     return user, item


# async def create_test_udhar_with_items(db_session, user, customer_name="Bill Customer", quantities=None):
#     """Helper to create udhar with items"""
#     background_tasks = BackgroundTasks()
    
#     if quantities is None:
#         quantities = [5, 3]  # Default quantities
    
#     created_items = []
#     for qty in quantities:
#         result = await create_udhar(
#             db=db_session,
#             customer_name=customer_name,
#             item_name="Test Product",
#             quantity=qty,
#             unit="KG",
#             current_user=user,
#             background_tasks=background_tasks
#         )
#         created_items.append(result)
    
#     return created_items


# # ============================================
# # GET CUSTOMER BY NAME TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_get_customer_by_name_success(db_session):
#     """Test getting existing customer by name"""
#     user = await register_user(db_session, "billcust1@example.com", "BillCust1", "pass123")
    
#     customer = await get_or_create_customer_by_name(db_session, "Bill Test Customer", user)
    
#     found = await get_customer_by_name(db_session, "Bill Test Customer", user)
    
#     assert found is not None
#     assert found.customer_name == "Bill Test Customer"


# @pytest.mark.asyncio
# async def test_get_customer_by_name_not_found(db_session):
#     """Test getting non-existent customer"""
#     user = await register_user(db_session, "billcust2@example.com", "BillCust2", "pass123")
    
#     with pytest.raises(HTTPException) as exc:
#         await get_customer_by_name(db_session, "Non Existent", user)
    
#     assert exc.value.status_code == 404


# # ============================================
# # SYNC BILL FROM UDHAR TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_sync_bill_from_udhar_success(db_session):
#     """Test successful bill sync from udhar"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar items
#     await create_udhar(
#         db=db_session,
#         customer_name="Sync Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Get customer
#     customer = await get_customer_by_name(db_session, "Sync Customer", user)
    
#     # Sync bill
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill is not None
#     assert bill.udhar_items_total == 500  # 5 * 100
#     assert bill.effective_total == 500
#     assert bill.status == "unpaid"


# @pytest.mark.asyncio
# async def test_sync_bill_with_multiple_items(db_session):
#     """Test syncing bill with multiple udhar items"""
#     user, item = await create_test_user_and_item(db_session)
    
#     # Create multiple udhar items
#     await create_test_udhar_with_items(db_session, user, "Multi Item Customer", [2, 3, 4])
    
#     # Get customer
#     customer = await get_customer_by_name(db_session, "Multi Item Customer", user)
    
#     # Sync bill
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill is not None
#     assert bill.udhar_items_total == 900  # (2+3+4) * 100
#     assert bill.effective_total == 900


# @pytest.mark.asyncio
# async def test_sync_bill_with_direct_addition(db_session):
#     """Test syncing bill with direct addition"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar items
#     await create_udhar(
#         db=db_session,
#         customer_name="Add Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Add direct addition
#     await update_direct_addition(db_session, "Add Customer", 200, user)
    
#     # Get customer and sync
#     customer = await get_customer_by_name(db_session, "Add Customer", user)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill is not None
#     assert bill.udhar_items_total == 500
#     assert bill.direct_addition == 200
#     assert bill.effective_total == 700


# @pytest.mark.asyncio
# async def test_sync_bill_with_direct_deduction(db_session):
#     """Test syncing bill with direct deduction"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar items
#     await create_udhar(
#         db=db_session,
#         customer_name="Deduct Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Add direct deduction
#     await update_direct_deduction(db_session, "Deduct Customer", 300, user)
    
#     # Get customer and sync
#     customer = await get_customer_by_name(db_session, "Deduct Customer", user)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill is not None
#     assert bill.udhar_items_total == 500
#     assert bill.direct_deduction == 300
#     assert bill.effective_total == 200


# @pytest.mark.asyncio
# async def test_sync_bill_zero_total(db_session):
#     """Test syncing bill when total becomes zero"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar items
#     await create_udhar(
#         db=db_session,
#         customer_name="Zero Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Add deduction to make total zero
#     await update_direct_deduction(db_session, "Zero Customer", 500, user)
    
#     # Get customer and sync
#     customer = await get_customer_by_name(db_session, "Zero Customer", user)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill is not None
#     assert bill.effective_total == 0
#     assert bill.status == "paid"


# @pytest.mark.asyncio
# async def test_sync_bill_no_udhar(db_session):
#     """Test syncing bill when no udhar exists"""
#     user, _ = await create_test_user_and_item(db_session)
    
#     # Create customer but no udhar
#     customer = await get_or_create_customer_by_name(db_session, "No Udhar Customer", user)
    
#     # Sync bill
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill is None




# # ============================================
# # GET ALL BILLS TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_get_all_bills_empty(db_session):
#     """Test getting all bills when none exist"""
#     user, _ = await create_test_user_and_item(db_session)
    
#     bills = await get_all_bills(db_session, user)
    
#     assert isinstance(bills, list)
#     assert len(bills) == 0


# @pytest.mark.asyncio
# async def test_get_all_bills_multiple(db_session):
#     """Test getting multiple bills"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhars for different customers
#     customers = ["Bill A", "Bill B", "Bill C"]
    
#     for customer in customers:
#         await create_udhar(
#             db=db_session,
#             customer_name=customer,
#             item_name="Test Product",
#             quantity=2,
#             unit="KG",
#             current_user=user,
#             background_tasks=background_tasks
#         )
#         # Sync bill for each
#         cust = await get_customer_by_name(db_session, customer, user)
#         await sync_bill_from_udhar(db_session, cust.customer_id, user)
    
#     bills = await get_all_bills(db_session, user)
    
#     assert len(bills) >= 3
#     customer_names = [b["customer_name"] for b in bills]
#     assert "Bill A" in customer_names


# @pytest.mark.asyncio
# async def test_get_all_bills_filter_by_status(db_session):
#     """Test getting bills filtered by status"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create unpaid bill
#     await create_udhar(
#         db=db_session,
#         customer_name="Unpaid Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
#     cust1 = await get_customer_by_name(db_session, "Unpaid Customer", user)
#     await sync_bill_from_udhar(db_session, cust1.customer_id, user)
    
#     # Create and pay bill
#     await create_udhar(
#         db=db_session,
#         customer_name="Paid Customer",
#         item_name="Test Product",
#         quantity=3,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
#     cust2 = await get_customer_by_name(db_session, "Paid Customer", user)
#     await sync_bill_from_udhar(db_session, cust2.customer_id, user)
#     await pay_bill(db_session, cust2.customer_id, user)
    
#     # Get only unpaid bills
#     unpaid_bills = await get_all_bills(db_session, user, status="unpaid")
#     paid_bills = await get_all_bills(db_session, user, status="paid")
    
#     assert len(unpaid_bills) >= 1
#     assert len(paid_bills) >= 1


# @pytest.mark.asyncio
# async def test_get_all_bills_user_specific(db_session):
#     """Test that users only see their own bills"""
#     # User 1
#     user1 = await register_user(db_session, "billuser1@example.com", "BillUser1", "pass123")
#     item1_data = ItemCreate(item_name="Item1", item_unit="KG", unit_price=100, stock_quantity=50)
#     await create_items(db_session, item1_data, user1)
    
#     # User 2
#     user2 = await register_user(db_session, "billuser2@example.com", "BillUser2", "pass123")
#     item2_data = ItemCreate(item_name="Item2", item_unit="KG", unit_price=200, stock_quantity=30)
#     await create_items(db_session, item2_data, user2)
    
#     background_tasks = BackgroundTasks()
    
#     # Create bill for user1
#     await create_udhar(
#         db=db_session,
#         customer_name="User1 Customer",
#         item_name="Item1",
#         quantity=5,
#         unit="KG",
#         current_user=user1,
#         background_tasks=background_tasks
#     )
#     cust1 = await get_customer_by_name(db_session, "User1 Customer", user1)
#     await sync_bill_from_udhar(db_session, cust1.customer_id, user1)
    
#     # Create bill for user2
#     await create_udhar(
#         db=db_session,
#         customer_name="User2 Customer",
#         item_name="Item2",
#         quantity=3,
#         unit="KG",
#         current_user=user2,
#         background_tasks=background_tasks
#     )
#     cust2 = await get_customer_by_name(db_session, "User2 Customer", user2)
#     await sync_bill_from_udhar(db_session, cust2.customer_id, user2)
    
#     user1_bills = await get_all_bills(db_session, user1)
#     user2_bills = await get_all_bills(db_session, user2)
    
#     assert len(user1_bills) == 1
#     assert len(user2_bills) == 1
#     assert user1_bills[0]["customer_name"] == "User1 Customer"
#     assert user2_bills[0]["customer_name"] == "User2 Customer"


# # ============================================
# # GET BILLS BY CUSTOMER TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_get_bills_by_customer_success(db_session):
#     """Test getting bills for specific customer"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create multiple udhars for same customer
#     await create_udhar(
#         db=db_session,
#         customer_name="Same Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     await create_udhar(
#         db=db_session,
#         customer_name="Same Customer",
#         item_name="Test Product",
#         quantity=3,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "Same Customer", user)
#     bills = await get_bills_by_customer(db_session, customer.customer_id, user)
    
#     assert len(bills) >= 1


# @pytest.mark.asyncio
# async def test_get_bills_by_customer_no_bills(db_session):
#     """Test getting bills for customer with no bills"""
#     user, _ = await create_test_user_and_item(db_session)
    
#     customer = await get_or_create_customer_by_name(db_session, "No Bills Customer", user)
#     bills = await get_bills_by_customer(db_session, customer.customer_id, user)
    
#     assert isinstance(bills, list)
#     assert len(bills) == 0


# # ============================================
# # PAY BILL TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_pay_bill_success(db_session):
#     """Test successful bill payment"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar and sync bill
#     await create_udhar(
#         db=db_session,
#         customer_name="Pay Bill Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "Pay Bill Customer", user)
#     await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     # Pay the bill
#     paid_bill = await pay_bill(db_session, customer.customer_id, user)
    
#     assert paid_bill is not None
#     assert paid_bill.status == "paid"


# @pytest.mark.asyncio
# async def test_pay_bill_no_unpaid_bill(db_session):
#     """Test paying when no unpaid bill exists"""
#     user, _ = await create_test_user_and_item(db_session)
    
#     customer = await get_or_create_customer_by_name(db_session, "No Bill Customer", user)
    
#     result = await pay_bill(db_session, customer.customer_id, user)
    
#     assert result is None


# @pytest.mark.asyncio
# async def test_pay_bill_by_customer_name_success(db_session):
#     """Test paying bill by customer name"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar
#     await create_udhar(
#         db=db_session,
#         customer_name="PayByName Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Pay by name
#     result = await pay_bill_by_customer_name(db_session, "PayByName Customer", user)
    
#     assert result is not None
#     assert result["message"] == "بل اور ادھار کامیابی سے ادا کر دیا گیا"
#     assert result["customer_name"] == "PayByName Customer"
#     assert result["status"] == "paid"


# @pytest.mark.asyncio
# async def test_pay_bill_by_customer_name_not_found(db_session):
#     """Test paying bill for non-existent customer"""
#     user, _ = await create_test_user_and_item(db_session)
    
#     with pytest.raises(HTTPException) as exc:
#         await pay_bill_by_customer_name(db_session, "Non Existent", user)
    
#     assert exc.value.status_code == 404


# @pytest.mark.asyncio
# async def test_pay_bill_by_customer_name_already_paid(db_session):
#     """Test paying bill that is already paid"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create and pay udhar
#     await create_udhar(
#         db=db_session,
#         customer_name="Already Paid",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Pay first time
#     await pay_bill_by_customer_name(db_session, "Already Paid", user)
    
#     # Try to pay again
#     with pytest.raises(HTTPException) as exc:
#         await pay_bill_by_customer_name(db_session, "Already Paid", user)
    
#     assert exc.value.status_code == 400


# # ============================================
# # DELETE BILL TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_delete_bill_success(db_session):
#     """Test successful bill deletion"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar and sync bill
#     await create_udhar(
#         db=db_session,
#         customer_name="Delete Bill Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "Delete Bill Customer", user)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     # First pay the bill
#     await pay_bill(db_session, customer.customer_id, user)
    
#     # Delete the bill
#     result = await delete_bill(db_session, bill.bill_id, user)
    
#     assert result is True


# @pytest.mark.asyncio
# async def test_delete_bill_not_found(db_session):
#     """Test deleting non-existent bill"""
#     user, _ = await create_test_user_and_item(db_session)
    
#     result = await delete_bill(db_session, 99999, user)
    
#     assert result is False


# @pytest.mark.asyncio
# async def test_delete_bill_unpaid(db_session):
#     """Test deleting unpaid bill (should not be allowed)"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar and sync bill (unpaid)
#     await create_udhar(
#         db=db_session,
#         customer_name="Unpaid Delete",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "Unpaid Delete", user)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     # Try to delete unpaid bill
#     result = await delete_bill(db_session, bill.bill_id, user)
    
#     assert result == "unpaid"  # Cannot delete unpaid bill


# @pytest.mark.asyncio
# async def test_delete_bill_wrong_user(db_session):
#     """Test user cannot delete another user's bill"""
#     # User 1
#     user1 = await register_user(db_session, "delbill1@example.com", "DelBill1", "pass123")
#     item1_data = ItemCreate(item_name="Item1", item_unit="KG", unit_price=100, stock_quantity=50)
#     await create_items(db_session, item1_data, user1)
    
#     # User 2
#     user2 = await register_user(db_session, "delbill2@example.com", "DelBill2", "pass123")
    
#     background_tasks = BackgroundTasks()
    
#     # Create bill for user1
#     await create_udhar(
#         db=db_session,
#         customer_name="User1 Bill",
#         item_name="Item1",
#         quantity=5,
#         unit="KG",
#         current_user=user1,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "User1 Bill", user1)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user1)
    
#     # Pay the bill first
#     await pay_bill(db_session, customer.customer_id, user1)
    
#     # User2 tries to delete
#     result = await delete_bill(db_session, bill.bill_id, user2)
    
#     assert result is False  # Not found for user2


# # ============================================
# # EDGE CASES & ADDITIONAL TESTS
# # ============================================
# @pytest.mark.asyncio
# async def test_sync_bill_updates_existing_bill(db_session):
#     """Test that syncing updates existing bill instead of creating new"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar
#     await create_udhar(
#         db=db_session,
#         customer_name="Update Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "Update Customer", user)
    
#     # First sync
#     bill1 = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     # Create another udhar item
#     await create_udhar(
#         db=db_session,
#         customer_name="Update Customer",
#         item_name="Test Product",
#         quantity=3,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     # Second sync (should update existing bill)
#     bill2 = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill1.bill_id == bill2.bill_id
#     assert bill2.udhar_items_total == 800  # 5+3 = 8 * 100


# @pytest.mark.asyncio
# async def test_bill_history_after_payment(db_session):
#     """Test that bill history is preserved after payment"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     # Create udhar
#     await create_udhar(
#         db=db_session,
#         customer_name="History Customer",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "History Customer", user)
#     await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     # Pay bill
#     await pay_bill(db_session, customer.customer_id, user)
    
#     # Bill should have history items (BillItemHistory)
#     # This is tested indirectly through format_bill
#     bills = await get_bills_by_customer(db_session, customer.customer_id, user)
#     assert len(bills) >= 1


# @pytest.mark.asyncio
# async def test_multiple_bills_same_customer(db_session):
#     """Test that a customer can have multiple bills (after payment)"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     customer_name = "Multi Bill Customer"
    
#     # First bill
#     await create_udhar(
#         db=db_session,
#         customer_name=customer_name,
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, customer_name, user)
#     await sync_bill_from_udhar(db_session, customer.customer_id, user)
#     await pay_bill(db_session, customer.customer_id, user)
    
#     # Second bill (new udhar after payment)
#     await create_udhar(
#         db=db_session,
#         customer_name=customer_name,
#         item_name="Test Product",
#         quantity=3,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     bills = await get_bills_by_customer(db_session, customer.customer_id, user)
#     assert len(bills) >= 2


# @pytest.mark.asyncio
# async def test_bill_with_zero_direct_operations(db_session):
#     """Test bill with no direct additions or deductions"""
#     user, item = await create_test_user_and_item(db_session)
#     background_tasks = BackgroundTasks()
    
#     await create_udhar(
#         db=db_session,
#         customer_name="Zero Direct",
#         item_name="Test Product",
#         quantity=5,
#         unit="KG",
#         current_user=user,
#         background_tasks=background_tasks
#     )
    
#     customer = await get_customer_by_name(db_session, "Zero Direct", user)
#     bill = await sync_bill_from_udhar(db_session, customer.customer_id, user)
    
#     assert bill.direct_addition == 0
#     assert bill.direct_deduction == 0
#     assert bill.effective_total == 500

