from playwright.sync_api import sync_playwright
import time

def test_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to the app
        print("Navigating to app...")
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")
        
        # Take screenshot of initial state
        page.screenshot(path="initial_state.png")
        print("Initial screenshot taken")
        
        # Wait for current price to load
        page.wait_for_selector("#currentPrice:has-text('Current SPY:')", timeout=5000)
        print("Current price loaded")
        
        # Click analyze button
        print("Clicking analyze button...")
        page.click("button:has-text('Analyze Strategies')")
        
        # Wait for results
        try:
            page.wait_for_selector(".strategy-card", timeout=10000)
            print("Results loaded successfully!")
            
            # Take screenshot of results
            page.screenshot(path="results_state.png")
            
            # Check if chart is rendered
            chart_canvas = page.query_selector("#chart")
            if chart_canvas:
                print("Chart rendered successfully")
            
        except Exception as e:
            print(f"Error waiting for results: {e}")
            page.screenshot(path="error_state.png")
            
            # Get any error messages
            error_msg = page.query_selector(".error")
            if error_msg:
                print(f"Error message: {error_msg.inner_text()}")
        
        # Keep browser open for manual inspection
        print("\nBrowser will close in 5 seconds...")
        time.sleep(5)
        
        browser.close()

if __name__ == "__main__":
    test_app()