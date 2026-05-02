import pytest
from playwright.sync_api import sync_playwright, expect
import uuid
import time

@pytest.fixture(scope="module")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def authenticated_page(browser_instance):
    """Create authenticated page for a specific user"""
    context = browser_instance.new_context()
    page = context.new_page()
    
    # Login with the specified user
    page.goto("http://localhost:5173/login")
    page.get_by_placeholder("ای میل درج کریں").fill("32304mubashir@gmail.com")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill("Pass1234!")
    page.get_by_role("button", name="لاگ ان کریں").click()
    
    # Wait for login to complete
    page.wait_for_url(lambda url: "items" in url.lower() or "dashboard" in url.lower(), timeout=15000)
    
    yield page
    context.close()

@pytest.fixture(scope="function")
def page_with_items(authenticated_page):
    """Ensure we're on items page"""
    page = authenticated_page
    
    # Navigate to items page
    if "/items" not in page.url:
        page.goto("http://localhost:5173/items")
    
    page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
    
    yield page

@pytest.fixture(scope="function")
def page_with_udhaar(authenticated_page):
    """Navigate to udhaar items page"""
    page = authenticated_page
    
    # Navigate to udhaar items page
    page.goto("http://localhost:5173/udhaar-items")
    
    # Wait for udhaar items page to load
    page.wait_for_selector("button:has-text('نیا ادھار')", timeout=10000)
    
    yield page

@pytest.fixture
def test_item():
    """Create a unique test item"""
    unique_id = uuid.uuid4().hex[:6]
    return {
        "name": f"ادھار ٹیسٹ آئٹم {unique_id}",
        "price": "500",
        "stock": "100",
        "unit": "عدد"
    }

@pytest.fixture
def test_udhaar_item():
    """Create unique udhaar item data"""
    unique_id = uuid.uuid4().hex[:6]
    return {
        "customer": f"ٹیسٹ کسٹمر {unique_id}",
        "customer_edit": f"ٹیسٹ کسٹمر {unique_id} (ترمیم شدہ)",
        "quantity": "10",
        "edit_quantity": "15",
        "unit": "عدد"
    }

class TestUdhaarItemsCRUD:
    """Complete CRUD test suite for Udhaar Items"""
    
    def test_create_base_item_first(self, page_with_items, test_item):
        """Step 1: Create a base item that will be used for udhaar"""
        page = page_with_items
        
        # Click add button
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Fill item form
        name_input = page.locator("input[type='text']").first
        name_input.fill(test_item["name"])
        
        unit_select = page.locator("select").first
        unit_select.select_option(test_item["unit"])
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill(test_item["price"])
        number_inputs.nth(1).fill(test_item["stock"])
        
        # Save item
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Verify item was created
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(test_item["name"])
        page.wait_for_timeout(1000)
        
        expect(page.get_by_text(test_item["name"])).to_be_visible()
        
        return test_item
    
    def test_add_udhaar_item(self, page_with_udhaar, test_item, test_udhaar_item):
        """Test adding a new udhaar item"""
        page = page_with_udhaar
        
        # First ensure the base item exists
        # Navigate to items to create base item
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        # Check if item exists, if not create it
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(test_item["name"])
        page.wait_for_timeout(1000)
        
        if not page.get_by_text(test_item["name"]).is_visible():
            # Create the item
            page.get_by_role("button", name="نیا آئٹم").click()
            page.wait_for_selector("form", timeout=5000)
            
            name_input = page.locator("input[type='text']").first
            name_input.fill(test_item["name"])
            
            unit_select = page.locator("select").first
            unit_select.select_option(test_item["unit"])
            
            number_inputs = page.locator("input[type='number']")
            number_inputs.first.fill(test_item["price"])
            number_inputs.nth(1).fill(test_item["stock"])
            
            page.get_by_role("button", name="محفوظ کریں").click()
            page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
            page.wait_for_timeout(1500)
        
        # Now go to udhaar items page
        page.goto("http://localhost:5173/udhaar-items")
        page.wait_for_selector("button:has-text('نیا ادھار')", timeout=10000)
        
        # Click add udhaar button
        page.get_by_role("button", name="نیا ادھار").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Fill udhaar form
        customer_input = page.locator("input[type='text']").first
        customer_input.fill(test_udhaar_item["customer"])
        
        # Wait for item dropdown to be populated - improved wait strategy
        item_select = page.locator("select").first
        
        # Wait for the select to have options and the specific item
        page.wait_for_function(
            f"""() => {{
                const select = document.querySelector('select');
                if (!select || select.options.length <= 1) return false;
                for (let i = 0; i < select.options.length; i++) {{
                    if (select.options[i].value === '{test_item["name"]}') return true;
                }}
                return false;
            }}""",
            timeout=15000
        )
        
        # Now select the option
        item_select.select_option(value=test_item["name"])
        
        # Fill quantity
        quantity_input = page.locator("input[type='number']").first
        quantity_input.fill(test_udhaar_item["quantity"])
        
        # Select unit
        unit_select = page.locator("select").nth(1)
        unit_select.select_option(test_udhaar_item["unit"])
        
        # Save udhaar item
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=ادھار آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Search and verify
        search_input = page.get_by_placeholder("🔍 کسٹمر یا آئٹم تلاش کریں...")
        search_input.fill(test_udhaar_item["customer"])
        page.wait_for_timeout(1000)
        
        expect(page.get_by_text(test_udhaar_item["customer"])).to_be_visible()
        expect(page.get_by_text(test_item["name"])).to_be_visible()
        expect(page.get_by_text(test_udhaar_item["quantity"])).to_be_visible()
    
    def test_complete_udhaar_lifecycle(self, page_with_udhaar, test_item, test_udhaar_item):
        """Complete CRUD workflow for udhaar items"""
        page = page_with_udhaar
        
        # ========== 1. CREATE BASE ITEM ==========
        # Navigate to items and create base item
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        
        name_input = page.locator("input[type='text']").first
        name_input.fill(test_item["name"])
        
        unit_select = page.locator("select").first
        unit_select.select_option(test_item["unit"])
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill(test_item["price"])
        number_inputs.nth(1).fill(test_item["stock"])
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # ========== 2. CREATE UDHAAR ITEM ==========
        page.goto("http://localhost:5173/udhaar-items")
        page.wait_for_selector("button:has-text('نیا ادھار')", timeout=10000)
        
        page.get_by_role("button", name="نیا ادھار").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Fill form
        customer_input = page.locator("input[type='text']").first
        customer_input.fill(test_udhaar_item["customer"])
        
        # Wait for and select item from dropdown
        item_select = page.locator("select").first
        
        # Wait for the specific item to appear in dropdown
        page.wait_for_function(
            f"""() => {{
                const select = document.querySelector('select');
                if (!select || select.options.length <= 1) return false;
                for (let i = 0; i < select.options.length; i++) {{
                    if (select.options[i].value === '{test_item["name"]}') return true;
                }}
                return false;
            }}""",
            timeout=15000
        )
        
        item_select.select_option(value=test_item["name"])
        
        quantity_input = page.locator("input[type='number']").first
        quantity_input.fill(test_udhaar_item["quantity"])
        
        unit_select = page.locator("select").nth(1)
        unit_select.select_option(test_udhaar_item["unit"])
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=ادھار آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Verify creation
        search_input = page.get_by_placeholder("🔍 کسٹمر یا آئٹم تلاش کریں...")
        search_input.fill(test_udhaar_item["customer"])
        page.wait_for_timeout(1000)
        
        expect(page.get_by_text(test_udhaar_item["customer"])).to_be_visible()
        
        # ========== 3. UPDATE/EDIT UDHAAR ITEM ==========
        # Find the row and click edit
        item_row = page.locator(f"tr:has-text('{test_udhaar_item['customer']}')").first
        edit_button = item_row.get_by_text("ترمیم", exact=False)
        edit_button.click()
        
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Update customer name
        customer_input = page.locator("input[type='text']").first
        customer_input.clear()
        customer_input.fill(test_udhaar_item["customer_edit"])
        
        # Update quantity
        quantity_input = page.locator("input[type='number']").first
        quantity_input.clear()
        quantity_input.fill(test_udhaar_item["edit_quantity"])
        
        # Save changes
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=ادھار آئٹم اپ ڈیٹ ہو گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Wait for the table to refresh
        page.wait_for_timeout(1000)
        
        # Verify update - look for edited customer name and quantity
        search_input.clear()
        search_input.fill(test_udhaar_item["customer_edit"])
        page.wait_for_timeout(1000)
        
        # Check if the edited customer name is visible
        expect(page.get_by_text(test_udhaar_item["customer_edit"], exact=False)).to_be_visible()
        
        # Look for the quantity in a cell (it might be in a different format)
        # The quantity appears in the column before the unit
        quantity_cell = page.locator(f"tr:has-text('{test_udhaar_item['customer_edit']}') td:nth-child(3)")
        expect(quantity_cell).to_be_visible()
        
        # Verify the quantity value
        quantity_text = quantity_cell.inner_text()
        assert test_udhaar_item["edit_quantity"] in quantity_text, f"Expected quantity {test_udhaar_item['edit_quantity']} not found in {quantity_text}"
        
        # ========== 4. DELETE UDHAAR ITEM ==========
        item_row = page.locator(f"tr:has-text('{test_udhaar_item['customer_edit']}')").first
        delete_button = item_row.get_by_text("حذف", exact=False)
        delete_button.click()
        
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        confirm_button = page.get_by_role("button", name="ہاں، حذف کریں")
        confirm_button.click()
        
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Verify deletion
        search_input.clear()
        search_input.fill(test_udhaar_item["customer_edit"])
        page.wait_for_timeout(1000)
        
        # Check that item is no longer visible
        no_records_text = page.get_by_text("کوئی ادھار آئٹم موجود نہیں ہے")
        if no_records_text.is_visible():
            pass  # Successfully deleted
        else:
            expect(page.get_by_text(test_udhaar_item["customer_edit"], exact=False)).not_to_be_visible()
        
        # ========== 5. CLEAN UP - DELETE BASE ITEM ==========
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(test_item["name"])
        page.wait_for_timeout(1000)
        
        if page.get_by_text(test_item["name"]).is_visible():
            item_row = page.locator(f"tr:has-text('{test_item['name']}')").first
            delete_button = item_row.get_by_text("حذف", exact=False)
            delete_button.click()
            
            page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
            page.get_by_role("button", name="ہاں، حذف کریں").click()
            page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
    
    def test_udhaar_search_functionality(self, page_with_udhaar, test_item, test_udhaar_item):
        """Test search functionality in udhaar items"""
        page = page_with_udhaar
        
        # Create test data
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        # Create base item
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        
        name_input = page.locator("input[type='text']").first
        name_input.fill(test_item["name"])
        
        unit_select = page.locator("select").first
        unit_select.select_option(test_item["unit"])
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill(test_item["price"])
        number_inputs.nth(1).fill(test_item["stock"])
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Create udhaar item
        page.goto("http://localhost:5173/udhaar-items")
        page.wait_for_selector("button:has-text('نیا ادھار')", timeout=10000)
        
        page.get_by_role("button", name="نیا ادھار").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        customer_input = page.locator("input[type='text']").first
        customer_input.fill(test_udhaar_item["customer"])
        
        item_select = page.locator("select").first
        page.wait_for_function(
            f"""() => {{
                const select = document.querySelector('select');
                if (!select || select.options.length <= 1) return false;
                for (let i = 0; i < select.options.length; i++) {{
                    if (select.options[i].value === '{test_item["name"]}') return true;
                }}
                return false;
            }}""",
            timeout=15000
        )
        item_select.select_option(value=test_item["name"])
        
        quantity_input = page.locator("input[type='number']").first
        quantity_input.fill(test_udhaar_item["quantity"])
        
        unit_select = page.locator("select").nth(1)
        unit_select.select_option(test_udhaar_item["unit"])
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=ادھار آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Search by customer name
        search_input = page.get_by_placeholder("🔍 کسٹمر یا آئٹم تلاش کریں...")
        search_input.fill(test_udhaar_item["customer"])
        page.wait_for_timeout(1000)
        
        expect(page.get_by_text(test_udhaar_item["customer"])).to_be_visible()
        
        # Search by item name
        search_input.fill(test_item["name"])
        page.wait_for_timeout(1000)
        
        expect(page.get_by_text(test_item["name"])).to_be_visible()
        
        # Search with non-existent term
        search_input.fill("غیرموجودٹرمxyz123")
        page.wait_for_timeout(1000)
        
        no_records_text = page.get_by_text('"غیرموجودٹرمxyz123" کے نام سے کوئی ادھار نہیں ملا')
        expect(no_records_text).to_be_visible()
        
        # Clear search
        search_input.clear()
        page.wait_for_timeout(1000)
        
        # Clean up
        item_row = page.locator(f"tr:has-text('{test_udhaar_item['customer']}')").first
        item_row.get_by_text("حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
        
        # Delete base item
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(test_item["name"])
        page.wait_for_timeout(1000)
        
        if page.get_by_text(test_item["name"]).is_visible():
            item_row = page.locator(f"tr:has-text('{test_item['name']}')").first
            item_row.get_by_text("حذف").click()
            page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
            page.get_by_role("button", name="ہاں، حذف کریں").click()
            page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
    
    def test_udhaar_form_validation(self, page_with_udhaar):
        """Test form validation in udhaar items"""
        page = page_with_udhaar
        
        # Try to submit empty form
        page.get_by_role("button", name="نیا ادھار").click()
        page.wait_for_selector("form", timeout=5000)
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_timeout(500)
        
        # Check validation messages
        expect(page.get_by_text("کسٹمر کا نام درج کریں")).to_be_visible()
        expect(page.get_by_text("آئٹم کا نام منتخب کریں")).to_be_visible()
        
        # Fill partial form
        customer_input = page.locator("input[type='text']").first
        customer_input.fill("ٹیسٹ کسٹمر")
        
        # Submit without item and quantity
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_timeout(500)
        
        expect(page.get_by_text("آئٹم کا نام منتخب کریں")).to_be_visible()
        
        # Cancel form
        page.get_by_role("button", name="منسوخ کریں").click()
        page.wait_for_timeout(500)
        
        # Verify form is closed
        expect(page.get_by_role("button", name="نیا ادھار")).to_be_visible()
    
    def test_udhaar_cancel_operations(self, page_with_udhaar, test_item, test_udhaar_item):
        """Test cancel operations in udhaar items"""
        page = page_with_udhaar
        
        # Test cancel add form
        page.get_by_role("button", name="نیا ادھار").click()
        page.wait_for_selector("form", timeout=5000)
        
        customer_input = page.locator("input[type='text']").first
        customer_input.fill(test_udhaar_item["customer"])
        
        page.get_by_role("button", name="منسوخ کریں").click()
        page.wait_for_timeout(500)
        
        # Verify form closed
        expect(page.get_by_role("button", name="نیا ادھار")).to_be_visible()
        expect(page.get_by_text(test_udhaar_item["customer"])).not_to_be_visible()
        
        # Create actual udhaar item to test cancel delete
        # First create base item
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        
        name_input = page.locator("input[type='text']").first
        name_input.fill(test_item["name"])
        
        unit_select = page.locator("select").first
        unit_select.select_option(test_item["unit"])
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill(test_item["price"])
        number_inputs.nth(1).fill(test_item["stock"])
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Create udhaar item
        page.goto("http://localhost:5173/udhaar-items")
        page.wait_for_selector("button:has-text('نیا ادھار')", timeout=10000)
        
        page.get_by_role("button", name="نیا ادھار").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        customer_input = page.locator("input[type='text']").first
        customer_input.fill(test_udhaar_item["customer"])
        
        item_select = page.locator("select").first
        page.wait_for_function(
            f"""() => {{
                const select = document.querySelector('select');
                if (!select || select.options.length <= 1) return false;
                for (let i = 0; i < select.options.length; i++) {{
                    if (select.options[i].value === '{test_item["name"]}') return true;
                }}
                return false;
            }}""",
            timeout=15000
        )
        item_select.select_option(value=test_item["name"])
        
        quantity_input = page.locator("input[type='number']").first
        quantity_input.fill(test_udhaar_item["quantity"])
        
        unit_select = page.locator("select").nth(1)
        unit_select.select_option(test_udhaar_item["unit"])
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=ادھار آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Test cancel delete
        search_input = page.get_by_placeholder("🔍 کسٹمر یا آئٹم تلاش کریں...")
        search_input.fill(test_udhaar_item["customer"])
        page.wait_for_timeout(1000)
        
        item_row = page.locator(f"tr:has-text('{test_udhaar_item['customer']}')").first
        item_row.get_by_text("حذف").click()
        
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="منسوخ").click()
        page.wait_for_timeout(1000)
        
        # Verify item still exists
        expect(page.get_by_text(test_udhaar_item["customer"])).to_be_visible()
        
        # Clean up
        item_row.get_by_text("حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
        
        # Delete base item
        page.goto("http://localhost:5173/items")
        page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
        
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(test_item["name"])
        page.wait_for_timeout(1000)
        
        if page.get_by_text(test_item["name"]).is_visible():
            item_row = page.locator(f"tr:has-text('{test_item['name']}')").first
            item_row.get_by_text("حذف").click()
            page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
            page.get_by_role("button", name="ہاں، حذف کریں").click()
            page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)


def test_quick_udhaar_workflow(authenticated_page):
    """Simplified quick test for udhaar CRUD workflow"""
    page = authenticated_page
    unique_id = uuid.uuid4().hex[:6]
    item_name = f"فوری آئٹم {unique_id}"
    customer_name = f"فوری کسٹمر {unique_id}"
    
    # Create base item
    page.goto("http://localhost:5173/items")
    page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
    
    page.get_by_role("button", name="نیا آئٹم").click()
    page.wait_for_selector("form", timeout=5000)
    page.wait_for_timeout(500)
    
    page.locator("input[type='text']").first.fill(item_name)
    page.locator("select").first.select_option("عدد")
    number_inputs = page.locator("input[type='number']")
    number_inputs.first.fill("1000")
    number_inputs.nth(1).fill("50")
    
    page.get_by_role("button", name="محفوظ کریں").click()
    page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
    page.wait_for_timeout(1000)
    
    # Create udhaar item
    page.goto("http://localhost:5173/udhaar-items")
    page.wait_for_selector("button:has-text('نیا ادھار')", timeout=10000)
    
    page.get_by_role("button", name="نیا ادھار").click()
    page.wait_for_selector("form", timeout=5000)
    page.wait_for_timeout(500)
    
    page.locator("input[type='text']").first.fill(customer_name)
    
    # Wait for dropdown to populate and select
    item_select = page.locator("select").first
    page.wait_for_function(
        f"""() => {{
            const select = document.querySelector('select');
            if (!select || select.options.length <= 1) return false;
            for (let i = 0; i < select.options.length; i++) {{
                if (select.options[i].value === '{item_name}') return true;
            }}
            return false;
        }}""",
        timeout=15000
    )
    item_select.select_option(value=item_name)
    
    page.locator("input[type='number']").first.fill("5")
    page.locator("select").nth(1).select_option("عدد")
    
    page.get_by_role("button", name="محفوظ کریں").click()
    page.wait_for_selector("text=ادھار آئٹم شامل کر دیا گیا", timeout=5000)
    page.wait_for_timeout(1000)
    
    # Verify udhaar item
    page.get_by_placeholder("🔍 کسٹمر یا آئٹم تلاش کریں...").fill(customer_name)
    page.wait_for_timeout(1000)
    expect(page.get_by_text(customer_name)).to_be_visible()
    
    # Delete udhaar item
    item_row = page.locator(f"tr:has-text('{customer_name}')").first
    item_row.get_by_text("حذف").click()
    page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
    page.get_by_role("button", name="ہاں، حذف کریں").click()
    page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
    
    # Delete base item
    page.goto("http://localhost:5173/items")
    page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
    
    page.get_by_placeholder("🔍 آئٹم تلاش کریں...").fill(item_name)
    page.wait_for_timeout(1000)
    
    if page.get_by_text(item_name).is_visible():
        item_row = page.locator(f"tr:has-text('{item_name}')").first
        item_row.get_by_text("حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)