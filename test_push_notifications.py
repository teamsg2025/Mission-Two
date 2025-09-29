#!/usr/bin/env python3
"""
Test script for push notifications
This script tests the push notification functionality by calling the server endpoints
"""

import requests
import json
import time

# Configuration
SERVER_URL = "https://mission-2-app-server.onrender.com"  # Update this to your server URL
# For local testing, use: SERVER_URL = "http://localhost:3001"

def test_server_health():
    """Test if the server is running"""
    try:
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_register_token():
    """Test token registration"""
    try:
        # Simulate a fake Expo push token
        fake_token = "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
        
        response = requests.post(
            f"{SERVER_URL}/register-token",
            json={
                "expo_push_token": fake_token,
                "user_id": "test_user_123",
                "device_name": "Test Device"
            }
        )
        
        if response.status_code == 200:
            print("✅ Token registration successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Token registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error registering token: {e}")
        return False

def test_initiate_call():
    """Test call initiation"""
    try:
        response = requests.post(
            f"{SERVER_URL}/initiate-call",
            json={
                "room_name": "test-room-123",
                "caller_name": "Test Caller",
                "target_user_id": None  # Send to all devices
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Call initiation successful")
            print(f"   Call ID: {result.get('call_id')}")
            print(f"   Room: {result.get('room_name')}")
            print(f"   Notifications sent: {result.get('notifications_sent')}")
            return True
        else:
            print(f"❌ Call initiation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        return False

def test_get_registered_tokens():
    """Test getting registered tokens"""
    try:
        response = requests.get(f"{SERVER_URL}/registered-tokens")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Retrieved registered tokens")
            print(f"   Total tokens: {result.get('total_tokens')}")
            for token_info in result.get('tokens', []):
                print(f"   - {token_info.get('token_preview')} (User: {token_info.get('user_id')})")
            return True
        else:
            print(f"❌ Failed to get registered tokens: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting registered tokens: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Push Notification System")
    print("=" * 50)
    
    # Test server health
    if not test_server_health():
        print("\n❌ Server is not running. Please start the server first.")
        return
    
    print()
    
    # Test token registration
    print("Testing token registration...")
    test_register_token()
    
    print()
    
    # Test getting registered tokens
    print("Testing get registered tokens...")
    test_get_registered_tokens()
    
    print()
    
    # Test call initiation
    print("Testing call initiation...")
    test_initiate_call()
    
    print()
    print("🎉 Test completed!")
    print("\nTo test with a real device:")
    print("1. Install the React Native app on a physical device")
    print("2. The app will automatically register its push token")
    print("3. Run this script to initiate a call")
    print("4. The device should receive a push notification")

if __name__ == "__main__":
    main()

