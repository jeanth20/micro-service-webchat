#!/usr/bin/env python3
"""
Create test users for WebChat testing
"""

import requests
import sys
import json

def create_test_users():
    """Create multiple test users for testing"""
    base_url = "http://localhost:8000"
    
    test_users = [
        {"username": "alice", "email": "alice@example.com"},
        {"username": "bob", "email": "bob@example.com"},
        {"username": "charlie", "email": "charlie@example.com"},
        {"username": "diana", "email": "diana@example.com"},
        {"username": "eve", "email": "eve@example.com"}
    ]
    
    created_users = []
    
    print("🔧 Creating test users...")
    
    for user_data in test_users:
        try:
            response = requests.post(f"{base_url}/api/users/", json=user_data)
            
            if response.status_code == 200:
                user = response.json()
                created_users.append(user)
                print(f"✓ Created user: {user['username']} (ID: {user['id']})")
            elif response.status_code == 400:
                # User might already exist, try to get it
                try:
                    get_response = requests.get(f"{base_url}/api/users/username/{user_data['username']}")
                    if get_response.status_code == 200:
                        user = get_response.json()
                        created_users.append(user)
                        print(f"✓ User already exists: {user['username']} (ID: {user['id']})")
                    else:
                        print(f"✗ Failed to create/get user: {user_data['username']}")
                except:
                    print(f"✗ Failed to create user: {user_data['username']}")
            else:
                print(f"✗ Failed to create user: {user_data['username']} - Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to WebChat server. Make sure it's running on http://localhost:8000")
            return []
        except Exception as e:
            print(f"✗ Error creating user {user_data['username']}: {e}")
    
    return created_users

def create_test_group(users):
    """Create a test group with some users"""
    if len(users) < 3:
        print("Need at least 3 users to create a test group")
        return None
    
    base_url = "http://localhost:8000"
    
    try:
        # Create group
        group_data = {
            "name": "Test Group Chat",
            "description": "A group for testing WebChat functionality"
        }
        
        response = requests.post(
            f"{base_url}/api/groups/",
            json=group_data,
            params={"created_by": users[0]["id"]}
        )
        
        if response.status_code == 200:
            group = response.json()
            print(f"✓ Created group: {group['name']} (ID: {group['id']})")
            
            # Add members to group
            for user in users[1:4]:  # Add 3 more users
                member_response = requests.post(
                    f"{base_url}/api/groups/{group['id']}/members",
                    params={"user_id": user["id"]}
                )
                
                if member_response.status_code == 200:
                    print(f"✓ Added {user['username']} to group")
                else:
                    print(f"✗ Failed to add {user['username']} to group")
            
            return group
        else:
            print(f"✗ Failed to create group - Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Error creating group: {e}")
        return None

def print_testing_instructions(users):
    """Print instructions for testing"""
    print("\n" + "="*60)
    print("🎉 Test Users Created Successfully!")
    print("="*60)
    
    print("\n📱 Testing Instructions:")
    print("\n1. **URL Parameter Method:**")
    for user in users[:3]:
        print(f"   http://localhost:8000/?user_id={user['id']}  # {user['username']}")
    
    print("\n2. **Username Parameter Method:**")
    for user in users[:3]:
        print(f"   http://localhost:8000/?username={user['username']}")
    
    print("\n3. **User Switcher Method:**")
    print("   - Open http://localhost:8000")
    print("   - Use the dropdown in the top-right to switch users")
    
    print("\n🧪 **Multi-User Testing:**")
    print("   1. Open multiple browser windows/tabs")
    print("   2. Use different URLs for different users:")
    print(f"      Tab 1: http://localhost:8000/?user_id={users[0]['id']} ({users[0]['username']})")
    if len(users) > 1:
        print(f"      Tab 2: http://localhost:8000/?user_id={users[1]['id']} ({users[1]['username']})")
    if len(users) > 2:
        print(f"      Tab 3: http://localhost:8000/?user_id={users[2]['id']} ({users[2]['username']})")
    print("   3. Start chatting between the users!")
    
    print("\n💬 **Testing Features:**")
    print("   ✓ Send messages between users")
    print("   ✓ Upload files and images")
    print("   ✓ Create group chats")
    print("   ✓ Test typing indicators")
    print("   ✓ Try call functionality")
    
    print("\n🔧 **Pro Tips:**")
    print("   • Use incognito/private windows for true multi-user testing")
    print("   • Check browser console for any errors")
    print("   • Test real-time features by typing in one window and watching another")

def main():
    print("🚀 WebChat Test User Setup")
    print("="*40)
    
    # Create test users
    users = create_test_users()
    
    if not users:
        print("\n❌ Failed to create test users. Make sure WebChat is running!")
        sys.exit(1)
    
    # Create test group
    if len(users) >= 3:
        create_test_group(users)
    
    # Print testing instructions
    print_testing_instructions(users)
    
    print(f"\n✅ Setup complete! Created {len(users)} test users.")
    print("Start testing with multiple browser windows! 🎉")

if __name__ == "__main__":
    main()
