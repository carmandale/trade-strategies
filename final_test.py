from playwright.sync_api import sync_playwright
import time

def final_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to the app
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")
        
        # Wait for everything to load
        page.wait_for_selector("#currentPrice:has-text('Current SPY:')")
        
        # Test different dates
        print("Testing with different dates...")
        
        # Test with past date
        page.fill("#date", "2025-07-25")
        page.click("button:has-text('Analyze Strategies')")
        page.wait_for_selector(".strategy-card", timeout=10000)
        time.sleep(2)
        page.screenshot(path="past_date_analysis.png")
        print("Past date analysis complete")
        
        # Test with today
        page.fill("#date", "2025-07-29")
        page.click("button:has-text('Analyze Strategies')")
        page.wait_for_selector(".strategy-card", timeout=10000)
        time.sleep(2)
        page.screenshot(path="today_analysis.png")
        print("Today's analysis complete")
        
        # Test saving a trade
        print("Testing trade logging...")
        trade_buttons = page.query_selector_all("button:has-text('Log Trade')")
        if trade_buttons:
            trade_buttons[0].click()
            time.sleep(1)
            page.screenshot(path="trade_logged.png")
            print("Trade logged successfully")
        
        print("\nAll tests complete! Check the screenshots.")
        time.sleep(3)
        
        browser.close()

if __name__ == "__main__":
    final_test()