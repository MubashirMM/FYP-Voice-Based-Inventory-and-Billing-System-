# locust_udhar_items_test.py
from locust import FastHttpUser, task, between, SequentialTaskSet
import random
from urllib.parse import quote

TEST_EMAIL_DOMAIN = "@test.com"
TEST_PASSWORD = "Test@123456"

class UdharItemsUser(SequentialTaskSet):
    """
    Udhar Items (Credit Items) API Performance Test User
    Tests all CRUD operations for credit items
    """
    
    def on_start(self):
        """Setup: Register and login user, create test data"""
        self.access_token = None
        self.test_id = random.randint(10000, 99999)
        self.user_email = f"test_user_{self.test_id}{TEST_EMAIL_DOMAIN}"
        self.username = f"user_{self.test_id}"
        self.password = TEST_PASSWORD
        self.created_udhar_item_ids = []
        self.created_customer_names = []
        self.test_items = []
        self.test_customers = ["Ahmed", "Raza", "Fatima", "Ali", "Zainab"]
        
        self.register_user()
        self.login_user()
        self.create_test_items()
        self.create_initial_udhar_items()
    
    def register_user(self):
        """Register a new user"""
        with self.client.post(
            "/auth/register",
            json={
                "email": self.user_email,
                "username": self.username,
                "password": self.password
            },
            catch_response=True,
            name="/auth/register"
        ) as response:
            if response.status_code in [201, 400]:
                response.success()
            else:
                response.failure(f"Register failed: {response.status_code}")
    
    def login_user(self):
        """Login and get access token"""
        with self.client.post(
            "/auth/login",
            data={
                "username": self.user_email,
                "password": self.password
            },
            catch_response=True,
            name="/auth/login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    def create_test_items(self):
        """Create test items for udhar transactions"""
        test_items_data = [
            {"item_name": "Rice Basmati", "item_unit": "kg", "unit_price": 180, "stock_quantity": 500},
            {"item_name": "Sugar White", "item_unit": "kg", "unit_price": 120, "stock_quantity": 400},
            {"item_name": "Flour", "item_unit": "bag", "unit_price": 850, "stock_quantity": 100},
            {"item_name": "Milk", "item_unit": "liter", "unit_price": 150, "stock_quantity": 200},
            {"item_name": "Tea", "item_unit": "kg", "unit_price": 500, "stock_quantity": 50}
        ]
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        for item in test_items_data:
            with self.client.post(
                "/items",
                json=item,
                headers=headers,
                catch_response=True,
                name="/items POST (setup)"
            ) as response:
                if response.status_code == 201:
                    data = response.json()
                    self.test_items.append(data)
                    response.success()
                else:
                    response.failure(f"Failed to create test item: {item['item_name']}")
    
    def create_initial_udhar_items(self):
        """Create initial udhar items for testing"""
        if not self.test_items or not self.test_customers:
            return
        
        for i in range(min(3, len(self.test_items))):
            customer = random.choice(self.test_customers)
            item = self.test_items[i]
            quantity = random.randint(1, 10)
            unit = item.get("item_unit", "kg")
            
            udhar_data = {
                "customer_name": customer,
                "item_name": item["item_name"],
                "quantity": quantity,
                "unit": unit
            }
            
            self.create_single_udhar_item(udhar_data)
    
    def create_single_udhar_item(self, udhar_data):
        """Helper method to create a single udhar item"""
        if not self.access_token:
            return None
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        customer_name = udhar_data.get("customer_name")
        
        with self.client.post(
            "/udhar-items/",
            json=udhar_data,
            headers=headers,
            catch_response=True,
            name="/udhar-items POST"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                item_id = data.get("udharitem_id")
                if item_id:
                    self.created_udhar_item_ids.append(item_id)
                    if customer_name and customer_name not in self.created_customer_names:
                        self.created_customer_names.append(customer_name)
                response.success()
                return data
            else:
                response.failure(f"Create udhar item failed: {response.status_code}")
                return None
    
    # ============================
    # TASKS - Weighted by importance
    # ============================
    
    @task(12)
    def get_all_udhar_items(self):
        """GET /udhar-items/ - Retrieve all udhar items (most frequent)"""
        if not self.access_token:
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.get(
            "/udhar-items/",
            headers=headers,
            catch_response=True,
            name="/udhar-items GET all"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Response should be a list")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Get udhar items failed: {response.status_code}")
    
    @task(10)
    def get_udhar_items_by_customer(self):
        """GET /udhar-items/customer/{customer_name} - Get items by customer"""
        if not self.access_token or not self.created_customer_names:
            return
            
        customer_name = random.choice(self.created_customer_names)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        encoded_customer = quote(customer_name, safe='')
        
        with self.client.get(
            f"/udhar-items/customer/{encoded_customer}",
            headers=headers,
            catch_response=True,
            name="/udhar-items/customer/{name} GET"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Response should be a list")
                except:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Get by customer failed: {response.status_code}")
    
    @task(8)
    def get_single_udhar_item(self):
        """GET /udhar-items/{item_id} - Get specific udhar item"""
        if not self.access_token or not self.created_udhar_item_ids:
            return
            
        item_id = random.choice(self.created_udhar_item_ids)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.get(
            f"/udhar-items/{item_id}",
            headers=headers,
            catch_response=True,
            name="/udhar-items/{id} GET"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    required_fields = ["udharitem_id", "customer_name", "item_name", "quantity", "total_amount"]
                    if all(field in data for field in required_fields):
                        response.success()
                    else:
                        response.failure("Missing required fields")
                except:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure(f"Udhar item {item_id} not found")
            else:
                response.failure(f"Get udhar item failed: {response.status_code}")
    
    @task(7)
    def search_udhar_items(self):
        """GET /udhar-items/search/?keyword={keyword} - Search by item name"""
        if not self.access_token:
            return
            
        search_keywords = ["Rice", "Sugar", "Flour", "Milk", "Tea"]
        keyword = random.choice(search_keywords)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.get(
            "/udhar-items/search/",
            params={"keyword": keyword},
            headers=headers,
            catch_response=True,
            name="/udhar-items/search GET"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")
    
    @task(6)
    def create_new_udhar_item(self):
        """POST /udhar-items/ - Create a new udhar item"""
        if not self.access_token or not self.test_items or not self.test_customers:
            return
            
        customer = random.choice(self.test_customers)
        item = random.choice(self.test_items)
        
        quantity = random.randint(1, 5)
        unit = item.get("item_unit", "kg")
        
        udhar_data = {
            "customer_name": customer,
            "item_name": item["item_name"],
            "quantity": quantity,
            "unit": unit
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.post(
            "/udhar-items/",
            json=udhar_data,
            headers=headers,
            catch_response=True,
            name="/udhar-items POST"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "udharitem_id" in data:
                    self.created_udhar_item_ids.append(data["udharitem_id"])
                    if customer not in self.created_customer_names:
                        self.created_customer_names.append(customer)
                response.success()
            elif response.status_code == 400:
                response.success()
            else:
                response.failure(f"Create udhar item failed: {response.status_code}")
    
    @task(5)
    def update_udhar_item(self):
        """PUT /udhar-items/{item_id} - Update an existing udhar item"""
        if not self.access_token or len(self.created_udhar_item_ids) < 2:
            return
            
        item_id = random.choice(self.created_udhar_item_ids)
        item = random.choice(self.test_items)
        quantity = random.randint(1, 3)
        
        update_data = {
            "customer_name": random.choice(self.test_customers),
            "item_name": item["item_name"],
            "quantity": quantity,
            "unit": item.get("item_unit", "kg")
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.put(
            f"/udhar-items/{item_id}",
            json=update_data,
            headers=headers,
            catch_response=True,
            name="/udhar-items/{id} PUT"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                response.success()
            elif response.status_code == 404:
                response.failure(f"Udhar item {item_id} not found for update")
            else:
                response.failure(f"Update failed: {response.status_code}")
    
    @task(3)
    def delete_udhar_item(self):
        """DELETE /udhar-items/{item_id} - Delete an udhar item"""
        if not self.access_token or len(self.created_udhar_item_ids) < 2:
            return
            
        if len(self.created_udhar_item_ids) <= 1:
            return
            
        item_id = random.choice(self.created_udhar_item_ids)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.delete(
            f"/udhar-items/{item_id}",
            headers=headers,
            catch_response=True,
            name="/udhar-items/{id} DELETE"
        ) as response:
            if response.status_code == 200:
                if item_id in self.created_udhar_item_ids:
                    self.created_udhar_item_ids.remove(item_id)
                response.success()
            elif response.status_code == 404:
                if item_id in self.created_udhar_item_ids:
                    self.created_udhar_item_ids.remove(item_id)
                response.success()
            else:
                response.failure(f"Delete failed: {response.status_code}")
    
    @task(2)
    def test_insufficient_stock(self):
        """Test handling of insufficient stock"""
        if not self.access_token or not self.test_items:
            return
            
        customer = random.choice(self.test_customers)
        
        item = self.test_items[0]
        current_stock = item.get("stock_quantity", 100)
        requested_quantity = current_stock + random.randint(10, 50)
        
        udhar_data = {
            "customer_name": customer,
            "item_name": item["item_name"],
            "quantity": requested_quantity,
            "unit": item.get("item_unit", "kg")
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.post(
            "/udhar-items/",
            json=udhar_data,
            headers=headers,
            catch_response=True,
            name="/udhar-items POST (stock test)"
        ) as response:
            if response.status_code == 400:
                response.success()
            elif response.status_code == 200:
                response.failure(f"Created with insufficient stock! Requested: {requested_quantity}, Available: {current_stock}")
            else:
                response.success()
    
    def on_stop(self):
        """Cleanup: Delete all created udhar items"""
        if self.access_token and self.created_udhar_item_ids:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            for item_id in self.created_udhar_item_ids[:]:
                with self.client.delete(
                    f"/udhar-items/{item_id}",
                    headers=headers,
                    name="/udhar-items DELETE (cleanup)",
                    catch_response=True
                ) as response:
                    pass


class UdharItemsAPIUser(FastHttpUser):
    """Main Locust user class for Udhar Items API"""
    wait_time = between(0.5, 2)
    host = "http://localhost:8000"
    tasks = [UdharItemsUser]