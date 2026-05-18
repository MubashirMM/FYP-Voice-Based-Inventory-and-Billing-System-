from locust import FastHttpUser, task, between
import random

TEST_EMAIL_DOMAIN = "@test.com"
TEST_PASSWORD = "Test@123456"

class APIUser(FastHttpUser):
    host = "http://localhost:8000"
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.access_token = None
        self.test_id = random.randint(10000, 99999)
        self.user_email = f"test_user_{self.test_id}{TEST_EMAIL_DOMAIN}"
        self.username = f"user_{self.test_id}"
        self.password = TEST_PASSWORD
        
        self.register_user()
        self.login_user()
    
    def register_user(self):
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
    
    @task(3)
    def get_me(self):
        if not self.access_token:
            return
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/auth/me",
            headers=headers,
            catch_response=True,
            name="/auth/me"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get me failed: {response.status_code}")
    
    @task(2)
    def update_profile(self):
        if not self.access_token:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        update_data = {
            "username": f"updated_user_{self.test_id}_{random.randint(1, 100)}"
        }
        
        with self.client.patch(
            "/auth/profile",
            json=update_data,
            headers=headers,
            catch_response=True,
            name="/auth/profile"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Update failed: {response.status_code} - {response.text}")
    
    @task(5)
    def forgot_password(self):
        with self.client.post(
            "/auth/forgot-password",
            params={"email": self.user_email},
            catch_response=True,
            name="/auth/forgot-password"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Forgot password failed: {response.status_code}")
    
    @task(1)
    def reset_password(self):
        with self.client.post(
            "/auth/reset-password-confirm",
            json={
                "email": self.user_email,
                "reset_code": "VBUGIMS-123456",
                "new_password": "NewTest@123456",
                "confirm_password": "NewTest@123456"
            },
            catch_response=True,
            name="/auth/reset-password-confirm"
        ) as response:
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Reset failed: {response.status_code}")
    
    @task(1)
    def get_all_users(self):
        if not self.access_token:
            return
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/auth/users",
            headers=headers,
            catch_response=True,
            name="/auth/users"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.success()
    
    def on_stop(self):
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            with self.client.delete(
                "/auth/profile",
                headers=headers,
                name="/auth/profile DELETE",
                catch_response=True
            ) as response:
                pass