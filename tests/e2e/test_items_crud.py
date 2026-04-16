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
    page.get_by_placeholder("example@email.com").fill("32304mubashir@gmail.com")
    page.get_by_placeholder("پاس ورڈ درج کریں").fill("Abcd1234!")
    page.get_by_role("button", name="لاگ ان کریں").click()
    
    # Wait for login to complete and dashboard to load
    page.wait_for_url(lambda url: "items" in url.lower() or "dashboard" in url.lower(), timeout=15000)
    
    # If not already on items page, navigate to items
    if "/items" not in page.url:
        try:
            # Try multiple possible selectors for items navigation
            items_link = page.get_by_text("آئٹمز", exact=False).first
            if items_link.is_visible():
                items_link.click()
            else:
                # Try alternative navigation
                page.goto("http://localhost:5173/items")
            page.wait_for_timeout(1000)
        except:
            page.goto("http://localhost:5173/items")
    
    # Wait for items page to load
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
        page.wait_for_timeout(500)  # Small delay for form animation
        
        # Fill form using more robust selectors
        # Option 1: Use CSS selector for the input field
        name_input = page.locator("input[class*='border-2']").first
        name_input.fill(item_data["name"])
        
        # Select unit from dropdown
        unit_select = page.locator("select").first
        unit_select.select_option(item_data["unit"])
        
        # Find price input (the number input fields)
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
        page.wait_for_timeout(1500)  # Wait for form to close
        
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
        
        # Click edit button in that row
        edit_button = item_row.get_by_role("button", name="ترمیم")
        edit_button.click()
        
        # Wait for edit form
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Clear and fill edited name
        name_input = page.locator("input[class*='border-2']").first
        name_input.clear()
        name_input.fill(item_data["edit_name"])
        
        # Update price
        number_inputs = page.locator("input[type='number']")
        price_input = number_inputs.first
        price_input.clear()
        price_input.fill(item_data["edit_price"])
        
        # Update stock
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
        delete_button = item_row.get_by_role("button", name="حذف")
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
        
        # Verify item no longer exists
        expect(page.get_by_text(item_data["edit_name"], exact=False)).not_to_be_visible()
    
    def test_add_item_with_custom_unit(self, page, item_data):
        """Test adding an item with custom unit"""
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        # Fill item name
        name_input = page.locator("input[class*='border-2']").first
        name_input.fill(item_data["name"])
        
        # Select custom unit from dropdown
        unit_select = page.locator("select").first
        unit_select.select_option("__custom")
        
        # Fill custom unit name
        custom_unit_input = page.locator("input[class*='border-2']").nth(1)
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
        expect(page.get_by_text("گھنٹہ")).to_be_visible()
        
        # Clean up - delete the test item
        item_row = page.locator(f"tr:has-text('{item_data['name']}')").first
        item_row.get_by_role("button", name="حذف").click()
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
        name_input = page.locator("input[class*='border-2']").first
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
        
        name_input = page.locator("input[class*='border-2']").first
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
        
        # Verify no records message
        expect(page.get_by_text("کوئی ریکارڈ موجود نہیں ہے۔")).to_be_visible()
        
        # Clear search
        search_input.clear()
        page.wait_for_timeout(1000)
        
        # Verify items are visible again (our test item should be there)
        expect(page.get_by_text(item_data["name"])).to_be_visible()
        
        # Clean up
        item_row = page.locator(f"tr:has-text('{item_data['name']}')").first
        item_row.get_by_role("button", name="حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)
    
    def test_cancel_operations(self, page, item_data):
        """Test canceling add and delete operations"""
        # Test cancel add form
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        
        name_input = page.locator("input[class*='border-2']").first
        name_input.fill(item_data["name"])
        
        page.get_by_role("button", name="منسوخ کریں").click()
        page.wait_for_timeout(500)
        
        # Verify form closed and we're back to list
        expect(page.get_by_role("button", name="نیا آئٹم")).to_be_visible()
        expect(page.get_by_text(item_data["name"])).not_to_be_visible()
        
        # Now actually create an item to test cancel delete
        page.get_by_role("button", name="نیا آئٹم").click()
        page.wait_for_selector("form", timeout=5000)
        page.wait_for_timeout(500)
        
        name_input = page.locator("input[class*='border-2']").first
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
        item_row.get_by_role("button", name="حذف").click()
        
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="منسوخ").click()
        page.wait_for_timeout(1000)
        
        # Verify item still exists
        expect(page.get_by_text(item_data["name"])).to_be_visible()
        
        # Clean up - actually delete it
        item_row.get_by_role("button", name="حذف").click()
        page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
        page.get_by_role("button", name="ہاں، حذف کریں").click()
        page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)

# Alternative simplified test if the above still has issues
def test_simplified_item_operations(page):
    """Simplified test that creates and deletes one item"""
    unique_name = f"سادہ ٹیسٹ {uuid.uuid4().hex[:6]}"
    
    # Create item
    page.get_by_role("button", name="نیا آئٹم").click()
    page.wait_for_selector("form", timeout=5000)
    
    # Use JavaScript to fill the form (more reliable)
    page.evaluate("""
        () => {
            const inputs = document.querySelectorAll('input');
            if (inputs[0]) inputs[0].value = arguments[0];
            const selects = document.querySelectorAll('select');
            if (selects[0]) selects[0].value = 'عدد';
            const numberInputs = document.querySelectorAll('input[type="number"]');
            if (numberInputs[0]) numberInputs[0].value = '150';
            if (numberInputs[1]) numberInputs[1].value = '30';
        }
    """, unique_name)
    
    page.get_by_role("button", name="محفوظ کریں").click()
    page.wait_for_selector("text=آئٹم شامل کر دیا گیا", timeout=5000)
    page.wait_for_timeout(1500)
    
    # Search and verify
    page.get_by_placeholder("🔍 آئٹم تلاش کریں...").fill(unique_name)
    page.wait_for_timeout(1000)
    expect(page.get_by_text(unique_name)).to_be_visible()
    
    # Delete
    item_row = page.locator(f"tr:has-text('{unique_name}')").first
    item_row.get_by_role("button", name="حذف").click()
    page.wait_for_selector("text=کیا آپ کو یقین ہے؟", timeout=5000)
    page.get_by_role("button", name="ہاں، حذف کریں").click()
    page.wait_for_selector("text=کامیابی سے حذف کر دیا گیا", timeout=5000)