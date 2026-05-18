# locust_items_test.py
from locust import FastHttpUser, task, between, SequentialTaskSet
import random
import json

TEST_EMAIL_DOMAIN = "@test.com"
TEST_PASSWORD = "Test@123456"

class ItemsUser(SequentialTaskSet):
    """
    Items API Performance Test User
    Tests all CRUD operations for items
    """
    
    def on_start(self):
        """Setup: Register and login user, create test items"""
        self.access_token = None
        self.test_id = random.randint(10000, 99999)
        self.user_email = f"test_user_{self.test_id}{TEST_EMAIL_DOMAIN}"
        self.username = f"user_{self.test_id}"
        self.password = TEST_PASSWORD
        self.created_item_ids = []
        self.current_search_keywords = ["چاول", "شکر", "آٹا", "دودھ"]
        
        self.register_user()
        self.login_user()
        self.create_initial_items()
    
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
    
    def create_initial_items(self):
        """Create initial items for testing"""
        test_items = [
            {"item_name": "چاول باسمتی", "item_unit": "کلو", "unit_price": 180, "stock_quantity": 100},
            {"item_name": "شکر سفید", "item_unit": "کلو", "unit_price": 120, "stock_quantity": 200},
            {"item_name": "آٹا", "item_unit": "بوری", "unit_price": 850, "stock_quantity": 50},
            {"item_name": "دودھ", "item_unit": "لیٹر", "unit_price": 150, "stock_quantity": 80},
            {"item_name": "چاول باسمتی", "item_unit": "کلو", "unit_price": 180, "stock_quantity": 100}
        ]
        
        for item in test_items[:3]:  # Create first 3 items
            self.create_single_item(item)
    
    def create_single_item(self, item_data):
        """Helper method to create a single item"""
        if not self.access_token:
            return None
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.post(
            "/items",
            json=item_data,
            headers=headers,
            catch_response=True,
            name="/items POST"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                item_id = data.get("item_id")
                if item_id:
                    self.created_item_ids.append(item_id)
                response.success()
                return data
            else:
                response.failure(f"Create item failed: {response.status_code}")
                return None
    
    # ============================
    # TASKS - Weighted by importance
    # ============================
    
    @task(10)
    def get_all_items(self):
        """GET /items - Retrieve all items (most frequent operation)"""
        if not self.access_token:
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.get(
            "/items",
            headers=headers,
            catch_response=True,
            name="/items GET"
        ) as response:
            if response.status_code == 200:
                # Validate response is list
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Response should be a list")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Get items failed: {response.status_code}")
    
    @task(8)
    def search_items(self):
        """GET /items/search - Search items by keywords"""
        if not self.access_token:
            return
            
        keyword = random.choice(self.current_search_keywords)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.get(
            "/items/search",
            params={"keywords": keyword},
            headers=headers,
            catch_response=True,
            name="/items/search"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # No results found - still acceptable
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")
    
    @task(6)
    def get_single_item(self):
        """GET /items/{item_id} - Get specific item"""
        if not self.access_token or not self.created_item_ids:
            return
            
        item_id = random.choice(self.created_item_ids)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.get(
            f"/items/{item_id}",
            headers=headers,
            catch_response=True,
            name="/items/{item_id} GET"
        ) as response:
            if response.status_code == 200:
                # Validate response structure
                try:
                    data = response.json()
                    required_fields = ["item_id", "item_name", "item_unit", "unit_price", "stock_quantity"]
                    if all(field in data for field in required_fields):
                        response.success()
                    else:
                        response.failure("Missing required fields")
                except:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Item not found")
            else:
                response.failure(f"Get item failed: {response.status_code}")
    
    @task(5)
    def create_new_item(self):
        """POST /items - Create a new item"""
        if not self.access_token:
            return
            
        random_suffix = random.randint(1, 10000)
        new_item = {
            "item_name": f"ٹیسٹ آئٹم {random_suffix}",
            "item_unit": random.choice(["کلو", "بوری", "لیٹر", "پیسیز"]),
            "unit_price": random.randint(50, 500),
            "stock_quantity": random.randint(0, 500)
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.post(
            "/items",
            json=new_item,
            headers=headers,
            catch_response=True,
            name="/items POST"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                if "item_id" in data:
                    self.created_item_ids.append(data["item_id"])
                response.success()
            elif response.status_code == 400:
                # Duplicate name might occur - still acceptable
                response.success()
            else:
                response.failure(f"Create failed: {response.status_code}")
    
    @task(4)
    def update_item(self):
        """PATCH /items/{item_id} - Update an existing item"""
        if not self.access_token or not self.created_item_ids:
            return
            
        item_id = random.choice(self.created_item_ids)
        update_data = {
            "unit_price": random.randint(100, 1000),
            "stock_quantity": random.randint(0, 500)
        }
        
        # Occasionally update name
        if random.random() > 0.7:
            update_data["item_name"] = f"اپڈیٹڈ آئٹم {random.randint(1, 100)}"
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.patch(
            f"/items/{item_id}",
            json=update_data,
            headers=headers,
            catch_response=True,
            name="/items/{item_id} PATCH"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Item not found for update")
            else:
                response.failure(f"Update failed: {response.status_code}")
    
    @task(2)
    def delete_item(self):
        """DELETE /items/{item_id} - Delete an item (less frequent)"""
        if not self.access_token or len(self.created_item_ids) < 3:
            return
            
        # Don't delete all items, leave at least 2
        if len(self.created_item_ids) <= 2:
            return
            
        item_id = random.choice(self.created_item_ids)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.delete(
            f"/items/{item_id}",
            headers=headers,
            catch_response=True,
            name="/items/{item_id} DELETE"
        ) as response:
            if response.status_code == 200:
                # Remove from our tracking list
                if item_id in self.created_item_ids:
                    self.created_item_ids.remove(item_id)
                response.success()
            elif response.status_code == 404:
                # Already deleted - acceptable
                if item_id in self.created_item_ids:
                    self.created_item_ids.remove(item_id)
                response.success()
            else:
                response.failure(f"Delete failed: {response.status_code}")
    
    @task(1)
    def create_duplicate_item(self):
        """Test duplicate item handling"""
        if not self.access_token or not self.created_item_ids:
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # First get an existing item
        with self.client.get(
            f"/items/{self.created_item_ids[0]}",
            headers=headers,
            catch_response=True,
            name="/items GET (for duplicate test)"
        ) as response:
            if response.status_code == 200:
                existing_item = response.json()
                duplicate_item = {
                    "item_name": existing_item["item_name"],
                    "item_unit": existing_item["item_unit"] + "_copy",
                    "unit_price": existing_item["unit_price"],
                    "stock_quantity": 10
                }
                
                # Try to create duplicate
                with self.client.post(
                    "/items",
                    json=duplicate_item,
                    headers=headers,
                    catch_response=True,
                    name="/items POST (duplicate test)"
                ) as dup_response:
                    if dup_response.status_code == 400:
                        # Expected behavior - duplicate prevented
                        dup_response.success()
                    elif dup_response.status_code == 201:
                        # Should not happen but if it does, track it
                        dup_response.failure("Duplicate item was created!")
                    else:
                        dup_response.failure(f"Unexpected status: {dup_response.status_code}")
    
    def on_stop(self):
        """Cleanup: Delete all created items"""
        if self.access_token and self.created_item_ids:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            for item_id in self.created_item_ids[:]:
                with self.client.delete(
                    f"/items/{item_id}",
                    headers=headers,
                    name="/items DELETE (cleanup)",
                    catch_response=True
                ) as response:
                    pass


class ItemsAPIUser(FastHttpUser):
    """Main Locust user class for Items API"""
    wait_time = between(0.5, 2)  # Wait between 0.5 to 2 seconds between tasks
    host = "http://localhost:8000"  # Change to your actual host
    tasks = [ItemsUser]