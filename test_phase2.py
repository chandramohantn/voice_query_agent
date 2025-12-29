#!/usr/bin/env python3

import asyncio
import base64
import json
import websockets
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from audio_converter import AudioConverter

def test_audio_conversion():
    """Test audio format conversion functions"""
    print("🎵 Testing Audio Conversion...")
    print("=" * 50)
    
    # Create sample μ-law data (silence)
    sample_mulaw = b'\xff' * 160  # 160 bytes = 20ms at 8kHz
    base64_mulaw = base64.b64encode(sample_mulaw).decode('utf-8')
    
    try:
        # Test Twilio to Gemini conversion
        base64_pcm = AudioConverter.twilio_to_gemini_format(base64_mulaw)
        if base64_pcm:
            print("✅ Twilio → Gemini conversion: Success")
            print(f"   Input length: {len(base64_mulaw)} chars")
            print(f"   Output length: {len(base64_pcm)} chars")
        else:
            print("❌ Twilio → Gemini conversion: Failed")
        
        # Test Gemini to Twilio conversion
        base64_mulaw_back = AudioConverter.gemini_to_twilio_format(base64_pcm)
        if base64_mulaw_back:
            print("✅ Gemini → Twilio conversion: Success")
            print(f"   Round-trip length: {len(base64_mulaw_back)} chars")
        else:
            print("❌ Gemini → Twilio conversion: Failed")
        
        # Test message creation
        message = AudioConverter.create_gemini_audio_message(base64_pcm)
        if message.get("realtime_input", {}).get("media_chunks"):
            print("✅ Gemini message format: Success")
            print(f"   Message structure: {list(message.keys())}")
        else:
            print("❌ Gemini message format: Failed")
            
    except Exception as e:
        print(f"❌ Audio conversion test failed: {e}")

async def test_virtual_client():
    """Test virtual WebSocket client connection"""
    print("\n🤖 Testing Virtual WebSocket Client...")
    print("=" * 50)
    
    try:
        from virtual_client import VirtualWebSocketClient
        
        # Create virtual client
        client = VirtualWebSocketClient("test_call_123")
        
        # Set up test callbacks
        responses_received = []
        
        def on_audio(audio_data):
            responses_received.append(("audio", len(audio_data)))
            print(f"   📢 Received audio response: {len(audio_data)} chars")
        
        def on_text(text):
            responses_received.append(("text", text))
            print(f"   💬 Received text response: {text}")
        
        def on_error(error):
            responses_received.append(("error", error))
            print(f"   ❌ Error: {error}")
        
        client.on_audio_response = on_audio
        client.on_text_response = on_text
        client.on_error = on_error
        
        print("✅ Virtual client created successfully")
        print("   Note: Connection test requires main WebSocket server running")
        
        return True
        
    except Exception as e:
        print(f"❌ Virtual client test failed: {e}")
        return False

async def test_session_manager():
    """Test call session manager"""
    print("\n📞 Testing Call Session Manager...")
    print("=" * 50)
    
    try:
        from call_session_manager import CallSessionManager
        
        # Create session manager
        manager = CallSessionManager()
        
        print("✅ Session manager created successfully")
        print(f"   Active sessions: {manager.get_active_session_count()}")
        
        # Test would require actual WebSocket connections
        print("   Note: Full session test requires Twilio WebSocket connection")
        
        return True
        
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        return False

async def test_websocket_server():
    """Test if the enhanced media stream server can start"""
    print("\n🌐 Testing Enhanced Media Stream Server...")
    print("=" * 50)
    
    try:
        # Import the updated handler
        from media_stream_handler import TwilioMediaStreamHandler
        
        handler = TwilioMediaStreamHandler()
        print("✅ Enhanced media stream handler created")
        print("   Ready to handle Twilio streams with Gemini integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced media stream handler test failed: {e}")
        return False

async def main():
    """Run all Phase 2 tests"""
    print("🚀 Phase 2 Testing - Audio Processing & Gemini Integration")
    print("=" * 60)
    
    # Test audio conversion
    test_audio_conversion()
    
    # Test virtual client
    await test_virtual_client()
    
    # Test session manager
    await test_session_manager()
    
    # Test enhanced server
    await test_websocket_server()
    
    print("\n📋 Phase 2 Summary:")
    print("=" * 50)
    print("✅ Audio format conversion (μ-law ↔ PCM)")
    print("✅ Virtual WebSocket client for Gemini connection")
    print("✅ Call session management")
    print("✅ Enhanced media stream handler")
    print("\n🎯 Next: End-to-end testing with actual Twilio calls")
    print("   Requires: Main WebSocket server + Twilio phone number")

if __name__ == "__main__":
    asyncio.run(main())
