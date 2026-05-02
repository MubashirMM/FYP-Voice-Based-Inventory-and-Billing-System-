import pytest
from playwright.sync_api import sync_playwright

import pytest

@pytest.fixture(autouse=True)
def setup_database():
    """
    Overrides the global async setup_database fixture.
    This prevents the 'Sync test depending on async fixture' error.
    """
    # If you need to clear the DB for E2E, do it via a standard sync request 
    # or leave empty if your server is already running with a test DB.
    pass
# This ensures the event loop is managed correctly between your 
# async DB tests and these sync browser tests.
@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        # headless=False lets you see the Urdu UI during the test
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        yield context
        browser.close()

@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    # Set timeout for your React login's 2-second delay
    page.set_default_timeout(10000) 
    yield page
    page.close()