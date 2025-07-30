from playwright.sync_api import sync_playwright
import time

def test_react_integration():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to the React app
        print("1. Navigating to React app...")
        page.goto("http://localhost:3000")
        page.wait_for_load_state("networkidle")
        
        # Check if the page loaded
        print("2. Checking page title and header...")
        title = page.title()
        print(f"   Page title: {title}")
        
        # Look for the SPY price in header
        spy_price_element = page.query_selector("text=/Current SPY:/")
        if spy_price_element:
            print("   ✅ SPY price element found in header")
        else:
            print("   ❌ SPY price element NOT found")
        
        # Check for main components
        print("\n3. Checking main components...")
        
        # Input controls
        date_input = page.query_selector("input[type='date']")
        print(f"   Date input: {'✅ Found' if date_input else '❌ Not found'}")
        
        contracts_input = page.query_selector("input[type='number']")
        print(f"   Contracts input: {'✅ Found' if contracts_input else '❌ Not found'}")
        
        # Strike price inputs
        strike_inputs = page.query_selector_all("input[type='number']")
        print(f"   Strike price inputs: {len(strike_inputs)} found")
        
        # Analyze button
        analyze_button = page.query_selector("button:has-text('Analyze Strategies')")
        print(f"   Analyze button: {'✅ Found' if analyze_button else '❌ Not found'}")
        
        # Take a screenshot of initial state
        page.screenshot(path="react_initial_state.png")
        print("\n4. Screenshot saved: react_initial_state.png")
        
        # Try clicking the Analyze button
        if analyze_button:
            print("\n5. Clicking 'Analyze Strategies' button...")
            analyze_button.click()
            
            # Wait for loading state
            time.sleep(3)
            
            # Check for results
            strategy_cards = page.query_selector_all(".strategy-card, [class*='strategy'], [class*='card']")
            print(f"   Strategy result cards: {len(strategy_cards)} found")
            
            # Take screenshot of results
            page.screenshot(path="react_analysis_results.png")
            print("   Screenshot saved: react_analysis_results.png")
            
        # Check browser console for errors
        print("\n6. Checking for console errors...")
        page.on("console", lambda msg: print(f"   Console {msg.type()}: {msg.text()}"))
        
        # Wait a bit to see any console messages
        time.sleep(2)
        
        print("\n7. Test complete!")
        
        # Keep browser open for manual inspection
        input("Press Enter to close browser...")
        
        browser.close()

if __name__ == "__main__":
    test_react_integration()