# import pytest
# from playwright.sync_api import sync_playwright, expect

# @pytest.fixture(scope="module")
# def browser_instance():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False, slow_mo=1500)
#         yield browser
#         browser.close()

# @pytest.fixture(scope="function")
# def page(browser_instance):
#     return browser_instance.new_page()
# def test_successful_login_flow(page):
#     page.goto("http://localhost:5173/login")

#     # Use the email you know exists in your DB
#     page.get_by_placeholder("example@email.com").fill("32304mubashir@gmail.com") 
#     page.get_by_placeholder("پاس ورڈ درج کریں").fill("Abcd1234!") 

#     page.get_by_role("button", name="لاگ ان کریں").click()

#     # FIX: Use a more flexible wait. 
#     # This waits for the 'items' to appear in the URL anywhere.
#     page.wait_for_url(lambda url: "items" in url.lower(), timeout=15000)
    
#     # Optional: Verify a piece of text that ONLY exists on the dashboard/items page
#     # expect(page.get_by_text("Items List")).to_be_visible()

import pytest
from playwright.sync_api import sync_playwright, expect

@pytest.fixture(scope="module")
def browser_instance():
    with sync_playwright() as p:
        # Changed from p.chromium to p.firefox
        browser = p.firefox.launch(headless=False, slow_mo=1500)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    # Contexts are better for clean state, but this works with your flow
    context = browser_instance.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_successful_login_flow(page):
    page.goto("http://localhost:5173/login")

    # Your existing logic
    page.get_by_placeholder("example@email.com").fill("32304mubashir@gmail.com") 
    page.get_by_placeholder("پاس ورڈ درج کریں").fill("Abcd1234!") 

    page.get_by_role("button", name="لاگ ان کریں").click()

    # Wait for navigation
    page.wait_for_url(lambda url: "items" in url.lower(), timeout=15000)
    
    # Final check
    expect(page).to_have_url(lambda url: "items" in url.lower())