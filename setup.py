#!/usr/bin/env python3
"""
WebChat Setup Script
This script helps set up the WebChat application by creating necessary directories
and initializing the database.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'static/uploads',
        'static/images',
        'static/css',
        'static/js',
        'templates',
        'alembic/versions'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import sqlalchemy
        import psycopg2
        import uvicorn
        print("✓ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_postgresql():
    """Check if PostgreSQL is accessible"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("✗ DATABASE_URL not found in .env file")
            return False
            
        # Try to connect
        conn = psycopg2.connect(database_url)
        conn.close()
        print("✓ PostgreSQL connection successful")
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("Please check your DATABASE_URL in .env file")
        return False

def setup_database():
    """Initialize database with Alembic"""
    try:
        # Check if alembic is initialized
        if not Path('alembic/env.py').exists():
            print("Initializing Alembic...")
            subprocess.run(['alembic', 'init', 'alembic'], check=True)
            print("✓ Alembic initialized")
        else:
            print("✓ Alembic already initialized")

        # Check if there are any migration files
        versions_dir = Path('alembic/versions')
        migration_files = list(versions_dir.glob('*.py'))
        migration_files = [f for f in migration_files if f.name != '__pycache__']

        if not migration_files:
            print("Creating initial migration...")
            subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'Initial migration'], check=True)
            print("✓ Initial migration created")
        else:
            print("✓ Migration files already exist")

        # Apply migrations
        print("Applying migrations...")
        subprocess.run(['alembic', 'upgrade', 'head'], check=True)
        print("✓ Database migrations applied")

        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Database setup failed: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not Path('.env').exists():
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from .env.example")
            print("Please edit .env file with your database credentials")
        else:
            print("✗ .env.example file not found")
            return False
    else:
        print("✓ .env file already exists")
    return True

def main():
    """Main setup function"""
    print("🚀 WebChat Setup Script")
    print("=" * 50)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Create .env file
    print("\n⚙️  Setting up environment...")
    if not create_env_file():
        print("Please create a .env file with your configuration")
        sys.exit(1)
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Check PostgreSQL
    print("\n🐘 Checking PostgreSQL connection...")
    if not check_postgresql():
        print("Please set up PostgreSQL and update your .env file")
        sys.exit(1)
    
    # Setup database
    print("\n🗄️  Setting up database...")
    if not setup_database():
        print("Database setup failed. Please check your configuration")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nTo start the application, run:")
    print("  python main.py")
    print("\nOr:")
    print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nThen open your browser to: http://localhost:8000")

if __name__ == "__main__":
    main()
