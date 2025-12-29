#!/usr/bin/env python3

import asyncio
import json
import websockets
import sys
import os
import time

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_services_individually():
    """Test each service individually without dependencies"""
    
    print("🧪 Individual Service Testing")
    print("=" * 60)
    
    # Test 1: Audio Conversion
    print("1️⃣ Testing Audio Conversion...")
    await test_audio_conversion()
    
    # Test 2: Virtual Client (without connection)
    print("\n2️⃣ Testing Virtual Client Creation...")
    test_virtual_client_creation()
    
    # Test 3: Session Manager
    print("\n3️⃣ Testing Session Manager...")
    test_session_manager_creation()
    
    # Test 4: Webhook Handler
    print("\n4️⃣ Testing Webhook Handler...")
    await test_webhook_handler()
    
    # Test 5: Media Stream Handler (basic)
    print("\n5️⃣ Testing Media Stream Handler...")
    test_media_handler_creation()

async def test_audio_conversion():
    """Test audio conversion thoroughly"""
    from audio_converter import AudioConverter
    import base64
    
    # Test different audio patterns
    test_patterns = [
        ("Silence", b'\x55' * 160),
        ("Pattern 1", b'\x50\x60\x55\x65' * 40),
        ("Pattern 2", bytes(range(160))),
    ]
    
    all_passed = True
    
    for name, mulaw_data in test_patterns:
        base64_mulaw = base64.b64encode(mulaw_data).decode('utf-8')
        
        # Test conversion chain
        base64_pcm = AudioConverter.twilio_to_gemini_format(base64_mulaw)
        base64_mulaw_back = AudioConverter.gemini_to_twilio_format(base64_pcm)
        message = AudioConverter.create_gemini_audio_message(base64_pcm)
        
        if base64_pcm and base64_mulaw_back and message.get("realtime_input"):
            print(f"   ✅ {name}: Conversion chain successful")
        else:
            print(f"   ❌ {name}: Conversion chain failed")
            all_passed = False
    
    if all_passed:
        print("   🎯 All audio conversion tests passed!")
    else:
        print("   ⚠️  Some audio conversion tests failed")

def test_virtual_client_creation():
    """Test virtual client creation without connection"""
    try:
        from virtual_client import VirtualWebSocketClient
        
        client = VirtualWebSocketClient("test_call_123")
        
        # Test callback setup
        responses = []
        client.on_audio_response = lambda x: responses.append(("audio", len(x)))
        client.on_text_response = lambda x: responses.append(("text", x))
        client.on_error = lambda x: responses.append(("error", x))
        
        print("   ✅ Virtual client created successfully")
        print("   ✅ Callbacks configured")
        
    except Exception as e:
        print(f"   ❌ Virtual client creation failed: {e}")

def test_session_manager_creation():
    """Test session manager creation"""
    try:
        from call_session_manager import CallSessionManager
        
        manager = CallSessionManager()
        count = manager.get_active_session_count()
        
        print(f"   ✅ Session manager created (active sessions: {count})")
        
    except Exception as e:
        print(f"   ❌ Session manager creation failed: {e}")

async def test_webhook_handler():
    """Test webhook handler by starting it briefly"""
    try:
        # Start webhook handler
        process = await asyncio.create_subprocess_exec(
            sys.executable, "backend/twilio_handler.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for startup
        await asyncio.sleep(2)
        
        # Test endpoints
        import requests
        
        try:
            # Health check
            response = requests.get("http://localhost:8082/health", timeout=3)
            if response.status_code == 200:
                print("   ✅ Webhook handler responding")
            else:
                print("   ❌ Webhook handler not responding properly")
                
        except requests.exceptions.RequestException:
            print("   ❌ Could not connect to webhook handler")
        
        # Cleanup
        process.terminate()
        await process.wait()
        
    except Exception as e:
        print(f"   ❌ Webhook handler test failed: {e}")

def test_media_handler_creation():
    """Test media handler creation without starting server"""
    try:
        from media_stream_handler import TwilioMediaStreamHandler
        
        handler = TwilioMediaStreamHandler()
        print("   ✅ Media stream handler created successfully")
        
    except Exception as e:
        print(f"   ❌ Media stream handler creation failed: {e}")

async def test_mock_integration():
    """Test integration with mock Gemini server"""
    
    print("\n🔗 Mock Integration Test")
    print("=" * 50)
    
    # Create a simple mock Gemini server
    async def mock_gemini_server(websocket, path):
        """Mock Gemini server that responds to setup and audio"""
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if "setup" in data:
                    # Respond with setup complete
                    setup_response = {"setupComplete": True}
                    await websocket.send(json.dumps(setup_response))
                    print("   📡 Mock Gemini: Setup complete sent")
                
                elif "realtime_input" in data:
                    # Respond with mock audio
                    audio_response = {
                        "serverContent": {
                            "modelTurn": {
                                "parts": [{
                                    "inlineData": {
                                        "mimeType": "audio/pcm",
                                        "data": "dGVzdCBhdWRpbyByZXNwb25zZQ=="  # "test audio response" in base64
                                    }
                                }]
                            }
                        }
                    }
                    await websocket.send(json.dumps(audio_response))
                    print("   📡 Mock Gemini: Audio response sent")
                    
        except websockets.exceptions.ConnectionClosed:
            print("   📡 Mock Gemini: Connection closed")
    
    # Start mock server
    mock_server = await websockets.serve(mock_gemini_server, "localhost", 8084)
    print("   🎭 Mock Gemini server started on port 8084")
    
    try:
        # Test virtual client with mock server
        from virtual_client import VirtualWebSocketClient
        
        client = VirtualWebSocketClient("test_call", "ws://localhost:8084")
        
        responses = []
        client.on_audio_response = lambda x: responses.append(("audio", len(x)))
        client.on_text_response = lambda x: responses.append(("text", x))
        
        # Connect and test
        await client.connect()
        await asyncio.sleep(1)
        
        # Send test audio
        await client.send_audio_from_twilio("dGVzdCBhdWRpbw==")  # "test audio" in base64
        await asyncio.sleep(1)
        
        await client.disconnect()
        
        if responses:
            print(f"   ✅ Mock integration successful: {len(responses)} responses received")
        else:
            print("   ⚠️  Mock integration: No responses received")
            
    except Exception as e:
        print(f"   ❌ Mock integration failed: {e}")
    
    finally:
        mock_server.close()
        await mock_server.wait_closed()
        print("   🎭 Mock server stopped")

if __name__ == "__main__":
    asyncio.run(test_services_individually())
    asyncio.run(test_mock_integration())
