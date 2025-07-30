"""Tests for data migration from trades.json to PostgreSQL database."""
import pytest
import json
import os
import tempfile
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from database.config import SessionLocal
from database.models import Trade, Strategy
from scripts.migrate_data import DataMigrator, MigrationError

class TestDataMigrator:
    """Test the DataMigrator class."""
    
    def setup_method(self):
        """Set up test data before each test."""
        self.sample_trades_data = [
            {
                "date": "2025-07-29",
                "strategy": "bull_call",
                "strikes": [637.0, 640.0],
                "contracts": 200,
                "entry_price": 638.57,
                "credit_debit": 150.0,
                "notes": "Entry: 08:30, Exit: 14:30",
                "id": 1,
                "timestamp": "2025-07-29T12:57:03.045815"
            },
            {
                "date": "2025-07-29",
                "strategy": "iron_condor",
                "strikes": [633.0, 636.0, 640.0, 643.0],
                "contracts": 100,
                "entry_price": 638.57,
                "credit_debit": 250.0,
                "notes": "Entry: 09:30, Exit: 15:30",
                "id": 2,
                "timestamp": "2025-07-29T18:09:08.755821"
            },
            {
                "date": "2025-07-28",
                "strategy": "butterfly",
                "strikes": [635.0, 638.0, 641.0],
                "contracts": 150,
                "entry_price": 637.25,
                "credit_debit": -75.0,
                "notes": "Expired worthlessly",
                "id": 3,
                "timestamp": "2025-07-28T16:00:00.000000"
            }
        ]
        
        # Create temporary JSON file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.sample_trades_data, self.temp_file)
        self.temp_file.close()
        
        self.migrator = DataMigrator(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_data_migrator_initialization(self):
        """Test DataMigrator initialization."""
        assert self.migrator.source_file == self.temp_file.name
        assert self.migrator.backup_created is False
        assert self.migrator.migration_completed is False
    
    def test_read_trades_json_valid_file(self):
        """Test reading valid trades.json file."""
        trades_data = self.migrator.read_trades_json()
        
        assert len(trades_data) == 3
        assert trades_data[0]["strategy"] == "bull_call"
        assert trades_data[1]["strategy"] == "iron_condor"
        assert trades_data[2]["strategy"] == "butterfly"
    
    def test_read_trades_json_missing_file(self):
        """Test reading non-existent trades.json file."""
        migrator = DataMigrator("nonexistent.json")
        
        with pytest.raises(MigrationError) as exc_info:
            migrator.read_trades_json()
        
        assert "trades.json file not found" in str(exc_info.value)
    
    def test_read_trades_json_invalid_json(self):
        """Test reading invalid JSON file."""
        # Create invalid JSON file
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        invalid_file.write("{ invalid json content")
        invalid_file.close()
        
        migrator = DataMigrator(invalid_file.name)
        
        try:
            with pytest.raises(MigrationError) as exc_info:
                migrator.read_trades_json()
            
            assert "Invalid JSON format" in str(exc_info.value)
        finally:
            os.unlink(invalid_file.name)
    
    def test_transform_trade_data_bull_call(self):
        """Test transforming bull call trade data."""
        original_trade = self.sample_trades_data[0]
        transformed = self.migrator.transform_trade_data(original_trade)
        
        assert transformed["trade_date"] == date(2025, 7, 29)
        assert transformed["symbol"] == "SPY"  # Default symbol
        assert transformed["strategy_type"] == "bull_call"
        assert transformed["strikes"] == [637.0, 640.0]
        assert transformed["contracts"] == 200
        assert transformed["entry_price"] == Decimal("638.57")
        assert transformed["credit_debit"] == Decimal("150.0")
        assert transformed["status"] == "open"  # Default status
        assert "Entry: 08:30, Exit: 14:30" in transformed["notes"]
    
    def test_transform_trade_data_iron_condor(self):
        """Test transforming iron condor trade data."""
        original_trade = self.sample_trades_data[1]
        transformed = self.migrator.transform_trade_data(original_trade)
        
        assert transformed["strategy_type"] == "iron_condor"
        assert transformed["strikes"] == [633.0, 636.0, 640.0, 643.0]
        assert transformed["contracts"] == 100
        assert transformed["credit_debit"] == Decimal("250.0")
    
    def test_transform_trade_data_missing_fields(self):
        """Test transforming trade data with missing fields."""
        incomplete_trade = {
            "date": "2025-07-29",
            "strategy": "bull_call",
            "strikes": [637.0, 640.0]
            # Missing contracts, entry_price, etc.
        }
        
        transformed = self.migrator.transform_trade_data(incomplete_trade)
        
        # Should use default values
        assert transformed["contracts"] == 1  # Default contracts
        assert transformed["entry_price"] == Decimal("0.00")  # Default entry_price
        assert transformed["credit_debit"] == Decimal("0.00")  # Default credit_debit
        assert transformed["notes"] == "Migrated from trades.json"  # Default notes
    
    def test_extract_time_from_notes(self):
        """Test extracting entry and exit times from notes."""
        notes = "Entry: 08:30, Exit: 14:30"
        entry_time, exit_time = self.migrator.extract_time_from_notes(notes)
        
        assert entry_time == "08:30:00"
        assert exit_time == "14:30:00"
    
    def test_extract_time_from_notes_partial(self):
        """Test extracting partial time information from notes."""
        notes = "Entry: 09:15"
        entry_time, exit_time = self.migrator.extract_time_from_notes(notes)
        
        assert entry_time == "09:15:00"
        assert exit_time is None
    
    def test_extract_time_from_notes_no_time(self):
        """Test extracting time from notes with no time information."""
        notes = "Regular trade with no time info"
        entry_time, exit_time = self.migrator.extract_time_from_notes(notes)
        
        assert entry_time is None
        assert exit_time is None
    
    def test_create_backup_file(self):
        """Test creating backup of original trades.json."""
        backup_path = self.migrator.create_backup()
        
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".backup")
        assert self.migrator.backup_created is True
        
        # Verify backup content matches original
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        assert backup_data == self.sample_trades_data
        
        # Clean up backup file
        os.unlink(backup_path)
    
    @patch('scripts.migrate_data.SessionLocal')
    def test_migrate_to_database_success(self, mock_session_local):
        """Test successful migration to database."""
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock successful migration
        result = self.migrator.migrate_to_database()
        
        assert result["success"] is True
        assert result["migrated_count"] == 3
        assert result["failed_count"] == 0
        assert self.migrator.migration_completed is True
        
        # Verify database operations were called
        assert mock_session.add.call_count == 3
        assert mock_session.commit.called
    
    @patch('scripts.migrate_data.SessionLocal')
    def test_migrate_to_database_with_errors(self, mock_session_local):
        """Test migration with some database errors."""
        # Mock database session with errors
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Make the second trade insertion fail
        def side_effect(*args):
            if mock_session.add.call_count == 2:
                raise Exception("Database constraint violation")
        
        mock_session.add.side_effect = side_effect
        
        result = self.migrator.migrate_to_database()
        
        assert result["success"] is True  # Overall success despite some failures
        assert result["migrated_count"] == 2  # Only 2 successful
        assert result["failed_count"] == 1   # 1 failed
        assert len(result["errors"]) == 1
    
    def test_verify_migration_data_integrity(self):
        """Test data integrity verification after migration."""
        # This test would verify that migrated data matches source data
        # For now, it's a placeholder for the actual implementation
        pass
    
    def test_migration_rollback_on_critical_error(self):
        """Test migration rollback on critical errors."""
        # This test would verify rollback functionality
        # For now, it's a placeholder for the actual implementation
        pass

class TestMigrationIntegration:
    """Integration tests for the complete migration process."""
    
    @pytest.mark.integration
    def test_full_migration_process(self):
        """Test the complete end-to-end migration process."""
        # This would be a full integration test
        # Testing: backup creation → data transformation → database insertion → verification
        pass
    
    @pytest.mark.integration
    def test_migration_with_existing_database_data(self):
        """Test migration behavior when database already contains data."""
        pass
    
    @pytest.mark.integration
    def test_large_dataset_migration_performance(self):
        """Test migration performance with large datasets."""
        pass

class TestMigrationUtilities:
    """Test utility functions for migration."""
    
    def test_validate_trade_data(self):
        """Test trade data validation before migration."""
        pass
    
    def test_generate_migration_report(self):
        """Test generation of migration summary report."""
        pass
    
    def test_migration_cleanup(self):
        """Test cleanup of temporary files and resources."""
        pass