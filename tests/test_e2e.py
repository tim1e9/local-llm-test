"""
End-to-end tests for HR Vacation Application using Playwright.
Tests login, vacation requests, balance viewing, manager approvals, and logout.
Run with: python tests/test_e2e.py
"""
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5000"

# Test users (from seed_data.py)
USERS = {
    "admin": {"username": "admin", "roles": ["ADMIN", "MANAGER"]},
    "manager": {"username": "jdoe", "roles": ["MANAGER"]},
    "employee1": {"username": "janedoe", "roles": ["EMPLOYEE"], "manager": "jdoe"},
    "employee2": {"username": "bobsmith", "roles": ["EMPLOYEE"], "manager": "jdoe"},
}


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        passed = 0
        failed = 0
        errors = []

        # ========== Test 1: Login as employee ==========
        print("\n[TEST 1] Login as employee (janedoe)")
        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
            page.wait_for_selector("#login-form", timeout=5000)
            page.fill("#username", "janedoe")
            page.click("button[type='submit']")
            page.wait_for_selector("#dashboard-view", timeout=8000)
            assert "hidden" not in page.locator("#dashboard-view").get_attribute("class")
            user_name = page.locator("#user-name").inner_text()
            assert "Jane Doe" in user_name, f"Expected 'Jane Doe', got '{user_name}'"
            print("  ✓ Login successful, dashboard visible")
            passed += 1

            # ========== Test 2: View balance ==========
            print("\n[TEST 2] View vacation balance")
            page.click('button[data-tab="balance"]')
            page.wait_for_selector("#balance-info", timeout=5000)
            balance_text = page.locator("#balance-info").inner_text()
            assert "80" in balance_text, f"Expected 80 hours in balance, got: {balance_text}"
            assert "Available" in balance_text, "Missing 'Available' label"
            print(f"  ✓ Balance displayed correctly: {balance_text[:80]}")
            passed += 1

            # ========== Test 3: Create vacation request ==========
            print("\n[TEST 3] Create a vacation request")
            page.click('button[data-tab="new-request"]')
            page.wait_for_selector("#vacation-form", timeout=5000)
            # Set dates for next week
            start_date = "2026-09-15"
            end_date = "2026-09-17"
            page.fill("#start-date", start_date)
            page.fill("#end-date", end_date)
            page.fill("#reason", "E2E test vacation")
            # Wait for hours calculation
            page.wait_for_function(
                "document.getElementById('hours-calculation').textContent !== '0'"
            )
            hours = page.locator("#hours-calculation").inner_text()
            assert "24" in hours, f"Expected 24 hours (3 days), got {hours}"
            print(f"  ✓ Hours calculated: {hours}")

            page.click('form#vacation-form button[type="submit"]')
            page.wait_for_selector("text=/successfully|submitted/i", timeout=8000)
            print("  ✓ Request submitted successfully")
            passed += 1

            # ========== Test 4: Verify request appears in "My Requests" ==========
            print("\n[TEST 4] Verify request appears in My Requests")
            page.click('button[data-tab="my-requests"]')
            page.wait_for_selector("#requests-list .card", timeout=5000)
            cards = page.locator("#requests-list .card")
            assert cards.count() > 0, "No request cards found"
            print(f"  ✓ Found {cards.count()} request card(s)")
            passed += 1

            # ========== Test 5: Logout ==========
            print("\n[TEST 5] Logout as employee")
            page.click("#logout-btn")
            page.wait_for_selector("#login-view", timeout=5000)
            assert "hidden" not in page.locator("#login-view").get_attribute("class")
            print("  ✓ Logged out successfully")
            passed += 1

            # ========== Test 6: Login as manager and approve request ==========
            print("\n[TEST 6] Login as manager (jdoe) and approve pending request")
            page.fill("#username", "jdoe")
            page.click("button[type='submit']")
            page.wait_for_selector("#dashboard-view", timeout=8000)
            user_name = page.locator("#user-name").inner_text()
            assert "John Doe" in user_name, f"Expected 'John Doe', got '{user_name}'"
            print("  ✓ Manager logged in")

            # Check pending approvals tab exists (manager role)
            pending_tab = page.locator('button[data-tab="pending-approvals"]')
            assert "hidden" not in pending_tab.get_attribute("class"), "Pending Approvals tab should be visible for manager"
            print("  ✓ Pending Approvals tab visible")

            # Navigate to pending approvals
            page.click('button[data-tab="pending-approvals"]')
            page.wait_for_selector("#pending-list", timeout=5000)
            pending_cards = page.locator("#pending-list .card")
            print(f"  ✓ Found {pending_cards.count()} pending request(s)")

            if pending_cards.count() > 0:
                # Approve the first pending request
                approve_btns = page.locator(".btn-approve")
                btn_count = approve_btns.count()
                assert btn_count > 0, "No approve button found"
                approve_btns.first.click()
                page.wait_for_selector("text=/approved/i", timeout=8000)
                print("  ✓ Request approved successfully")
                passed += 1

            # ========== Test 7: Logout as manager ==========
            print("\n[TEST 7] Logout as manager")
            page.click("#logout-btn")
            page.wait_for_selector("#login-view", timeout=5000)
            print("  ✓ Manager logged out successfully")
            passed += 1

            # ========== Test 8: Login as employee and verify approved status ==========
            print("\n[TEST 8] Verify request status is APPROVED")
            page.fill("#username", "janedoe")
            page.click("button[type='submit']")
            page.wait_for_selector("#dashboard-view", timeout=8000)
            page.click('button[data-tab="my-requests"]')
            page.wait_for_selector("#requests-list .card", timeout=5000)
            status_elements = page.locator("#requests-list .status")
            statuses = [status_elements.nth(i).inner_text() for i in range(status_elements.count())]
            assert "APPROVED" in statuses, f"Expected APPROVED status, got: {statuses}"
            print(f"  ✓ Request status is APPROVED (statuses: {statuses})")
            passed += 1

        except Exception as e:
            failed += 1
            error_msg = f"[TEST {passed + failed}] FAILED: {str(e)}"
            errors.append(error_msg)
            print(f"  ✗ {error_msg}")
            # Take screenshot on failure
            try:
                page.screenshot(path=f"tests/screenshots/failure_{passed + failed}.png")
            except Exception:
                pass

        browser.close()

        # ========== Summary ==========
        total = passed + failed
        print(f"\n{'='*50}")
        print(f"E2E Test Results: {passed}/{total} passed, {failed} failed")
        print(f"{'='*50}")
        if errors:
            for err in errors:
                print(f"  ❌ {err}")
        print()


if __name__ == "__main__":
    run_tests()
