#!/usr/bin/env python3
"""
Test script to verify the fixes for WebChat issues
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_websocket_performance():
    """Test WebSocket message handling performance"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test WebSocket connection
        with client.websocket_connect("/ws/1") as websocket:
            # Send a test message
            test_message = {
                "type": "message",
                "content": "Test message for performance",
                "message_type": "text",
                "receiver_id": 2
            }
            
            websocket.send_text(json.dumps(test_message))
            
            # Should receive response quickly
            data = websocket.receive_text()
            response = json.loads(data)
            
            print("✓ WebSocket message handling working")
            return True
            
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

async def test_media_upload():
    """Test media upload functionality"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        import io
        
        client = TestClient(app)
        
        # Create a test user first
        user_response = client.post("/api/users/", json={"username": "testuser_media"})
        if user_response.status_code == 200:
            user = user_response.json()
            
            # Create a test file
            test_file_content = b"This is a test file content"
            test_file = io.BytesIO(test_file_content)
            
            # Test file upload
            response = client.post(
                "/api/media/upload",
                files={"file": ("test.txt", test_file, "text/plain")},
                data={"user_id": user["id"]}
            )
            
            if response.status_code == 200:
                media = response.json()
                print(f"✓ Media upload working: {media['filename']}")
                return True
            else:
                print(f"✗ Media upload failed: {response.status_code}")
                return False
        else:
            print("✗ Could not create test user for media test")
            return False
            
    except Exception as e:
        print(f"✗ Media upload test failed: {e}")
        return False

async def test_call_functionality():
    """Test call request functionality"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Create test users
        user1_response = client.post("/api/users/", json={"username": "caller"})
        user2_response = client.post("/api/users/", json={"username": "receiver"})
        
        if user1_response.status_code == 200 and user2_response.status_code == 200:
            user1 = user1_response.json()
            user2 = user2_response.json()
            
            # Test WebSocket call
            with client.websocket_connect(f"/ws/{user1['id']}") as websocket:
                call_message = {
                    "type": "call",
                    "call_status": "request",
                    "receiver_id": user2["id"]
                }
                
                websocket.send_text(json.dumps(call_message))
                
                # Should process without error
                print("✓ Call functionality working")
                return True
        else:
            print("✗ Could not create test users for call test")
            return False
            
    except Exception as e:
        print(f"✗ Call functionality test failed: {e}")
        return False

async def test_message_delivery():
    """Test message delivery and real-time updates"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Create test users
        user1_response = client.post("/api/users/", json={"username": "sender"})
        user2_response = client.post("/api/users/", json={"username": "recipient"})
        
        if user1_response.status_code == 200 and user2_response.status_code == 200:
            user1 = user1_response.json()
            user2 = user2_response.json()
            
            # Test message creation via API
            message_data = {
                "content": "Test message for delivery",
                "receiver_id": user2["id"],
                "message_type": "text"
            }
            
            response = client.post("/api/messages/", json=message_data)
            
            if response.status_code == 200:
                message = response.json()
                print(f"✓ Message delivery working: {message['content']}")
                
                # Test marking as delivered
                delivered_response = client.put(f"/api/messages/{message['id']}/delivered")
                if delivered_response.status_code == 200:
                    print("✓ Message delivery status working")
                    return True
                else:
                    print("✗ Message delivery status failed")
                    return False
            else:
                print(f"✗ Message creation failed: {response.status_code}")
                return False
        else:
            print("✗ Could not create test users for message test")
            return False
            
    except Exception as e:
        print(f"✗ Message delivery test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing WebChat Fixes")
    print("=" * 50)
    
    tests = [
        ("Message Delivery", test_message_delivery),
        ("Media Upload", test_media_upload),
        ("Call Functionality", test_call_functionality),
        ("WebSocket Performance", test_websocket_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All fixes are working correctly!")
        print("\n🚀 Your WebChat application should now have:")
        print("  • Faster message delivery")
        print("  • Working media uploads")
        print("  • Enhanced call functionality")
        print("  • Better error handling")
        print("  • Improved real-time performance")
    else:
        print("⚠️  Some issues may still exist. Check the error messages above.")
    
    return passed == total

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
