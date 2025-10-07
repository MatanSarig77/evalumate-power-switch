#!/usr/bin/env python3
"""
Database Management Script for Power Switch

This script helps manage database migrations and backups.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask
from src.database import init_db, backup_database, restore_database, db, CustomerAnalysis

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure database URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customer_analysis.db'
    
    init_db(app)
    return app

def backup_to_file(filename=None):
    """Create a backup and save to file"""
    app = create_app()
    
    with app.app_context():
        backup_data = backup_database()
        if not backup_data:
            print("Failed to create backup")
            return False
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"Backup saved to {filename}")
        print(f"Total records: {backup_data['total_records']}")
        return True

def restore_from_file(filename):
    """Restore database from backup file"""
    app = create_app()
    
    try:
        with open(filename, 'r') as f:
            backup_data = json.load(f)
        
        with app.app_context():
            if restore_database(backup_data):
                print(f"Successfully restored {backup_data['total_records']} records")
                return True
            else:
                print("Failed to restore database")
                return False
    except FileNotFoundError:
        print(f"Backup file {filename} not found")
        return False
    except json.JSONDecodeError:
        print(f"Invalid JSON in backup file {filename}")
        return False

def show_stats():
    """Show database statistics"""
    app = create_app()
    
    with app.app_context():
        try:
            total = CustomerAnalysis.query.count()
            print(f"Total records in database: {total}")
            
            if total > 0:
                # Get some sample data
                recent = CustomerAnalysis.query.order_by(
                    CustomerAnalysis.analysis_timestamp.desc()
                ).limit(5).all()
                
                print("\nRecent analyses:")
                for analysis in recent:
                    print(f"  - {analysis.customer_name} ({analysis.selected_provider}) - ₪{analysis.monthly_savings_nis}")
        except Exception as e:
            print(f"Error getting stats: {e}")

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_db.py backup [filename]")
        print("  python manage_db.py restore <filename>")
        print("  python manage_db.py stats")
        return
    
    command = sys.argv[1]
    
    if command == "backup":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        backup_to_file(filename)
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Please specify backup filename")
            return
        restore_from_file(sys.argv[2])
    elif command == "stats":
        show_stats()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
