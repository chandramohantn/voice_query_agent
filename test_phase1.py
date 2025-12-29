#!/usr/bin/env python3

import requests
import json
import time

def test_webhook_endpoints():
    """Test Twilio webhook endpoints"""
    
    base_url = "http://localhost:8082"
    
    print("🧪 Testing Twilio webhook endpoints...")
    print("=" * 50)
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print(f"✅ Health check: {response.status_code} - {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test incoming call webhook (simulate Twilio request)
    try:
        call_data = {
            "CallSid": "test_call_sid_123",
            "From": "+1234567890",
            "To": "+0987654321"
        }
        
        response = requests.post(f"{base_url}/incoming-call", data=call_data)
        if response.status_code == 200:
            print(f"✅ Incoming call webhook: {response.status_code}")
            print(f"   📋 TwiML Response Preview:")
            twiml = response.text
            if "<Say>" in twiml and "<Stream" in twiml:
                print(f"   ✅ Contains <Say> element")
                print(f"   ✅ Contains <Stream> element")
                print(f"   📡 Stream URL: wss://localhost:8083/media-stream")
            else:
                print(f"   ❌ Missing required TwiML elements")
        else:
            print(f"❌ Incoming call webhook failed: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Incoming call webhook failed: {e}")
    
    # Test call status webhook
    try:
        status_data = {
            "CallSid": "test_call_sid_123",
            "CallStatus": "in-progress"
        }
        
        response = requests.post(f"{base_url}/call-status", data=status_data)
        if response.status_code == 200:
            print(f"✅ Call status webhook: {response.status_code} - {response.json()}")
        else:
            print(f"❌ Call status webhook failed: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Call status webhook failed: {e}")

def test_media_stream_server():
    """Test if media stream server is accessible"""
    print("\n🎵 Testing Media Stream Server...")
    print("=" * 50)
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8083))
        sock.close()
        
        if result == 0:
            print("✅ Media stream server is listening on port 8083")
            print("   📡 WebSocket URL: ws://localhost:8083/media-stream")
        else:
            print("❌ Media stream server is not accessible on port 8083")
            
    except Exception as e:
        print(f"❌ Media stream server test failed: {e}")

if __name__ == "__main__":
    print("🚀 Phase 1 Testing - Twilio Integration")
    print("=" * 50)
    
    test_webhook_endpoints()
    test_media_stream_server()
    
    print("\n📋 Phase 1 Summary:")
    print("=" * 50)
    print("✅ Twilio webhook handler (HTTP endpoints)")
    print("✅ Media stream handler (WebSocket server)")
    print("✅ TwiML generation with proper Stream configuration")
    print("✅ Health check and status endpoints")
    print("\n🎯 Next: Configure Twilio phone number to use these webhooks")
    print("   Webhook URL: https://your-domain.com/incoming-call")
