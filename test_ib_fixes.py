#!/usr/bin/env python3
"""
Test script to verify IB Integration fixes
Tests the critical components that were broken
"""

import sys
import traceback
from api.services.ib_connection_manager import IBConnectionManager
from api.models.ib_models import IBSettings

def test_connection_manager_initialization():
    """Test that connection manager initializes properly"""
    print("Testing connection manager initialization...")
    try:
        manager = IBConnectionManager()
        assert manager.is_connected == False
        assert manager.account == None
        assert manager.reconnect_attempts == 0
        assert manager.max_reconnect_attempts == 3
        print("✅ Connection manager initialization: PASSED")
        return True
    except Exception as e:
        print(f"❌ Connection manager initialization: FAILED - {e}")
        traceback.print_exc()
        return False

def test_connection_settings_property():
    """Test that connection_settings property can be set (for testing)"""
    print("\nTesting connection_settings property setter...")
    try:
        manager = IBConnectionManager()
        
        # Create mock settings
        mock_settings = IBSettings()
        mock_settings.host = '127.0.0.1'
        mock_settings.port = 7497
        mock_settings.client_id = 1
        mock_settings.account = 'TEST123'
        mock_settings.active = True
        
        # This should work now with our setter
        manager.connection_settings = mock_settings
        
        # Verify it was set
        assert manager.connection_settings == mock_settings
        assert manager.connection_settings.account == 'TEST123'
        print("✅ Connection settings property setter: PASSED")
        return True
    except Exception as e:
        print(f"❌ Connection settings property setter: FAILED - {e}")
        traceback.print_exc()
        return False

def test_encryption_methods():
    """Test that encryption/decryption methods exist and work"""
    print("\nTesting encryption methods...")
    try:
        manager = IBConnectionManager()
        
        # Test encryption
        test_password = "test_password_123"
        encrypted = manager.encrypt_credentials(test_password)
        assert encrypted != test_password
        
        # Test decryption
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == test_password
        
        print("✅ Encryption/decryption methods: PASSED")
        return True
    except Exception as e:
        print(f"❌ Encryption/decryption methods: FAILED - {e}")
        traceback.print_exc()
        return False

def test_health_monitor_methods():
    """Test that health monitor methods exist"""
    print("\nTesting health monitor methods...")
    try:
        manager = IBConnectionManager()
        
        # Test start method exists
        assert hasattr(manager, 'start_health_monitor')
        assert callable(manager.start_health_monitor)
        
        # Test stop method exists
        assert hasattr(manager, 'stop_health_monitor')
        assert callable(manager.stop_health_monitor)
        
        # Start and stop monitor
        manager.start_health_monitor(interval=5)
        manager.stop_health_monitor()
        
        print("✅ Health monitor methods: PASSED")
        return True
    except Exception as e:
        print(f"❌ Health monitor methods: FAILED - {e}")
        traceback.print_exc()
        return False

def test_ib_settings_model():
    """Test that IBSettings model has all required fields"""
    print("\nTesting IBSettings model fields...")
    try:
        settings = IBSettings()
        
        # Check new fields exist
        assert hasattr(settings, 'active')
        assert hasattr(settings, 'connection_timeout')
        assert hasattr(settings, 'retry_attempts')
        assert hasattr(settings, 'market_data_permissions')
        
        # Check defaults
        assert settings.active == True
        assert settings.connection_timeout == 10
        assert settings.retry_attempts == 3
        
        print("✅ IBSettings model fields: PASSED")
        return True
    except Exception as e:
        print(f"❌ IBSettings model fields: FAILED - {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("IB Integration Fix Verification Tests")
    print("=" * 60)
    
    tests = [
        test_connection_manager_initialization,
        test_connection_settings_property,
        test_encryption_methods,
        test_health_monitor_methods,
        test_ib_settings_model
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\nThe critical IB integration issues have been fixed!")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("\nThere are still issues to fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())