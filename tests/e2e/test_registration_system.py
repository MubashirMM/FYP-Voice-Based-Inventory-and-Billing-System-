import pytest
import time
from playwright.sync_api import sync_playwright, expect

@pytest.fixture(scope="module")
def browser_instance():
    # Added slow_mo so you can watch it type
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000) 
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    page = browser_instance.new_page()
    yield page
    page.close()

def test_successful_registration_flow(page):
    page.goto("http://localhost:5173/register")

    unique_id = int(time.time())
    email = f"user_{unique_id}@example.com"
    password = "Password@123"

    page.get_by_placeholder("ای میل درج کریں").fill(email)
    page.get_by_placeholder("یوزر نیم درج کریں").fill(f"user_{unique_id}")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill(password)
    page.get_by_placeholder("پاس ورڈ دوبارہ درج کریں").fill(password)

    page.get_by_role("button", name="رجسٹر کریں").click()

    # FIX: Instead of checking for the text (which disappears quickly), 
    # just wait for the successful redirect.
    try:
        page.wait_for_url("**/voice-samples-form", timeout=10000)
        print(f"\n✅ SUCCESS: Registered {email}")
    except Exception:
        # Only check for error if the redirect didn't happen
        if page.locator(".bg-red-100").is_visible():
            print(f"Error: {page.locator('.bg-red-100').inner_text()}")
        raise