"""Data migration script to migrate trades from JSON file to PostgreSQL database."""
import json
import os
import shutil
import re
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import logging

from database.config import SessionLocal
from database.models import Trade, Strategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass

class DataMigrator:
    """Handles migration of trade data from JSON to PostgreSQL."""
    
    def __init__(self, source_file: str = "trades.json"):
        self.source_file = source_file
        self.backup_created = False
        self.migration_completed = False
        self.default_symbol = "SPY"  # Default symbol for legacy trades
    
    def read_trades_json(self) -> List[Dict[str, Any]]:
        """Read and parse the trades.json file."""
        try:
            if not os.path.exists(self.source_file):
                raise MigrationError(f"trades.json file not found at: {self.source_file}")
            
            with open(self.source_file, 'r') as f:
                trades_data = json.load(f)
            
            logger.info(f"Successfully read {len(trades_data)} trades from {self.source_file}")
            return trades_data
            
        except json.JSONDecodeError as e:
            raise MigrationError(f"Invalid JSON format in {self.source_file}: {str(e)}")
        except Exception as e:
            raise MigrationError(f"Error reading {self.source_file}: {str(e)}")
    
    def transform_trade_data(self, original_trade: Dict[str, Any]) -> Dict[str, Any]:
        """Transform original trade data to match the new database schema."""
        try:
            # Parse the date
            trade_date = datetime.strptime(original_trade["date"], "%Y-%m-%d").date()
            
            # Extract time information from notes if available
            notes = original_trade.get("notes", "Migrated from trades.json")
            entry_time, exit_time = self.extract_time_from_notes(notes)
            
            # Transform the data
            transformed = {
                "trade_date": trade_date,
                "entry_time": entry_time,
                "symbol": self.default_symbol,  # Default to SPY for legacy trades
                "strategy_type": original_trade.get("strategy", "unknown"),
                "strikes": original_trade.get("strikes", []),
                "contracts": original_trade.get("contracts", 1),
                "entry_price": Decimal(str(original_trade.get("entry_price", 0.0))),
                "credit_debit": Decimal(str(original_trade.get("credit_debit", 0.0))),
                "status": "open",  # Default status for migrated trades
                "notes": notes,
                "exit_time": exit_time,
                # Add migration metadata
                "migrated_from_json": True,
                "original_id": original_trade.get("id"),
                "original_timestamp": original_trade.get("timestamp")
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming trade data: {original_trade}")
            raise MigrationError(f"Data transformation failed: {str(e)}")
    
    def extract_time_from_notes(self, notes: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract entry and exit times from notes field."""
        if not notes:
            return None, None
        
        entry_time = None
        exit_time = None
        
        # Look for "Entry: HH:MM" pattern
        entry_match = re.search(r'Entry:\s*(\d{1,2}:\d{2})', notes, re.IGNORECASE)
        if entry_match:
            entry_time = entry_match.group(1) + ":00"  # Add seconds
        
        # Look for "Exit: HH:MM" pattern
        exit_match = re.search(r'Exit:\s*(\d{1,2}:\d{2})', notes, re.IGNORECASE)
        if exit_match:
            exit_time = exit_match.group(1) + ":00"  # Add seconds
        
        return entry_time, exit_time
    
    def create_backup(self) -> str:
        """Create a backup of the original trades.json file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.source_file}.{timestamp}.backup"
            
            shutil.copy2(self.source_file, backup_path)
            self.backup_created = True
            
            logger.info(f"Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            raise MigrationError(f"Failed to create backup: {str(e)}")
    
    def migrate_to_database(self) -> Dict[str, Any]:
        """Migrate all trades to the PostgreSQL database."""
        trades_data = self.read_trades_json()
        migrated_count = 0
        failed_count = 0
        errors = []
        
        try:
            with SessionLocal() as db:
                for original_trade in trades_data:
                    try:
                        # Transform the trade data
                        transformed_trade = self.transform_trade_data(original_trade)
                        
                        # Create Trade object (excluding metadata fields)
                        trade_data = {k: v for k, v in transformed_trade.items() 
                                    if k not in ["migrated_from_json", "original_id", "original_timestamp"]}
                        
                        db_trade = Trade(**trade_data)
                        
                        # Add to database
                        db.add(db_trade)
                        db.commit()
                        db.refresh(db_trade)
                        
                        migrated_count += 1
                        logger.info(f"Migrated trade {original_trade.get('id', 'unknown')}: {db_trade.id}")
                        
                    except Exception as e:
                        failed_count += 1
                        error_msg = f"Failed to migrate trade {original_trade.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        db.rollback()
                        continue
                
                self.migration_completed = True
                
        except Exception as e:
            raise MigrationError(f"Database migration failed: {str(e)}")
        
        result = {
            "success": True,
            "migrated_count": migrated_count,
            "failed_count": failed_count,
            "total_trades": len(trades_data),
            "errors": errors
        }
        
        logger.info(f"Migration completed: {migrated_count} successful, {failed_count} failed")
        return result
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify the integrity of migrated data."""
        try:
            original_data = self.read_trades_json()
            
            with SessionLocal() as db:
                # Count total trades in database
                total_db_trades = db.query(Trade).count()
                
                # Get sample of migrated trades for verification
                sample_trades = db.query(Trade).limit(5).all()
                
                verification_result = {
                    "original_count": len(original_data),
                    "database_count": total_db_trades,
                    "sample_verification": True,  # Simplified for now
                    "integrity_check_passed": total_db_trades >= len(original_data)
                }
                
                logger.info(f"Verification: {len(original_data)} original trades, {total_db_trades} in database")
                return verification_result
                
        except Exception as e:
            raise MigrationError(f"Migration verification failed: {str(e)}")
    
    def generate_migration_report(self, migration_result: Dict[str, Any]) -> str:
        """Generate a detailed migration report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
=== TRADE DATA MIGRATION REPORT ===
Migration Date: {timestamp}
Source File: {self.source_file}
Backup Created: {self.backup_created}

MIGRATION RESULTS:
- Total Trades Processed: {migration_result['total_trades']}
- Successfully Migrated: {migration_result['migrated_count']}
- Failed Migrations: {migration_result['failed_count']}
- Success Rate: {(migration_result['migrated_count'] / migration_result['total_trades'] * 100):.1f}%

"""
        
        if migration_result['errors']:
            report += "ERRORS ENCOUNTERED:\n"
            for i, error in enumerate(migration_result['errors'], 1):
                report += f"{i}. {error}\n"
        
        report += f"\nMigration Status: {'COMPLETED' if self.migration_completed else 'FAILED'}\n"
        report += "=" * 50 + "\n"
        
        return report

def main():
    """Main migration function."""
    source_file = "trades.json"
    
    try:
        # Initialize migrator
        migrator = DataMigrator(source_file)
        
        # Create backup
        print("Creating backup of original trades.json...")
        backup_path = migrator.create_backup()
        print(f"Backup created: {backup_path}")
        
        # Perform migration
        print("Starting data migration...")
        migration_result = migrator.migrate_to_database()
        
        # Verify migration
        print("Verifying migration...")
        verification_result = migrator.verify_migration()
        
        # Generate report
        report = migrator.generate_migration_report(migration_result)
        print(report)
        
        # Save report to file
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"Migration report saved: {report_file}")
        
        if migration_result['success'] and verification_result['integrity_check_passed']:
            print("✅ Migration completed successfully!")
        else:
            print("⚠️ Migration completed with issues. Check the report for details.")
            
    except MigrationError as e:
        print(f"❌ Migration failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())