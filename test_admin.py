#!/usr/bin/env python3
"""
Test script for admin functionality
"""
import requests
import base64
import json

# Admin credentials
admin_username = "admin"
admin_password = "admin123"
base_url = "http://localhost:8000"

# Create basic auth header
credentials = base64.b64encode(f"{admin_username}:{admin_password}".encode()).decode()
headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

def test_admin_endpoints():
    print("Testing Admin Panel Endpoints...")
    
    # Test 1: Initialize admin data
    print("\n1. Testing admin initialization...")
    try:
        response = requests.post(f"{base_url}/api/admin/initialize", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get dashboard
    print("\n2. Testing dashboard...")
    try:
        response = requests.get(f"{base_url}/api/admin/dashboard", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total Users: {data['stats']['total_users']}")
            print(f"   Active Users: {data['stats']['active_users']}")
            print(f"   Total Messages: {data['stats']['total_messages']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get users
    print("\n3. Testing users endpoint...")
    try:
        response = requests.get(f"{base_url}/api/admin/users", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"   Found {len(users)} users")
            for user in users[:3]:  # Show first 3 users
                print(f"   - {user['username']} ({user['email'] or 'No email'}) - {user['role']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Get groups
    print("\n4. Testing groups endpoint...")
    try:
        response = requests.get(f"{base_url}/api/admin/groups", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            groups = response.json()
            print(f"   Found {len(groups)} groups")
            for group in groups[:3]:  # Show first 3 groups
                print(f"   - {group['name']} (Members: {group.get('member_count', 0)})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Get messages
    print("\n5. Testing messages endpoint...")
    try:
        response = requests.get(f"{base_url}/api/admin/messages?limit=5", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            messages = response.json()
            print(f"   Found {len(messages)} messages")
            for msg in messages[:3]:  # Show first 3 messages
                content = msg['content'][:50] + '...' if msg['content'] and len(msg['content']) > 50 else msg['content'] or '[Media]'
                print(f"   - {msg.get('sender_username', f'User {msg['sender_id']}')} -> {content}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 6: Get call logs
    print("\n6. Testing call logs endpoint...")
    try:
        response = requests.get(f"{base_url}/api/admin/call-logs?limit=5", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            calls = response.json()
            print(f"   Found {len(calls)} call logs")
            for call in calls[:3]:  # Show first 3 calls
                print(f"   - {call.get('caller_username', f'User {call['caller_id']}')} -> {call.get('receiver_username', f'User {call.get('receiver_id', 'N/A')}')} ({call['call_status']})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 7: Get settings
    print("\n7. Testing settings endpoint...")
    try:
        response = requests.get(f"{base_url}/api/admin/settings", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            settings = response.json()
            print(f"   Found {len(settings)} settings")
            for key, value in list(settings.items())[:5]:  # Show first 5 settings
                print(f"   - {key}: {value}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\nAdmin panel testing completed!")

if __name__ == "__main__":
    test_admin_endpoints()
