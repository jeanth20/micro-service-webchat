#!/usr/bin/env python3
"""
Debug script to test real-time messaging
"""

import asyncio
import websockets
import json
import requests
import time

async def test_websocket_messaging():
    """Test WebSocket messaging between two users"""
    
    # First, create test users via API
    base_url = "http://localhost:8000"
    
    print("🔧 Creating test users...")
    
    # Create user 1
    user1_data = {"username": "debug_user1"}
    response1 = requests.post(f"{base_url}/api/users/", json=user1_data)
    if response1.status_code == 200:
        user1 = response1.json()
        print(f"✓ Created user1: {user1['username']} (ID: {user1['id']})")
    else:
        # Try to get existing user
        response1 = requests.get(f"{base_url}/api/users/username/debug_user1")
        if response1.status_code == 200:
            user1 = response1.json()
            print(f"✓ Using existing user1: {user1['username']} (ID: {user1['id']})")
        else:
            print("❌ Failed to create/get user1")
            return
    
    # Create user 2
    user2_data = {"username": "debug_user2"}
    response2 = requests.post(f"{base_url}/api/users/", json=user2_data)
    if response2.status_code == 200:
        user2 = response2.json()
        print(f"✓ Created user2: {user2['username']} (ID: {user2['id']})")
    else:
        # Try to get existing user
        response2 = requests.get(f"{base_url}/api/users/username/debug_user2")
        if response2.status_code == 200:
            user2 = response2.json()
            print(f"✓ Using existing user2: {user2['username']} (ID: {user2['id']})")
        else:
            print("❌ Failed to create/get user2")
            return
    
    print(f"\n🔗 Testing WebSocket connections...")
    
    # Connect both users via WebSocket
    ws_url1 = f"ws://localhost:8000/ws/{user1['id']}"
    ws_url2 = f"ws://localhost:8000/ws/{user2['id']}"
    
    try:
        async with websockets.connect(ws_url1) as ws1, websockets.connect(ws_url2) as ws2:
            print(f"✓ WebSocket connected for user1: {ws_url1}")
            print(f"✓ WebSocket connected for user2: {ws_url2}")
            
            # Test message from user1 to user2
            message1 = {
                "type": "message",
                "content": "Hello from user1!",
                "message_type": "text",
                "receiver_id": user2["id"]
            }
            
            print(f"\n📤 Sending message from user1 to user2...")
            await ws1.send(json.dumps(message1))
            print(f"✓ Message sent: {message1['content']}")
            
            # Wait for message on user2's WebSocket
            try:
                response = await asyncio.wait_for(ws2.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✓ Message received by user2: {data}")
                
                if data.get("type") == "message" and data.get("message", {}).get("content") == message1["content"]:
                    print("✅ Real-time messaging is working!")
                else:
                    print("❌ Message content doesn't match")
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for message on user2's WebSocket")
                return False
            
            # Test message from user2 to user1
            message2 = {
                "type": "message",
                "content": "Hello back from user2!",
                "message_type": "text",
                "receiver_id": user1["id"]
            }
            
            print(f"\n📤 Sending message from user2 to user1...")
            await ws2.send(json.dumps(message2))
            print(f"✓ Message sent: {message2['content']}")
            
            # Wait for message on user1's WebSocket
            try:
                response = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✓ Message received by user1: {data}")
                
                if data.get("type") == "message" and data.get("message", {}).get("content") == message2["content"]:
                    print("✅ Bidirectional messaging is working!")
                    return True
                else:
                    print("❌ Message content doesn't match")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for message on user1's WebSocket")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False

def test_api_messaging():
    """Test API messaging"""
    base_url = "http://localhost:8000"
    
    print("\n🔧 Testing API messaging...")
    
    try:
        # Get users
        response1 = requests.get(f"{base_url}/api/users/username/debug_user1")
        response2 = requests.get(f"{base_url}/api/users/username/debug_user2")
        
        if response1.status_code == 200 and response2.status_code == 200:
            user1 = response1.json()
            user2 = response2.json()
            
            # Send message via API
            message_data = {
                "content": "API test message",
                "receiver_id": user2["id"],
                "message_type": "text"
            }
            
            response = requests.post(f"{base_url}/api/messages/", json=message_data)
            
            if response.status_code == 200:
                message = response.json()
                print(f"✓ Message sent via API: {message['content']}")
                
                # Get conversation to verify
                conv_response = requests.get(f"{base_url}/api/messages/conversation/{user1['id']}/{user2['id']}")
                if conv_response.status_code == 200:
                    messages = conv_response.json()
                    if messages and any(msg['content'] == message_data['content'] for msg in messages):
                        print("✅ API messaging is working!")
                        return True
                    else:
                        print("❌ Message not found in conversation")
                        return False
                else:
                    print("❌ Failed to get conversation")
                    return False
            else:
                print(f"❌ Failed to send message via API: {response.status_code}")
                return False
        else:
            print("❌ Failed to get test users")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

async def main():
    """Main debug function"""
    print("🐛 WebChat Real-time Debug Tool")
    print("=" * 50)
    
    # Test API first
    api_result = test_api_messaging()
    
    # Test WebSocket
    ws_result = await test_websocket_messaging()
    
    print("\n" + "=" * 50)
    print("📊 Debug Results:")
    print(f"  API Messaging: {'✅ Working' if api_result else '❌ Failed'}")
    print(f"  WebSocket Messaging: {'✅ Working' if ws_result else '❌ Failed'}")
    
    if api_result and ws_result:
        print("\n🎉 All real-time features are working correctly!")
        print("\n💡 To test in browser:")
        print("  1. Open: http://localhost:8000/?username=debug_user1")
        print("  2. Open: http://localhost:8000/?username=debug_user2")
        print("  3. Start chatting between the windows!")
    else:
        print("\n⚠️  Some issues detected. Check the server logs for more details.")
        print("\n🔧 Troubleshooting tips:")
        print("  • Make sure the server is running on http://localhost:8000")
        print("  • Check browser console for JavaScript errors")
        print("  • Verify WebSocket connections in browser dev tools")

if __name__ == "__main__":
    asyncio.run(main())
