#!/usr/bin/env python3
"""
Comprehensive test for WebChat real-time messaging and calls
"""

import asyncio
import websockets
import json
import requests
import time
import threading

class WebChatTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.users = []
        
    def create_test_users(self):
        """Create test users"""
        print("🔧 Creating test users...")
        
        test_users = [
            {"username": "realtime_alice", "email": "alice@test.com"},
            {"username": "realtime_bob", "email": "bob@test.com"}
        ]
        
        for user_data in test_users:
            try:
                response = requests.post(f"{self.base_url}/api/users/", json=user_data)
                
                if response.status_code == 200:
                    user = response.json()
                    self.users.append(user)
                    print(f"✓ Created user: {user['username']} (ID: {user['id']})")
                elif response.status_code == 400:
                    # User exists, get it
                    response = requests.get(f"{self.base_url}/api/users/username/{user_data['username']}")
                    if response.status_code == 200:
                        user = response.json()
                        self.users.append(user)
                        print(f"✓ Using existing user: {user['username']} (ID: {user['id']})")
                        
            except requests.exceptions.ConnectionError:
                print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
                return False
            except Exception as e:
                print(f"❌ Error creating user: {e}")
                return False
        
        return len(self.users) >= 2
    
    async def test_websocket_realtime(self):
        """Test real-time WebSocket messaging"""
        print("\n🔗 Testing WebSocket real-time messaging...")
        
        if len(self.users) < 2:
            print("❌ Need at least 2 users for testing")
            return False
        
        user1, user2 = self.users[0], self.users[1]
        
        ws_url1 = f"ws://localhost:8000/ws/{user1['id']}"
        ws_url2 = f"ws://localhost:8000/ws/{user2['id']}"
        
        try:
            async with websockets.connect(ws_url1) as ws1, websockets.connect(ws_url2) as ws2:
                print(f"✓ Connected both users via WebSocket")
                
                # Test message from user1 to user2
                test_message = {
                    "type": "message",
                    "content": f"Real-time test message {int(time.time())}",
                    "message_type": "text",
                    "receiver_id": user2["id"]
                }
                
                print(f"📤 Sending message from {user1['username']} to {user2['username']}")
                await ws1.send(json.dumps(test_message))
                
                # Wait for message on user2's WebSocket
                try:
                    response = await asyncio.wait_for(ws2.recv(), timeout=10.0)
                    data = json.loads(response)
                    print(f"📥 Received: {data}")
                    
                    if (data.get("type") == "message" and 
                        data.get("message", {}).get("content") == test_message["content"]):
                        print("✅ Real-time messaging working!")
                        
                        # Test reverse direction
                        reverse_message = {
                            "type": "message",
                            "content": f"Reply message {int(time.time())}",
                            "message_type": "text",
                            "receiver_id": user1["id"]
                        }
                        
                        print(f"📤 Sending reply from {user2['username']} to {user1['username']}")
                        await ws2.send(json.dumps(reverse_message))
                        
                        # Wait for reply
                        reply_response = await asyncio.wait_for(ws1.recv(), timeout=10.0)
                        reply_data = json.loads(reply_response)
                        
                        if (reply_data.get("type") == "message" and 
                            reply_data.get("message", {}).get("content") == reverse_message["content"]):
                            print("✅ Bidirectional messaging working!")
                            return True
                        else:
                            print("❌ Reply message not received correctly")
                            return False
                    else:
                        print("❌ Message not received correctly")
                        print(f"Expected: {test_message['content']}")
                        print(f"Received: {data.get('message', {}).get('content')}")
                        return False
                        
                except asyncio.TimeoutError:
                    print("❌ Timeout waiting for message")
                    return False
                    
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    async def test_call_functionality(self):
        """Test call request functionality"""
        print("\n📞 Testing call functionality...")
        
        if len(self.users) < 2:
            print("❌ Need at least 2 users for testing")
            return False
        
        user1, user2 = self.users[0], self.users[1]
        
        ws_url1 = f"ws://localhost:8000/ws/{user1['id']}"
        ws_url2 = f"ws://localhost:8000/ws/{user2['id']}"
        
        try:
            async with websockets.connect(ws_url1) as ws1, websockets.connect(ws_url2) as ws2:
                print(f"✓ Connected both users for call test")
                
                # Send call request
                call_request = {
                    "type": "call",
                    "call_status": "request",
                    "call_type": "audio",
                    "call_id": f"test_call_{int(time.time())}",
                    "receiver_id": user2["id"]
                }
                
                print(f"📞 Sending call request from {user1['username']} to {user2['username']}")
                await ws1.send(json.dumps(call_request))
                
                # Wait for call request on user2's WebSocket
                try:
                    response = await asyncio.wait_for(ws2.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"📥 Call request received: {data}")
                    
                    if (data.get("type") == "call" and 
                        data.get("call_status") == "request"):
                        print("✅ Call request functionality working!")
                        
                        # Send call accept
                        call_accept = {
                            "type": "call",
                            "call_status": "accept",
                            "call_id": call_request["call_id"]
                        }
                        
                        print(f"📞 Sending call accept from {user2['username']}")
                        await ws2.send(json.dumps(call_accept))
                        
                        # Wait for accept confirmation
                        accept_response = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                        accept_data = json.loads(accept_response)
                        
                        if (accept_data.get("type") == "call" and 
                            accept_data.get("call_status") == "accept"):
                            print("✅ Call accept functionality working!")
                            return True
                        else:
                            print("❌ Call accept not received correctly")
                            return False
                    else:
                        print("❌ Call request not received correctly")
                        return False
                        
                except asyncio.TimeoutError:
                    print("❌ Timeout waiting for call request")
                    return False
                    
        except Exception as e:
            print(f"❌ Call test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🌐 Testing API endpoints...")
        
        try:
            # Test message creation
            if len(self.users) >= 2:
                user1, user2 = self.users[0], self.users[1]
                
                message_data = {
                    "content": f"API test message {int(time.time())}",
                    "receiver_id": user2["id"],
                    "message_type": "text"
                }
                
                response = requests.post(f"{self.base_url}/api/messages/", json=message_data)
                
                if response.status_code == 200:
                    message = response.json()
                    print(f"✅ API message creation working: {message['content']}")
                    
                    # Test conversation retrieval
                    conv_response = requests.get(
                        f"{self.base_url}/api/messages/conversation/{user1['id']}/{user2['id']}"
                    )
                    
                    if conv_response.status_code == 200:
                        messages = conv_response.json()
                        if any(msg['content'] == message_data['content'] for msg in messages):
                            print("✅ API conversation retrieval working!")
                            return True
                        else:
                            print("❌ Message not found in conversation")
                            return False
                    else:
                        print("❌ Failed to retrieve conversation")
                        return False
                else:
                    print(f"❌ Failed to create message via API: {response.status_code}")
                    return False
            else:
                print("❌ Need users for API testing")
                return False
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 WebChat Comprehensive Real-time Test")
        print("=" * 60)
        
        # Create users
        if not self.create_test_users():
            print("❌ Failed to create test users")
            return False
        
        # Test API
        api_result = self.test_api_endpoints()
        
        # Test WebSocket messaging
        ws_result = await self.test_websocket_realtime()
        
        # Test call functionality
        call_result = await self.test_call_functionality()
        
        # Results
        print("\n" + "=" * 60)
        print("📊 Test Results:")
        print(f"  API Endpoints: {'✅ PASS' if api_result else '❌ FAIL'}")
        print(f"  Real-time Messaging: {'✅ PASS' if ws_result else '❌ FAIL'}")
        print(f"  Call Functionality: {'✅ PASS' if call_result else '❌ FAIL'}")
        
        all_passed = api_result and ws_result and call_result
        
        if all_passed:
            print("\n🎉 All tests PASSED! Your WebChat is working perfectly!")
            print("\n💡 Ready for testing:")
            print(f"  User 1: http://localhost:8000/?user_id={self.users[0]['id']} ({self.users[0]['username']})")
            print(f"  User 2: http://localhost:8000/?user_id={self.users[1]['id']} ({self.users[1]['username']})")
            print("\n🚀 Features working:")
            print("  ✅ Real-time messaging")
            print("  ✅ WebSocket connections")
            print("  ✅ Call requests")
            print("  ✅ API endpoints")
        else:
            print("\n⚠️  Some tests failed. Check the server logs and try again.")
            print("\n🔧 Troubleshooting:")
            print("  • Make sure the server is running: python main.py")
            print("  • Check browser console for errors")
            print("  • Verify WebSocket connections")
        
        return all_passed

async def main():
    tester = WebChatTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
