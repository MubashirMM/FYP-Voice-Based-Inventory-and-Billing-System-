import pytest
from playwright.sync_api import sync_playwright, expect
import uuid
import time

@pytest.fixture(scope="module")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    context = browser_instance.new_context()
    page = context.new_page()
    
    # First login to get authenticated
    page.goto("http://localhost:5173/login")
    page.get_by_placeholder("ای میل درج کریں").fill("32304mubashir@gmail.com")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill("Pass1234!")
    page.get_by_role("button", name="لاگ ان کریں").click()
    
    # Wait for login to complete
    page.wait_for_url(lambda url: "items" in url.lower() or "dashboard" in url.lower(), timeout=15000)
    
    # If not already on items page, navigate to items
    if "/items" not in page.url:
        try:
            # Try multiple possible selectors for items navigation
            items_link = page.get_by_text("آئٹمز", exact=False).first
            if items_link.is_visible():
                items_link.click()
            else:
                page.goto("http://localhost:5173/items")
            page.wait_for_timeout(1000)
        except:
            page.goto("http://localhost:5173/items")
    
    # Wait for items page to load - look for the main elements
    page.wait_for_selector("button:has-text('نیا آئٹم')", timeout=10000)
    
    yield page
    context.close()

@pytest.fixture
def item_data():
    """Generate unique item data for testing"""
    unique_id = uuid.uuid4().hex[:6]
    return {
        "name": f"ٹیسٹ آئٹم {unique_id}",
        "edit_name": f"ٹیسٹ آئٹم {unique_id} (ترمیم شدہ)",
        "price": "250",
        "edit_price": "350",
        "stock": "100",
        "edit_stock": "75",
        "unit": "کلوگرام"
    }

class TestItemsCRUD:
    
    def test_complete_item_lifecycle(self, page, item_data):
        """Complete CRUD workflow - Add, Search, Edit, Delete in one test"""
        
        # ========== 1. CREATE ITEM ==========
        # Click add button
        page.get_by_role("button", name="نیا آئٹم").click()
        
        # Wait for form to be visible
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Fill item name - use the input with proper selector
        name_input = page.locator("input[type='text']").first
        name_input.fill(item_data["name"])
        
        # Select unit from dropdown
        unit_select = page.locator("select").first
        unit_select.select_option(item_data["unit"])
        
        # Find price and stock inputs (both are type='number')
        number_inputs = page.locator("input[type='number']")
        price_input = number_inputs.first
        price_input.fill(item_data["price"])
        
        # Fill stock quantity (second number input)
        stock_input = number_inputs.nth(1)
        stock_input.fill(item_data["stock"])
        
        # Click save button
        save_button = page.get_by_role("button", name="محفوظ کریں")
        save_button.click()
        
        # Wait for success message
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # ========== 2. SEARCH AND VERIFY CREATION ==========
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(item_data["name"])
        page.wait_for_timeout(1000)
        
        # Verify item appears in table
        expect(page.get_by_text(item_data["name"], exact=False)).to_be_visible()
        expect(page.get_by_text(f"Rs. {item_data['price']}")).to_be_visible()
        
        # ========== 3. EDIT ITEM ==========
        # Find the row with our item
        item_row = page.locator(f"tr:has-text('{item_data['name']}')").first
        
        # Click edit button in that row using the text content
        edit_button = item_row.get_by_text("ترمیم", exact=False)
        edit_button.click()
        
        # Wait for edit form
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Clear and fill edited name
        name_input = page.locator("input[type='text']").first
        name_input.clear()
        name_input.fill(item_data["edit_name"])
        
        # Update price and stock
        number_inputs = page.locator("input[type='number']")
        price_input = number_inputs.first
        price_input.clear()
        price_input.fill(item_data["edit_price"])
        
        stock_input = number_inputs.nth(1)
        stock_input.clear()
        stock_input.fill(item_data["edit_stock"])
        
        # Save changes
        save_button = page.get_by_role("button", name="محفوظ کریں")
        save_button.click()
        
        # Wait for update success message
        page.wait_for_selector("text=آئٹم اپ ڈیٹ ہو گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # ========== 4. SEARCH AND VERIFY UPDATE ==========
        search_input.clear()
        search_input.fill(item_data["edit_name"])
        page.wait_for_timeout(1000)
        
        # Verify updated item appears with new values
        expect(page.get_by_text(item_data["edit_name"], exact=False)).to_be_visible()
        expect(page.get_by_text(f"Rs. {item_data['edit_price']}")).to_be_visible()
        
        # ========== 5. DELETE ITEM ==========
        # Find the row with our edited item
        item_row = page.locator(f"tr:has-text('{item_data['edit_name']}')").first
        
        # Click delete button
        delete_button = item_row.get_by_text("حذف", exact=False)
        delete_button.click()
        
        # Wait for confirmation modal and confirm
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        confirm_button = page.get_by_role("button", name="ہاں، حذف کریں")
        confirm_button.click()
        
        # Wait for delete success message
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # ========== 6. VERIFY DELETION ==========
        search_input.clear()
        search_input.fill(item_data["edit_name"])
        page.wait_for_timeout(1000)
        
        # Look for the "no records" message instead of checking item not visible
        # Since the table shows "کوئی آئٹم موجود نہیں ہے" when empty
        no_records_text = page.get_by_text("کوئی آئٹم موجود نہیں ہے")
        if no_records_text.is_visible():
            # Item successfully deleted
            pass
        else:
            # If no records text not visible, check that our specific item is gone
            expect(page.get_by_text(item_data["edit_name"], exact=False)).not_to_be_visible()
    
    def test_add_item_with_custom_unit(self, page, item_data):
        """Test adding an item with custom unit"""
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Fill item name
        name_input = page.locator("input[type='text']").first
        name_input.fill(item_data["name"])
        
        # Select custom unit from dropdown
        unit_select = page.locator("select").first
        unit_select.select_option("__custom")
        
        # Fill custom unit name - this appears as a text input
        custom_unit_input = page.locator("input[type='text']").nth(1)
        custom_unit_input.fill("گھنٹہ")
        
        # Fill price and stock
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill("200")
        number_inputs.nth(1).fill("50")
        
        # Save
        page.get_by_role("button", name="محفوظ کریں").click()
        
        # Verify success
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Search and verify
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(item_data["name"])
        page.wait_for_timeout(1000)
        
        expect(page.get_by_text(item_data["name"])).to_be_visible()
        # The unit appears in the table - check for the text in the unit column
        expect(page.get_by_role("cell", name="گھنٹہ").first).to_be_visible()
        
        # Clean up - delete the test item
        item_row = page.locator(f"tr:has-text('{item_data['name']}')").first
        item_row.get_by_text("حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
    
    def test_form_validation(self, page):
        """Test form validation errors"""
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        
        # Try to submit empty form
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_timeout(500)
        
        # Check for validation error messages
        expect(page.get_by_text("آئٹم کا نام درج کریں")).to_be_visible()
        expect(page.get_by_text("قیمت درج کریں")).to_be_visible()
        expect(page.get_by_text("مقدار درج کریں")).to_be_visible()
        
        # Test negative price validation
        name_input = page.locator("input[type='text']").first
        name_input.fill("ویلیڈیشن ٹیسٹ")
        
        unit_select = page.locator("select").first
        unit_select.select_option("عدد")
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill("-100")
        number_inputs.nth(1).fill("10")
        
        page.get_by_role("button", name="محفوظ کریں").click()
        
        # Should show price validation error
        expect(page.get_by_text("قیمت صفر سے زیادہ ہونی چاہیے")).to_be_visible()
        
        # Cancel form
        page.get_by_role("button", name="منسوخ کریں").click()
    
    def test_search_functionality(self, page, item_data):
        """Test search/filter functionality"""
        # Create a unique item for search test
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        name_input = page.locator("input[type='text']").first
        name_input.fill(item_data["name"])
        
        unit_select = page.locator("select").first
        unit_select.select_option("عدد")
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill("500")
        number_inputs.nth(1).fill("10")
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Search for the item
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(item_data["name"])
        page.wait_for_timeout(1000)
        
        # Verify item is visible
        expect(page.get_by_text(item_data["name"])).to_be_visible()
        
        # Search with non-existent term
        search_input.fill("غیرموجودآئٹمxyz123")
        page.wait_for_timeout(1000)
        
        # Verify no records message - the actual message in your component
        no_records_text = page.get_by_text(f'"غیرموجودآئٹمxyz123" کے نام سے کوئی آئٹم نہیں ملا')
        expect(no_records_text).to_be_visible()
        
        # Clear search
        search_input.clear()
        page.wait_for_timeout(1000)
        
        # Verify items are visible again (our test item should be there)
        expect(page.get_by_text(item_data["name"])).to_be_visible()
        
        # Clean up
        item_row = page.locator(f"tr:has-text('{item_data['name']}')").first
        item_row.get_by_text("حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
    
    def test_cancel_operations(self, page, item_data):
        """Test canceling add and delete operations"""
        # Test cancel add form
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        
        name_input = page.locator("input[type='text']").first
        name_input.fill(item_data["name"])
        
        page.get_by_role("button", name="منسوخ کریں").click()
        page.wait_for_timeout(500)
        
        # Verify form closed and we're back to list
        expect(page.get_by_role("button", name="نیا آئٹم")).to_be_visible()
        # The item should not be visible since we cancelled
        expect(page.get_by_text(item_data["name"])).not_to_be_visible()
        
        # Now actually create an item to test cancel delete
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        name_input = page.locator("input[type='text']").first
        name_input.fill(item_data["name"])
        
        unit_select = page.locator("select").first
        unit_select.select_option("عدد")
        
        number_inputs = page.locator("input[type='number']")
        number_inputs.first.fill("100")
        number_inputs.nth(1).fill("20")
        
        page.get_by_role("button", name="محفوظ کریں").click()
        page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
        page.wait_for_timeout(1500)
        
        # Test cancel delete
        search_input = page.get_by_placeholder("🔍 آئٹم تلاش کریں...")
        search_input.fill(item_data["name"])
        page.wait_for_timeout(1000)
        
        item_row = page.locator(f"tr:has-text('{item_data['name']}')").first
        item_row.get_by_text("حذف").click()
        
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="منسوخ").click()
        page.wait_for_timeout(1000)
        
        # Verify item still exists
        expect(page.get_by_text(item_data["name"])).to_be_visible()
        
        # Clean up - actually delete it
        item_row.get_by_text("حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)


def test_simplified_item_operations(page):
    """Simplified test that creates and deletes one item using proper selectors"""
    unique_name = f"سادہ ٹیسٹ {uuid.uuid4().hex[:6]}"
    
    # Create item
    page.get_by_role("button", name="نیا آئٹم").click()
    page.wait_for_selector("form", timeout=5000)
    page.wait_for_timeout(500)
    
    # Fill form using proper selectors
    name_input = page.locator("input[type='text']").first
    name_input.fill(unique_name)
    
    unit_select = page.locator("select").first
    unit_select.select_option("عدد")
    
    number_inputs = page.locator("input[type='number']")
    number_inputs.first.fill("150")
    number_inputs.nth(1).fill("30")
    
    page.get_by_role("button", name="محفوظ کریں").click()
    page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
    page.wait_for_timeout(1500)
    
    # Search and verify
    page.get_by_placeholder("🔍 آئٹم تلاش کریں...").fill(unique_name)
    page.wait_for_timeout(1000)
    expect(page.get_by_text(unique_name)).to_be_visible()
    
    # Delete
    item_row = page.locator(f"tr:has-text('{unique_name}')").first
    item_row.get_by_text("حذف").click()
    page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
    page.get_by_role("button", name="ہاں، حذف کریں").click()
    page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)