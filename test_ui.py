from playwright.sync_api import sync_playwright
import time

def test_spread_tool():
    with sync_playwright() as p:
        # Launch browser in headed mode to see what's happening
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to the app
        page.goto("http://localhost:8000")
        
        # Take a screenshot
        page.screenshot(path="ui_screenshot.png")
        
        # Wait a bit to see the page
        time.sleep(2)
        
        # Try to click the analyze button
        try:
            page.click("button:has-text('Analyze Strategies')")
            time.sleep(2)
            page.screenshot(path="after_analyze.png")
        except Exception as e:
            print(f"Error clicking analyze: {e}")
            # Check console for errors
            page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
            
        # Keep browser open for inspection
        time.sleep(10)
        
        browser.close()

if __name__ == "__main__":
    test_spread_tool()