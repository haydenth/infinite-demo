#!/usr/bin/env python3
"""
Migration management script for the onramp service
Usage:
  python migrate.py init     # Initialize migrations
  python migrate.py migrate # Create new migration
  python migrate.py upgrade # Run migrations
  python migrate.py --help  # Show help
"""

import sys
import os
from flask import Flask
from flask_migrate import Migrate, init, migrate as create_migration, upgrade
from models import db

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Database configuration
    postgres_user = os.environ.get('POSTGRES_USER', 'postgres')
    postgres_pass = os.environ.get('POSTGRES_PASSWORD', 'password')
    postgres_db = os.environ.get('POSTGRES_DB', 'infinite_dev')
    postgres_host = os.environ.get('POSTGRES_HOST', 'localhost')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{postgres_user}:{postgres_pass}@{postgres_host}:5432/{postgres_db}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    return app

def show_help():
    print(__doc__)
    print("Available commands:")
    print("  init     - Initialize migration repository")
    print("  migrate  - Generate a new migration")
    print("  upgrade  - Apply pending migrations")
    print("  help     - Show this help message")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['--help', '-h', 'help']:
        show_help()
        return
    
    app = create_app()
    migrate = Migrate(app, db)
    
    with app.app_context():
        if command == 'init':
            try:
                init()
                print("✓ Migration repository initialized")
            except Exception as e:
                print(f"✗ Failed to initialize: {e}")
                
        elif command == 'migrate':
            message = input("Migration message (optional): ").strip()
            try:
                create_migration(message=message or None)
                print("✓ Migration created successfully")
            except Exception as e:
                print(f"✗ Failed to create migration: {e}")
                
        elif command == 'upgrade':
            try:
                upgrade()
                print("✓ Migrations applied successfully")
            except Exception as e:
                print(f"✗ Failed to apply migrations: {e}")
                
        else:
            print(f"Unknown command: {command}")
            show_help()

if __name__ == '__main__':
    main()
