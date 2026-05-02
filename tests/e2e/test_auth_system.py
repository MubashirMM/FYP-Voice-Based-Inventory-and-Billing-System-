import pytest
import time
from playwright.sync_api import sync_playwright, expect
import re

@pytest.fixture(scope="module")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500) 
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    page = browser_instance.new_page()
    yield page
    page.close()

def test_successful_registration_flow(page):
    """Test complete registration flow"""
    page.goto("http://localhost:5173/register")

    unique_id = int(time.time())
    email = f"user_{unique_id}@example.com"
    password = "Password@123"

    page.get_by_placeholder("ای میل درج کریں").fill(email)
    page.get_by_placeholder("یوزر نیم درج کریں").fill(f"user_{unique_id}")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill(password)
    page.get_by_placeholder("پاس ورڈ دوبارہ درج کریں").fill(password)

    page.get_by_role("button", name="رجسٹر کریں").click()

    try:
        page.wait_for_url("**/voice-samples-form", timeout=10000)
        print(f"\n✅ SUCCESS: Registered {email}")
        return email, password  # Return credentials for login test
    except Exception:
        if page.locator(".bg-red-100").is_visible():
            print(f"Error: {page.locator('.bg-red-100').inner_text()}")
        raise

def test_login_with_newly_registered_user(page):
    """Test login flow with proper waiting"""
    
    # First register a user
    unique_id = int(time.time())
    email = f"login_user_{unique_id}@example.com"
    password = "Password@123"
    
    # Register first
    page.goto("http://localhost:5173/register")
    
    page.get_by_placeholder("ای میل درج کریں").fill(email)
    page.get_by_placeholder("یوزر نیم درج کریں").fill(f"user_{unique_id}")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill(password)
    page.get_by_placeholder("پاس ورڈ دوبارہ درج کریں").fill(password)
    
    page.get_by_role("button", name="رجسٹر کریں").click()
    
    # Wait for registration to complete
    try:
        page.wait_for_url("**/voice-samples-form", timeout=10000)
        print(f"\n✅ Registered: {email}")
    except Exception:
        if page.locator(".bg-red-100").is_visible():
            print(f"Registration error: {page.locator('.bg-red-100').inner_text()}")
        raise
    
    # Now test login
    page.goto("http://localhost:5173/login")
    
    # Wait for page to be fully loaded
    page.wait_for_load_state("networkidle")
    
    # Fill login form
    email_input = page.get_by_placeholder("ای میل درج کریں")
    email_input.fill(email)
    email_input.blur()  # Trigger validation
    
    password_input = page.get_by_placeholder("پاس ورڈ درج کریں")
    password_input.fill(password)
    password_input.blur()
    
    # Click login button
    login_button = page.get_by_role("button", name="لاگ ان کریں")
    login_button.click()
    
    # Wait for API response first (check for success message)
    try:
        # Wait for success message to appear
        success_message = page.locator(".bg-green-100")
        expect(success_message).to_be_visible(timeout=5000)
        print(f"\n✅ Success message visible")
        
        # Wait for success message text
        expect(success_message).to_contain_text("لاگ ان کامیاب")
        print(f"✅ Login successful message confirmed")
        
    except Exception as e:
        print(f"❌ Success message not found: {e}")
        # Check for error message
        if page.locator(".bg-red-100").is_visible():
            error_text = page.locator(".bg-red-100").inner_text()
            print(f"Error message: {error_text}")
        raise
    
    # Now wait for navigation to items page
    try:
        # Wait for URL to change to /items
        page.wait_for_url(lambda url: "/items" in url, timeout=15000)
        
        # Verify we're on items page
        current_url = page.url
        print(f"✅ Navigated to: {current_url}")
        assert "/items" in current_url, f"Expected /items in URL, got {current_url}"
        
        # Wait for items page to load
        page.wait_for_load_state("networkidle")
        
        print(f"✅ SUCCESS: Logged in and redirected to items page")
        
    except Exception as e:
        print(f"❌ Navigation timeout: {e}")
        print(f"Current URL: {page.url}")
        
        # Take screenshot for debugging
        page.screenshot(path="login_failure.png")
        print("Screenshot saved as login_failure.png")
        raise

def test_login_with_invalid_credentials(page):
    """Test login with wrong password"""
    page.goto("http://localhost:5173/login")
    
    page.wait_for_load_state("networkidle")
    
    # Use invalid credentials
    page.get_by_placeholder("ای میل درج کریں").fill("nonexistent@example.com")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill("WrongPassword123!")
    
    page.get_by_role("button", name="لاگ ان کریں").click()
    
    # Wait for error message
    try:
        error_message = page.locator(".bg-red-100")
        expect(error_message).to_be_visible(timeout=5000)
        error_text = error_message.inner_text()
        print(f"\n✅ Expected error shown: {error_text}")
        
        # Verify URL is still /login (didn't redirect)
        assert "/login" in page.url, "Should stay on login page"
        
    except Exception as e:
        print(f"❌ Error message not shown: {e}")
        raise

def test_login_with_empty_fields(page):
    """Test validation with empty fields"""
    page.goto("http://localhost:5173/login")
    
    page.wait_for_load_state("networkidle")
    
    # Click login without filling anything
    page.get_by_role("button", name="لاگ ان کریں").click()
    
    # Check for validation messages
    try:
        # Email validation should appear
        email_error = page.locator("p.text-red-500").first
        expect(email_error).to_be_visible(timeout=3000)
        print(f"\n✅ Email validation shown: {email_error.inner_text()}")
        
        # Should still be on login page
        assert "/login" in page.url
        
    except Exception as e:
        print(f"❌ Validation not working: {e}")
        raise