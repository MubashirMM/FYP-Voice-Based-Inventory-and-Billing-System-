"""
API Test Suite for VBUGIMS (Voice-Based Inventory and General Item Management System)
Run this script to test all API endpoints manually

Test Cases Summary:
==================
AUTH TESTS:
- test_register_user: Register new user
- test_login_user: Login with email/password
- test_get_users: Get all users (no auth required)
- test_forgot_password: Request password reset

SHOP TESTS:
- test_create_shop: Create new shop
- test_get_shops: Get all shops for user
- test_get_shop: Get single shop by ID
- test_update_shop: Update shop details
- test_delete_shop: Delete shop

ITEM TESTS:
- test_create_item: Create new item
- test_get_items: Get all items
- test_get_item: Get single item
- test_search_items: Search items by keywords
- test_update_item: Update item details
- test_delete_item: Delete item

CUSTOMER TESTS:
- test_create_customer: Create new customer
- test_get_customers: Get all customers
- test_get_customer: Get single customer
- test_search_customer: Search customer by name
- test_delete_customer: Delete customer

BILL ITEM TESTS:
- test_create_bill_item: Create bill item
- test_get_bill_items: Get all bill items

BILL TESTS:
- test_get_bills: Get all bills
- test_get_customer_bills: Get customer bills
- test_pay_bill: Pay customer bill

SALES TESTS:
- test_get_sales: Get all sales
- test_get_sales_by_item: Get sales by item ID

UDHAAR TESTS:
- test_get_udhars: Get all udhars
- test_get_udhar_by_customer: Get udhar for customer
- test_direct_addition: Add direct addition
- test_direct_deduction: Add direct deduction
- test_udhar_summary: Get udhar summary

UDHAAR ITEM TESTS:
- test_create_udhar_item: Create udhar item
- test_get_udhar_items: Get all udhar items
"""

import requests
import json
import random

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        self.test_email = f"apitest{random.randint(1000,9999)}@example.com"
        
        # Store created IDs for testing
        self.shop_ids = []
        self.item_ids = []
        self.customer_ids = []
        
    def print_response(self, test_name: str, response: requests.Response):
        """Print test results in a formatted way"""
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except:
            print(f"Response: {response.text}")
        
    # ==================== AUTH TESTS ====================
    
    def test_register_and_login(self):
        """Register a new user and login to get token"""
        print("\n" + "="*80)
        print("STEP 1: Register and Login to get token")
        print("="*80)
        
        # Register
        url = f"{self.base_url}/auth/register"
        payload = {
            "email": self.test_email,
            "username": "apitest",
            "password": "testpass123",
            "voice_samples": []
        }
        response = requests.post(url, json=payload)
        self.print_response("Register User", response)
        
        # Login with EMAIL as username (this is how OAuth2PasswordRequestForm works)
        url = f"{self.base_url}/auth/login"
        data = {"username": self.test_email, "password": "testpass123"}
        response = requests.post(url, data=data)
        self.print_response("Login User", response)
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            print(f"\n>>> TOKEN OBTAINED: {self.token[:50]}...")
            return True
        return False
    
    def test_get_users(self):
        """Test get all users"""
        url = f"{self.base_url}/auth/users"
        response = requests.get(url)
        self.print_response("Get All Users", response)
        return response
    
    def test_forgot_password(self):
        """Test forgot password"""
        url = f"{self.base_url}/auth/forgot-password"
        params = {"email": self.test_email}
        response = requests.post(url, params=params)
        self.print_response("Forgot Password", response)
        return response
    
    # ==================== SHOP TESTS ====================
    
    def test_create_shop(self, name: str = None):
        """Test create shop"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        shop_name = name or f"Test Shop {random.randint(100,999)}"
        url = f"{self.base_url}/shops/"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "shop_name": shop_name,
            "address": "123 Test Street"
        }
        response = requests.post(url, json=payload, headers=headers)
        self.print_response("Create Shop", response)
        
        # Store created shop ID
        if response.status_code == 201:
            try:
                self.shop_ids.append(response.json().get("shop_id"))
            except:
                pass
        return response
    
    def test_get_shops(self):
        """Test get all shops"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/shops/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Shops", response)
        return response
    
    def test_get_shop(self, shop_id: int = None):
        """Test get single shop"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        # Use first created shop ID or default
        test_id = shop_id if shop_id else (self.shop_ids[0] if self.shop_ids else 1)
            
        url = f"{self.base_url}/shops/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Get Shop {test_id}", response)
        return response
    
    def test_update_shop(self, shop_id: int = None):
        """Test update shop"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        test_id = shop_id if shop_id else (self.shop_ids[0] if self.shop_ids else 1)
        url = f"{self.base_url}/shops/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "shop_name": "Updated Shop Name",
            "address": "456 New Street"
        }
        response = requests.patch(url, json=payload, headers=headers)
        self.print_response(f"Update Shop {test_id}", response)
        return response
    
    def test_delete_shop(self, shop_id: int = None):
        """Test delete shop"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        test_id = shop_id if shop_id else (self.shop_ids[0] if self.shop_ids else 1)
        url = f"{self.base_url}/shops/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.delete(url, headers=headers)
        self.print_response(f"Delete Shop {test_id}", response)
        return response
    
    # ==================== ITEM TESTS ====================
    
    def test_create_item(self, name: str = None):
        """Test create item"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        item_name = name or f"Test Item {random.randint(100,999)}"
        url = f"{self.base_url}/items/"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "item_name": item_name,
            "item_unit": "عدد",
            "unit_price": 100.0,
            "stock_quantity": 50.0
        }
        response = requests.post(url, json=payload, headers=headers)
        self.print_response("Create Item", response)
        
        # Store created item ID
        if response.status_code == 200:
            try:
                self.item_ids.append(response.json().get("item_id"))
            except:
                pass
        return response
    
    def test_get_items(self):
        """Test get all items"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/items/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Items", response)
        return response
    
    def test_get_item(self, item_id: int = None):
        """Test get single item"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = item_id if item_id else (self.item_ids[0] if self.item_ids else 1)
            
        url = f"{self.base_url}/items/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Get Item {test_id}", response)
        return response
    
    def test_search_items(self, keywords: str = "Test"):
        """Test search items"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/items/search"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"keywords": keywords}
        response = requests.get(url, headers=headers, params=params)
        self.print_response(f"Search Items: {keywords}", response)
        return response
    
    def test_update_item(self, item_id: int = None):
        """Test update item"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = item_id if item_id else (self.item_ids[0] if self.item_ids else 1)
            
        url = f"{self.base_url}/items/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "item_name": "Updated Item",
            "unit_price": 150.0
        }
        response = requests.patch(url, json=payload, headers=headers)
        self.print_response(f"Update Item {test_id}", response)
        return response
    
    def test_delete_item(self, item_id: int = None):
        """Test delete item"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = item_id if item_id else (self.item_ids[0] if self.item_ids else 1)
            
        url = f"{self.base_url}/items/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.delete(url, headers=headers)
        self.print_response(f"Delete Item {test_id}", response)
        return response
    
    # ==================== CUSTOMER TESTS ====================
    
    def test_create_customer(self, name: str = None):
        """Test create customer"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        customer_name = name or f"Test Customer {random.randint(100,999)}"
            
        url = f"{self.base_url}/customers/"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "customer_name": customer_name
        }
        response = requests.post(url, json=payload, headers=headers)
        self.print_response("Create Customer", response)
        
        # Store created customer ID
        if response.status_code == 201:
            try:
                self.customer_ids.append(response.json().get("customer_id"))
            except:
                pass
        return response
    
    def test_get_customers(self):
        """Test get all customers"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/customers/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Customers", response)
        return response
    
    def test_get_customer(self, customer_id: int = None):
        """Test get single customer"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/customers/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Get Customer {test_id}", response)
        return response
    
    def test_search_customer(self, customer_name: str = "Test"):
        """Test search customer"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/customers/search"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"customer_name": customer_name}
        response = requests.get(url, headers=headers, params=params)
        self.print_response(f"Search Customer: {customer_name}", response)
        return response
    
    def test_delete_customer(self, customer_id: int = None):
        """Test delete customer"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/customers/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.delete(url, headers=headers)
        self.print_response(f"Delete Customer {test_id}", response)
        return response
    
    # ==================== BILL ITEM TESTS ====================
    
    def test_create_bill_item(self, item_id: int = None, quantity: float = 5, unit_price: float = 100.0):
        """Test create bill item"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_item_id = item_id if item_id else (self.item_ids[0] if self.item_ids else 1)
            
        url = f"{self.base_url}/billitems/"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "item_id": test_item_id,
            "item_name": "Test Item",
            "quantity": quantity,
            "requested_unit": "عدد",
            "unit_price": unit_price
        }
        response = requests.post(url, json=payload, headers=headers)
        self.print_response("Create Bill Item", response)
        return response
    
    def test_get_bill_items(self):
        """Test get all bill items"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/billitems/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Bill Items", response)
        return response
    
    # ==================== BILL TESTS ====================
    
    def test_get_bills(self):
        """Test get all bills"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/bills/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Bills", response)
        return response
    
    def test_get_customer_bills(self, customer_id: int = None):
        """Test get customer bills"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/bills/customer/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Get Customer {test_id} Bills", response)
        return response
    
    def test_pay_bill(self, customer_id: int = None):
        """Test pay customer bill"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/bills/customer/{test_id}/pay"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.put(url, headers=headers)
        self.print_response(f"Pay Customer {test_id} Bill", response)
        return response
    
    # ==================== SALES TESTS ====================
    
    def test_get_sales(self):
        """Test get all sales"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/sales/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Sales", response)
        return response
    
    def test_get_sales_by_item(self, item_id: int = None):
        """Test get sales by item"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = item_id if item_id else (self.item_ids[0] if self.item_ids else 1)
            
        url = f"{self.base_url}/sales/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Get Sales for Item {test_id}", response)
        return response
    
    # ==================== UDHAAR TESTS ====================
    
    def test_get_udhars(self):
        """Test get all udhars"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/udhars/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Udhars", response)
        return response
    
    def test_get_udhar_by_customer(self, customer_id: int = None):
        """Test get udhar by customer"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/udhars/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Get Udhar for Customer {test_id}", response)
        return response
    
    def test_direct_addition(self, customer_id: int = None, amount: float = 500.0):
        """Test direct addition to udhar"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/udhars/{test_id}/direct-addition"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"amount": amount}
        response = requests.put(url, headers=headers, params=params)
        self.print_response(f"Direct Addition for Customer {test_id}", response)
        return response
    
    def test_direct_deduction(self, customer_id: int = None, amount: float = 100.0):
        """Test direct deduction from udhar"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/udhars/{test_id}/direct-deduction"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"amount": amount}
        response = requests.put(url, headers=headers, params=params)
        self.print_response(f"Direct Deduction for Customer {test_id}", response)
        return response
    
    def test_udhar_summary(self, customer_id: int = None):
        """Test get udhar summary"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
            
        url = f"{self.base_url}/udhars/{test_id}/summary"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response(f"Udhar Summary for Customer {test_id}", response)
        return response
    
    # ==================== UDHAAR ITEM TESTS ====================
    
    def test_create_udhar_item(self, customer_id: int = None):
        """Test create udhar item"""
        if not self.token:
            print("No token! Please login first")
            return None
        
        test_customer_id = customer_id if customer_id else (self.customer_ids[0] if self.customer_ids else 1)
        test_item_id = self.item_ids[0] if self.item_ids else 1
            
        url = f"{self.base_url}/udhar-items/"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "customer_id": test_customer_id,
            "item_id": test_item_id,
            "quantity": 2,
            "unit": "عدد",
            "date_": "2026-02-22"
        }
        response = requests.post(url, json=payload, headers=headers)
        self.print_response("Create Udhar Item", response)
        return response
    
    def test_get_udhar_items(self):
        """Test get all udhar items"""
        if not self.token:
            print("No token! Please login first")
            return None
            
        url = f"{self.base_url}/udhar-items/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        self.print_response("Get All Udhar Items", response)
        return response
    
    # ==================== RUN ALL TESTS ====================
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        
        print("\n" + "="*80)
        print("STARTING API TEST SUITE FOR VBUGIMS")
        print("="*80)
        
        # Step 1: Register and Login
        if not self.test_register_and_login():
            print("FAILED TO LOGIN! Cannot proceed with tests.")
            return
        
        # Auth Tests
        print("\n\n" + "#"*80)
        print("# AUTH TESTS")
        print("#"*80)
        
        self.test_get_users()
        self.test_forgot_password()
        
        # Shop Tests
        print("\n\n" + "#"*80)
        print("# SHOP TESTS")
        print("#"*80)
        
        self.test_create_shop()
        self.test_get_shops()
        self.test_get_shop()  # Uses first created shop ID
        self.test_update_shop()  # Uses first created shop ID
        self.test_get_shops()
        # self.test_delete_shop()  # Uncomment to test delete
        
        # Item Tests
        print("\n\n" + "#"*80)
        print("# ITEM TESTS")
        print("#"*80)
        
        self.test_create_item()
        self.test_get_items()
        self.test_get_item()  # Uses first created item ID
        self.test_search_items("Test")
        self.test_update_item()  # Uses first created item ID
        self.test_get_items()
        # self.test_delete_item()  # Uncomment to test delete
        
        # Customer Tests
        print("\n\n" + "#"*80)
        print("# CUSTOMER TESTS")
        print("#"*80)
        
        self.test_create_customer()
        self.test_get_customers()
        self.test_get_customer()  # Uses first created customer ID
        self.test_search_customer("Test")
        # self.test_delete_customer()  # Uncomment to test delete
        
        # Bill Item Tests
        print("\n\n" + "#"*80)
        print("# BILL ITEM TESTS")
        print("#"*80)
        
        self.test_create_bill_item()  # Uses first created item ID
        self.test_get_bill_items()
        
        # Bill Tests
        print("\n\n" + "#"*80)
        print("# BILL TESTS")
        print("#"*80)
        
        self.test_get_bills()
        self.test_get_customer_bills()  # Uses first created customer ID
        # self.test_pay_bill()  # Uncomment to test payment
        
        # Sales Tests
        print("\n\n" + "#"*80)
        print("# SALES TESTS")
        print("#"*80)
        
        self.test_get_sales()
        self.test_get_sales_by_item()  # Uses first created item ID
        
        # Udhar Tests
        print("\n\n" + "#"*80)
        print("# UDHAAR TESTS")
        print("#"*80)
        
        self.test_get_udhars()
        self.test_get_udhar_by_customer()  # Uses first created customer ID
        # self.test_direct_addition()  # Uncomment to test
        # self.test_direct_deduction()  # Uncomment to test
        # self.test_udhar_summary()  # Uncomment to test
        
        # Udhar Item Tests
        print("\n\n" + "#"*80)
        print("# UDHAAR ITEM TESTS")
        print("#"*80)
        
        self.test_create_udhar_item()  # Uses first created customer & item ID
        self.test_get_udhar_items()
        
        print("\n\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
