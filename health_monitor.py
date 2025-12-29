#!/usr/bin/env python3

import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime
import sys

class HealthMonitor:
    """Monitors health of all Voice Query Agent services"""
    
    def __init__(self):
        self.services = {
            "gemini_proxy": {"type": "websocket", "url": "ws://localhost:8080", "status": "unknown"},
            "twilio_webhooks": {"type": "http", "url": "http://localhost:8082/health", "status": "unknown"},
            "media_streams": {"type": "websocket", "url": "ws://localhost:8083", "status": "unknown"}
        }
        self.session = None
    
    async def check_http_service(self, name, url):
        """Check HTTP service health"""
        try:
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    self.services[name]["status"] = "healthy"
                    self.services[name]["response"] = data
                    return True
                else:
                    self.services[name]["status"] = f"error_{response.status}"
                    return False
        except Exception as e:
            self.services[name]["status"] = f"error: {str(e)[:50]}"
            return False
    
    async def check_websocket_service(self, name, url):
        """Check WebSocket service health"""
        try:
            async with websockets.connect(url, timeout=5) as websocket:
                # For Gemini proxy, send a test message
                if name == "gemini_proxy":
                    test_message = {"test": "health_check"}
                    await websocket.send(json.dumps(test_message))
                
                self.services[name]["status"] = "healthy"
                return True
        except Exception as e:
            self.services[name]["status"] = f"error: {str(e)[:50]}"
            return False
    
    async def check_all_services(self):
        """Check health of all services"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        tasks = []
        for name, config in self.services.items():
            if config["type"] == "http":
                task = self.check_http_service(name, config["url"])
            else:
                task = self.check_websocket_service(name, config["url"])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    def print_status(self):
        """Print current status of all services"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🔍 Health Check - {timestamp}")
        print("=" * 50)
        
        all_healthy = True
        for name, config in self.services.items():
            status = config["status"]
            if status == "healthy":
                print(f"✅ {name.replace('_', ' ').title()}: {status}")
            else:
                print(f"❌ {name.replace('_', ' ').title()}: {status}")
                all_healthy = False
        
        if all_healthy:
            print("\n🎯 All services healthy!")
        else:
            print("\n⚠️  Some services need attention")
        
        return all_healthy
    
    async def continuous_monitoring(self, interval=30):
        """Continuously monitor services"""
        print("🔄 Starting continuous health monitoring...")
        print(f"   Checking every {interval} seconds")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                await self.check_all_services()
                healthy = self.print_status()
                
                if not healthy:
                    print("\n🚨 ALERT: Service degradation detected!")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
        finally:
            if self.session:
                await self.session.close()

async def run_health_check():
    """Run a single health check"""
    monitor = HealthMonitor()
    await monitor.check_all_services()
    healthy = monitor.print_status()
    
    if monitor.session:
        await monitor.session.close()
    
    return healthy

async def run_continuous_monitoring():
    """Run continuous monitoring"""
    monitor = HealthMonitor()
    await monitor.continuous_monitoring()

async def test_call_flow():
    """Test the complete call flow simulation"""
    print("\n🧪 Testing Complete Call Flow")
    print("=" * 50)
    
    monitor = HealthMonitor()
    
    # Check if services are running
    await monitor.check_all_services()
    if not monitor.print_status():
        print("❌ Cannot test call flow - services not healthy")
        return False
    
    print("\n📞 Simulating incoming call...")
    
    try:
        # Test webhook endpoint
        async with aiohttp.ClientSession() as session:
            call_data = {
                "CallSid": "test_flow_call_123",
                "From": "+1234567890",
                "To": "+0987654321"
            }
            
            async with session.post(
                "http://localhost:8082/incoming-call",
                data=call_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    twiml = await response.text()
                    if "<Stream" in twiml:
                        print("✅ Webhook responds with proper TwiML")
                    else:
                        print("❌ Webhook TwiML missing Stream element")
                        return False
                else:
                    print(f"❌ Webhook returned status {response.status}")
                    return False
        
        # Test media stream connection
        print("🎵 Testing media stream connection...")
        
        async with websockets.connect("ws://localhost:8083/media-stream") as websocket:
            # Send connected event
            await websocket.send(json.dumps({"event": "connected"}))
            
            # Send start event
            start_msg = {
                "event": "start",
                "streamSid": "test_flow_stream",
                "start": {"callSid": "test_flow_call_123"}
            }
            await websocket.send(json.dumps(start_msg))
            
            # Send sample audio
            import base64
            sample_audio = base64.b64encode(b'\x55' * 160).decode('utf-8')
            media_msg = {
                "event": "media",
                "streamSid": "test_flow_stream",
                "media": {"payload": sample_audio}
            }
            await websocket.send(json.dumps(media_msg))
            
            # Send stop event
            stop_msg = {"event": "stop", "streamSid": "test_flow_stream"}
            await websocket.send(json.dumps(stop_msg))
            
            print("✅ Media stream flow completed successfully")
        
        print("\n🎯 Call flow test: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Call flow test failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            asyncio.run(run_continuous_monitoring())
        elif sys.argv[1] == "test":
            asyncio.run(test_call_flow())
        else:
            print("Usage: python health_monitor.py [monitor|test]")
    else:
        # Single health check
        asyncio.run(run_health_check())
