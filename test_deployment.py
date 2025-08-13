#!/usr/bin/env python3
"""
Test script to verify deployment readiness for Railway.
This script simulates the Railway environment and tests our FastAPI app.
"""
import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_docker_build():
    """Test if Docker image builds successfully."""
    print("🏗️  Testing Docker build...")
    
    try:
        # Build the Docker image
        result = subprocess.run([
            "docker", "build", "-t", "trade-strategies-test", "."
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Docker build failed:")
            print(result.stderr)
            return False
        
        print("✅ Docker build successful")
        return True
    except subprocess.TimeoutExpired:
        print("❌ Docker build timed out (5 minutes)")
        return False
    except FileNotFoundError:
        print("❌ Docker not found - install Docker to test build")
        return False

def test_local_startup():
    """Test if the app starts correctly with environment variables."""
    print("🚀 Testing local app startup...")
    
    # Set environment variables similar to Railway
    env = os.environ.copy()
    env['PORT'] = '8888'
    
    try:
        # Start the app
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8888"
        ], env=env)
        
        # Wait for startup
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8888/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health check passed")
                health_status = True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                health_status = False
        except requests.RequestException as e:
            print(f"❌ Health check failed: {e}")
            health_status = False
        
        # Test root endpoint
        try:
            response = requests.get("http://localhost:8888/", timeout=10)
            if response.status_code == 200:
                print("✅ Root endpoint accessible")
                root_status = True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                root_status = False
        except requests.RequestException as e:
            print(f"❌ Root endpoint failed: {e}")
            root_status = False
        
        # Terminate process
        process.terminate()
        process.wait(timeout=10)
        
        return health_status and root_status
        
    except Exception as e:
        print(f"❌ Local startup test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files are present."""
    print("📁 Testing file structure...")
    
    required_files = [
        "api/main.py",
        "api/routes/strategies.py", 
        "database/config.py",
        "services/",
        "requirements.txt",
        "Dockerfile",
        "railway.toml"
    ]
    
    missing_files = []
    for file_path in required_files:
        path = Path(file_path)
        if not path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_dependencies():
    """Test if all dependencies are installed."""
    print("📦 Testing dependencies...")
    
    try:
        import fastapi
        import uvicorn
        print("✅ Core dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    """Run all deployment readiness tests."""
    print("🔍 Running Railway Deployment Readiness Tests\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies), 
        ("Local Startup", test_local_startup),
        ("Docker Build", test_docker_build),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n{'='*50}")
    print("🎯 DEPLOYMENT READINESS SUMMARY")
    print(f"{'='*50}")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED - Ready for Railway deployment!")
        print(f"🚀 Push to GitHub to trigger Railway deployment")
        return 0
    else:
        print(f"\n⚠️  Some tests failed - fix issues before deploying")
        return 1

if __name__ == "__main__":
    exit(main())