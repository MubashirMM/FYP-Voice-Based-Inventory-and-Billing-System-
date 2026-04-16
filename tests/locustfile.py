import base64
from locust import HttpUser, task, between

class APIUser(HttpUser):
    # Simulated user waits 1-2 seconds between actions
    wait_time = between(1, 2)
    
    user_count = 0

    @task(1)
    def register_user(self):
        APIUser.user_count += 1
        payload = {
            "email": f"perf_test_{APIUser.user_count}@example.com",
            "username": f"user_{APIUser.user_count}",
            "password": "TestPassword123!"
        }
        # Specify the URL of your FastAPI backend
        self.client.post("/auth/register", json=payload)

    @task(3)
    def login_user(self):
        # Use a user that definitely exists in your test database
        self.client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword"}
        )

    @task(1)
    def voice_login_attempt(self):
        # Simulated small audio string
        fake_audio = base64.b64encode(b"fake audio data").decode('utf-8')
        payload = {
            "email": "testuser@example.com",
            "audio_base64": fake_audio
        }
        self.client.post("/auth/voice-login", json=payload)