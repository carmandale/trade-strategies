from playwright.sync_api import sync_playwright
import time

def debug_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        # Capture page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        
        # Navigate to the app
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")
        
        # Get the HTML to see what's rendered
        html = page.content()
        print("=== PAGE CONTENT ===")
        print(html[:500] + "..." if len(html) > 500 else html)
        
        # Check if Chart.js loaded
        chart_loaded = page.evaluate("() => typeof Chart !== 'undefined'")
        print(f"\nChart.js loaded: {chart_loaded}")
        
        # Try to get values from inputs
        try:
            date_value = page.input_value("#date")
            print(f"Date value: {date_value}")
            
            bull_call_1 = page.input_value("#bullCall1")
            print(f"Bull Call Strike 1: {bull_call_1}")
        except Exception as e:
            print(f"Error getting input values: {e}")
        
        # Try to analyze
        try:
            page.click("button:has-text('Analyze Strategies')")
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Error clicking analyze: {e}")
        
        # Print console messages
        if console_messages:
            print("\n=== CONSOLE MESSAGES ===")
            for msg in console_messages:
                print(msg)
        
        # Print page errors
        if page_errors:
            print("\n=== PAGE ERRORS ===")
            for err in page_errors:
                print(err)
        
        browser.close()

if __name__ == "__main__":
    debug_ui()