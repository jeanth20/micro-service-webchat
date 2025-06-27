#!/usr/bin/env python3
"""
Quick WebChat Setup Script
A simpler alternative that creates tables directly without Alembic
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'static/uploads',
        'static/images',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_database_direct():
    """Setup database directly using SQLAlchemy"""
    try:
        from database import create_tables
        
        print("Creating database tables...")
        create_tables()
        print("✓ Database tables created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 WebChat Quick Setup")
    print("=" * 40)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Check .env file
    print("\n⚙️  Checking environment...")
    if not Path('.env').exists():
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from .env.example")
            print("Please edit .env file with your database credentials")
        else:
            print("✗ Please create a .env file with your database configuration")
            return False
    else:
        print("✓ .env file exists")
    
    # Setup database
    print("\n🗄️  Setting up database...")
    if not setup_database_direct():
        return False
    
    print("\n" + "=" * 40)
    print("✅ Quick setup completed!")
    print("\nTo start the application:")
    print("  python main.py")
    print("\nThen open: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
