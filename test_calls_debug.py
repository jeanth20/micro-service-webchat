#!/usr/bin/env python3
"""
Debug script specifically for call functionality
"""

import asyncio
import websockets
import json
import requests
import time

async def test_call_flow():
    """Test the complete call flow"""
    
    base_url = "http://localhost:8000"
    
    print("🔧 Setting up call test...")
    
    # Create/get test users
    users = []
    for username in ["call_user1", "call_user2"]:
        try:
            response = requests.post(f"{base_url}/api/users/", json={"username": username})
            if response.status_code == 200:
                user = response.json()
                users.append(user)
                print(f"✓ Created user: {user['username']} (ID: {user['id']})")
            else:
                # Try to get existing user
                response = requests.get(f"{base_url}/api/users/username/{username}")
                if response.status_code == 200:
                    user = response.json()
                    users.append(user)
                    print(f"✓ Using existing user: {user['username']} (ID: {user['id']})")
        except Exception as e:
            print(f"❌ Error with user {username}: {e}")
            return False
    
    if len(users) < 2:
        print("❌ Need 2 users for call testing")
        return False
    
    user1, user2 = users[0], users[1]
    
    print(f"\n📞 Testing call flow between {user1['username']} and {user2['username']}")
    
    # Connect both users
    ws_url1 = f"ws://localhost:8000/ws/{user1['id']}"
    ws_url2 = f"ws://localhost:8000/ws/{user2['id']}"
    
    try:
        async with websockets.connect(ws_url1) as ws1, websockets.connect(ws_url2) as ws2:
            print("✓ Both users connected via WebSocket")
            
            # Step 1: User1 initiates call to User2
            call_request = {
                "type": "call",
                "call_status": "request",
                "call_type": "audio",
                "call_id": f"test_call_{int(time.time())}",
                "receiver_id": user2["id"]
            }
            
            print(f"\n📤 Step 1: {user1['username']} initiating call...")
            print(f"Sending: {call_request}")
            await ws1.send(json.dumps(call_request))
            
            # Step 2: User2 should receive call request
            print(f"\n📥 Step 2: Waiting for call request on {user2['username']}'s WebSocket...")
            try:
                response = await asyncio.wait_for(ws2.recv(), timeout=10.0)
                call_data = json.loads(response)
                print(f"Received: {call_data}")
                
                # Verify call request structure
                if call_data.get("type") == "call":
                    call_status = call_data.get("call_status") or call_data.get("call_log", {}).get("call_status")
                    call_type = call_data.get("call_type")
                    call_id = call_data.get("call_id")
                    caller_id = call_data.get("caller_id") or call_data.get("call_log", {}).get("caller_id")
                    
                    print(f"✓ Call request received:")
                    print(f"  Status: {call_status}")
                    print(f"  Type: {call_type}")
                    print(f"  ID: {call_id}")
                    print(f"  Caller: {caller_id}")
                    
                    if call_status == "request" and caller_id == user1["id"]:
                        print("✅ Call request structure is correct!")
                        
                        # Step 3: User2 accepts the call
                        call_accept = {
                            "type": "call",
                            "call_status": "accept",
                            "call_type": call_type or "audio",
                            "call_id": call_id or call_request["call_id"],
                            "receiver_id": caller_id
                        }
                        
                        print(f"\n📤 Step 3: {user2['username']} accepting call...")
                        print(f"Sending: {call_accept}")
                        await ws2.send(json.dumps(call_accept))
                        
                        # Step 4: User1 should receive accept confirmation
                        print(f"\n📥 Step 4: Waiting for accept confirmation on {user1['username']}'s WebSocket...")
                        try:
                            accept_response = await asyncio.wait_for(ws1.recv(), timeout=10.0)
                            accept_data = json.loads(accept_response)
                            print(f"Received: {accept_data}")
                            
                            accept_status = accept_data.get("call_status")
                            if accept_status == "accept":
                                print("✅ Call accept confirmation received!")
                                
                                # Step 5: Test call end
                                call_end = {
                                    "type": "call",
                                    "call_status": "end",
                                    "call_id": call_request["call_id"],
                                    "receiver_id": user2["id"]
                                }
                                
                                print(f"\n📤 Step 5: {user1['username']} ending call...")
                                await ws1.send(json.dumps(call_end))
                                
                                print("✅ Complete call flow test PASSED!")
                                return True
                            else:
                                print(f"❌ Expected 'accept' status, got: {accept_status}")
                                return False
                                
                        except asyncio.TimeoutError:
                            print("❌ Timeout waiting for accept confirmation")
                            return False
                    else:
                        print(f"❌ Invalid call request - Status: {call_status}, Caller: {caller_id}")
                        return False
                else:
                    print(f"❌ Expected call message, got: {call_data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for call request")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False

async def test_call_decline():
    """Test call decline functionality"""
    
    base_url = "http://localhost:8000"
    
    print("\n🔧 Testing call decline...")
    
    # Get existing users
    try:
        response1 = requests.get(f"{base_url}/api/users/username/call_user1")
        response2 = requests.get(f"{base_url}/api/users/username/call_user2")
        
        if response1.status_code == 200 and response2.status_code == 200:
            user1 = response1.json()
            user2 = response2.json()
        else:
            print("❌ Test users not found")
            return False
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return False
    
    ws_url1 = f"ws://localhost:8000/ws/{user1['id']}"
    ws_url2 = f"ws://localhost:8000/ws/{user2['id']}"
    
    try:
        async with websockets.connect(ws_url1) as ws1, websockets.connect(ws_url2) as ws2:
            # User1 initiates call
            call_request = {
                "type": "call",
                "call_status": "request",
                "call_type": "video",
                "call_id": f"decline_test_{int(time.time())}",
                "receiver_id": user2["id"]
            }
            
            print(f"📤 {user1['username']} initiating video call...")
            await ws1.send(json.dumps(call_request))
            
            # User2 receives and declines
            response = await asyncio.wait_for(ws2.recv(), timeout=5.0)
            call_data = json.loads(response)
            
            if call_data.get("type") == "call":
                call_decline = {
                    "type": "call",
                    "call_status": "decline",
                    "call_type": "video",
                    "call_id": call_request["call_id"],
                    "receiver_id": user1["id"]
                }
                
                print(f"📤 {user2['username']} declining call...")
                await ws2.send(json.dumps(call_decline))
                
                # User1 should receive decline
                decline_response = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                decline_data = json.loads(decline_response)
                
                if decline_data.get("call_status") == "decline":
                    print("✅ Call decline test PASSED!")
                    return True
                else:
                    print(f"❌ Expected decline, got: {decline_data}")
                    return False
            else:
                print("❌ Call request not received")
                return False
                
    except Exception as e:
        print(f"❌ Call decline test failed: {e}")
        return False

async def main():
    """Run all call tests"""
    print("🧪 WebChat Call Functionality Debug")
    print("=" * 50)
    
    # Test call flow
    flow_result = await test_call_flow()
    
    # Test call decline
    decline_result = await test_call_decline()
    
    print("\n" + "=" * 50)
    print("📊 Call Test Results:")
    print(f"  Call Flow: {'✅ PASS' if flow_result else '❌ FAIL'}")
    print(f"  Call Decline: {'✅ PASS' if decline_result else '❌ FAIL'}")
    
    if flow_result and decline_result:
        print("\n🎉 All call tests PASSED!")
        print("\n💡 Ready for browser testing:")
        print("  1. Open: http://localhost:8000/?username=call_user1")
        print("  2. Open: http://localhost:8000/?username=call_user2")
        print("  3. Click audio/video call buttons")
        print("  4. Accept/decline calls in the other window")
        print("\n🔧 Debug tips:")
        print("  • Check browser console for 'callType' errors")
        print("  • Allow microphone/camera permissions")
        print("  • Look for WebRTC connection logs")
    else:
        print("\n⚠️  Some call tests failed.")
        print("Check the server logs for more details.")

if __name__ == "__main__":
    asyncio.run(main())
