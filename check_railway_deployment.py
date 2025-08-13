#!/usr/bin/env python3
"""
Railway deployment verification script.
Tests the deployed API endpoints and provides deployment status.
"""
import requests
import time
import json
from typing import Dict, Any

RAILWAY_URL = "https://trade-strategies-production.up.railway.app"

def test_endpoint(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Test an endpoint and return status information."""
    try:
        response = requests.get(url, timeout=timeout)
        return {
            "status": "success",
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

def check_deployment():
    """Check Railway deployment status."""
    print("🚀 Railway Deployment Verification")
    print("=" * 50)
    print(f"Testing: {RAILWAY_URL}")
    print()
    
    endpoints = [
        ("Root", "/"),
        ("Health Check", "/health"),
        ("Strategies", "/strategies"),
        ("Docs", "/docs")
    ]
    
    results = []
    
    for name, path in endpoints:
        print(f"Testing {name} ({path})...")
        url = f"{RAILWAY_URL}{path}"
        result = test_endpoint(url)
        results.append((name, path, result))
        
        if result["status"] == "success":
            print(f"  ✅ {result['status_code']} - OK")
            if isinstance(result["response"], dict):
                print(f"  📄 Response: {json.dumps(result['response'], indent=2)[:100]}...")
        else:
            print(f"  ❌ {result['error_type']}: {result['error']}")
        print()
    
    # Summary
    print("=" * 50)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for _, _, result in results if result["status"] == "success")
    total_count = len(results)
    
    for name, path, result in results:
        if result["status"] == "success":
            status_icon = "✅"
            status_text = f"HTTP {result['status_code']}"
        else:
            status_icon = "❌"
            status_text = f"ERROR - {result['error_type']}"
        
        print(f"{status_icon} {name} ({path}): {status_text}")
    
    print()
    if success_count == total_count:
        print("🎉 ALL ENDPOINTS WORKING - Deployment successful!")
        return 0
    elif success_count > 0:
        print(f"⚠️  Partial success: {success_count}/{total_count} endpoints working")
        return 1
    else:
        print("❌ DEPLOYMENT FAILED - No endpoints responding")
        return 2

def wait_for_deployment(max_wait_minutes: int = 5):
    """Wait for deployment to complete and then test."""
    print(f"⏳ Waiting up to {max_wait_minutes} minutes for Railway deployment...")
    
    for minute in range(max_wait_minutes):
        print(f"  Checking deployment status... ({minute + 1}/{max_wait_minutes})")
        
        # Test basic connectivity
        result = test_endpoint(f"{RAILWAY_URL}/health", timeout=5)
        if result["status"] == "success":
            print("✅ Deployment detected - running full verification...")
            return check_deployment()
        
        if minute < max_wait_minutes - 1:  # Don't sleep on last iteration
            time.sleep(60)
    
    print("⏰ Timeout waiting for deployment - running verification anyway...")
    return check_deployment()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        exit_code = wait_for_deployment()
    else:
        exit_code = check_deployment()
    
    exit(exit_code)