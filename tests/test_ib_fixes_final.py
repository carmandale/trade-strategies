#!/usr/bin/env python3
"""
Final validation test for IB Integration fixes
Tests ONLY the critical fixes we made, avoiding database/IB connection requirements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch
from api.services.ib_connection_manager import IBConnectionManager
from api.models.ib_models import IBSettings

def test_fixes():
    """Test all the critical fixes we made"""
    
    print("=" * 60)
    print("IB Integration Phase 1 Fix Validation")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Connection settings property can be set
    print("\n1. Testing connection_settings property setter...")
    try:
        manager = IBConnectionManager()
        mock_settings = Mock(spec=IBSettings)
        mock_settings.account = 'TEST123'
        
        # This should work with our fix
        manager.connection_settings = mock_settings
        assert manager._connection_settings == mock_settings
        print("   ✅ PASSED: Property setter works")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 2: IBSettings has required fields
    print("\n2. Testing IBSettings model has new fields...")
    try:
        settings = IBSettings()
        assert hasattr(settings, 'active')
        assert hasattr(settings, 'connection_timeout')
        assert hasattr(settings, 'retry_attempts')
        assert hasattr(settings, 'market_data_permissions')
        
        # Check defaults
        assert settings.active == True
        assert settings.connection_timeout == 10
        assert settings.retry_attempts == 3
        print("   ✅ PASSED: All new fields present with correct defaults")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 3: Encryption methods exist
    print("\n3. Testing encryption methods exist...")
    try:
        manager = IBConnectionManager()
        assert hasattr(manager, 'encrypt_credentials')
        assert hasattr(manager, 'decrypt_credentials')
        assert callable(manager.encrypt_credentials)
        assert callable(manager.decrypt_credentials)
        
        # Test they actually work
        test_password = "test123"
        encrypted = manager.encrypt_credentials(test_password)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == test_password
        print("   ✅ PASSED: Encryption/decryption works")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 4: Health monitor methods exist
    print("\n4. Testing health monitor methods exist...")
    try:
        manager = IBConnectionManager()
        assert hasattr(manager, 'start_health_monitor')
        assert hasattr(manager, 'stop_health_monitor')
        assert callable(manager.start_health_monitor)
        assert callable(manager.stop_health_monitor)
        print("   ✅ PASSED: Health monitor methods present")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 5: Connect method returns dict (not boolean)
    print("\n5. Testing connect method returns proper dict...")
    try:
        with patch('api.services.ib_connection_manager.IB'):
            manager = IBConnectionManager()
            mock_settings = Mock(spec=IBSettings)
            mock_settings.host = '127.0.0.1'
            mock_settings.port = 7497
            mock_settings.account = 'TEST'
            manager.connection_settings = mock_settings
            
            # Mock the database session
            with patch.object(manager, 'get_db_session'):
                result = manager.connect()
                assert isinstance(result, dict)
                assert 'success' in result
                assert 'message' in result
                assert 'status' in result
                print("   ✅ PASSED: Connect returns proper dict structure")
                tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 6: _log_connection_event has correct signature
    print("\n6. Testing _log_connection_event signature...")
    try:
        manager = IBConnectionManager()
        import inspect
        sig = inspect.signature(manager._log_connection_event)
        params = list(sig.parameters.keys())
        assert 'event_type' in params
        assert 'status' in params
        assert 'account' in params
        assert 'error' in params
        assert 'metadata' not in params  # Should NOT have metadata
        print("   ✅ PASSED: Method has correct parameters")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    total = tests_passed + tests_failed
    print(f"Tests Passed: {tests_passed}/{total}")
    print(f"Tests Failed: {tests_failed}/{total}")
    
    if tests_failed == 0:
        print("\n✅ ALL CRITICAL FIXES VALIDATED!")
        print("\nThe Phase 1 foundation fixes are working correctly.")
        print("The system is ready for Phase 2 development.")
        return 0
    else:
        print(f"\n❌ {tests_failed} tests still failing")
        print("Additional fixes needed.")
        return 1

if __name__ == "__main__":
    sys.exit(test_fixes())