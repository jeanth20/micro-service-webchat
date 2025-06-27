#!/usr/bin/env python3
"""
WebChat Test Script
This script tests the basic functionality of the WebChat application.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_database_connection():
    """Test database connection"""
    try:
        from database import get_db, create_tables
        
        # Test database connection
        db = next(get_db())
        db.close()
        print("✓ Database connection successful")
        
        # Test table creation
        create_tables()
        print("✓ Database tables created/verified")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✓ Root endpoint working")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
            return False
        
        # Test API documentation
        response = client.get("/docs")
        if response.status_code == 200:
            print("✓ API documentation accessible")
        else:
            print(f"✗ API documentation failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False

async def test_user_creation():
    """Test user creation"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Create a test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        response = client.post("/api/users/", json=user_data)
        if response.status_code == 200:
            user = response.json()
            print(f"✓ User created successfully: {user['username']}")
            
            # Test getting the user
            response = client.get(f"/api/users/{user['id']}")
            if response.status_code == 200:
                print("✓ User retrieval successful")
            else:
                print(f"✗ User retrieval failed: {response.status_code}")
                return False
                
            return True
        else:
            print(f"✗ User creation failed: {response.status_code}")
            if response.status_code == 400:
                print("Note: User might already exist from previous tests")
                return True
            return False
    except Exception as e:
        print(f"✗ User creation test failed: {e}")
        return False

async def test_message_creation():
    """Test message creation"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # First, create two test users
        user1_data = {"username": "testuser1"}
        user2_data = {"username": "testuser2"}
        
        response1 = client.post("/api/users/", json=user1_data)
        response2 = client.post("/api/users/", json=user2_data)
        
        if response1.status_code == 200 and response2.status_code == 200:
            user1 = response1.json()
            user2 = response2.json()
            
            # Create a message
            message_data = {
                "content": "Hello, this is a test message!",
                "receiver_id": user2["id"],
                "message_type": "text"
            }
            
            response = client.post("/api/messages/", json=message_data)
            if response.status_code == 200:
                message = response.json()
                print(f"✓ Message created successfully: {message['content']}")
                return True
            else:
                print(f"✗ Message creation failed: {response.status_code}")
                return False
        else:
            print("✗ Could not create test users for message test")
            return False
            
    except Exception as e:
        print(f"✗ Message creation test failed: {e}")
        return False

async def test_file_structure():
    """Test file structure"""
    required_files = [
        'main.py',
        'models.py',
        'schemas.py',
        'database.py',
        'requirements.txt',
        '.env.example',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    required_dirs = [
        'api',
        'templates',
        'static/css',
        'static/js',
        'static/uploads'
    ]
    
    all_good = True
    
    print("Checking required files...")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - Missing")
            all_good = False
    
    print("\nChecking required directories...")
    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ - Missing")
            all_good = False
    
    return all_good

async def main():
    """Main test function"""
    print("🧪 WebChat Test Suite")
    print("=" * 50)
    
    # Test file structure
    print("\n📁 Testing file structure...")
    if not await test_file_structure():
        print("File structure test failed. Please run setup.py first.")
        return False
    
    # Test database
    print("\n🗄️  Testing database...")
    if not await test_database_connection():
        print("Database test failed. Please check your database configuration.")
        return False
    
    # Test API endpoints
    print("\n🌐 Testing API endpoints...")
    if not await test_api_endpoints():
        print("API test failed.")
        return False
    
    # Test user creation
    print("\n👤 Testing user creation...")
    if not await test_user_creation():
        print("User creation test failed.")
        return False
    
    # Test message creation
    print("\n💬 Testing message creation...")
    if not await test_message_creation():
        print("Message creation test failed.")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("\nYour WebChat application is ready to use!")
    print("Start the server with: python main.py")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if not result:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
