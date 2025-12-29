#!/usr/bin/env python3

import asyncio
import aiohttp
import websockets
import json
import time
import statistics
from datetime import datetime
import concurrent.futures
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

class PerformanceTester:
    """Performance testing suite for Voice Query Agent"""
    
    def __init__(self):
        self.results = {
            "webhook_latency": [],
            "audio_conversion_time": [],
            "websocket_connection_time": [],
            "end_to_end_latency": []
        }
    
    async def test_webhook_performance(self, num_requests=100):
        """Test webhook response performance"""
        print(f"🚀 Testing webhook performance ({num_requests} requests)...")
        
        async def single_webhook_test():
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                call_data = {
                    "CallSid": f"perf_test_{int(time.time() * 1000)}",
                    "From": "+1234567890",
                    "To": "+0987654321"
                }
                
                async with session.post(
                    "http://localhost:8082/incoming-call",
                    data=call_data,
                    timeout=5
                ) as response:
                    await response.text()
                    latency = (time.time() - start_time) * 1000  # ms
                    return latency, response.status == 200
        
        # Run concurrent requests
        tasks = [single_webhook_test() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        latencies = []
        
        for result in results:
            if isinstance(result, tuple):
                latency, success = result
                if success:
                    successful += 1
                    latencies.append(latency)
        
        self.results["webhook_latency"] = latencies
        
        print(f"   ✅ Webhook Performance:")
        print(f"      Success Rate: {successful}/{num_requests} ({successful/num_requests*100:.1f}%)")
        if latencies:
            print(f"      Avg Latency: {statistics.mean(latencies):.1f}ms")
            print(f"      Min Latency: {min(latencies):.1f}ms")
            print(f"      Max Latency: {max(latencies):.1f}ms")
            print(f"      95th Percentile: {statistics.quantiles(latencies, n=20)[18]:.1f}ms")
    
    def test_audio_conversion_performance(self, num_conversions=1000):
        """Test audio conversion performance"""
        print(f"🎵 Testing audio conversion performance ({num_conversions} conversions)...")
        
        from audio_converter import AudioConverter
        import base64
        
        # Test data
        test_audio = base64.b64encode(b'\x55' * 160).decode('utf-8')
        conversion_times = []
        
        for _ in range(num_conversions):
            start_time = time.time()
            
            # Twilio to Gemini conversion
            gemini_audio = AudioConverter.twilio_to_gemini_format(test_audio)
            
            # Gemini to Twilio conversion
            twilio_audio = AudioConverter.gemini_to_twilio_format(gemini_audio)
            
            conversion_time = (time.time() - start_time) * 1000  # ms
            conversion_times.append(conversion_time)
        
        self.results["audio_conversion_time"] = conversion_times
        
        print(f"   ✅ Audio Conversion Performance:")
        print(f"      Avg Time: {statistics.mean(conversion_times):.2f}ms")
        print(f"      Min Time: {min(conversion_times):.2f}ms")
        print(f"      Max Time: {max(conversion_times):.2f}ms")
        print(f"      Throughput: {1000/statistics.mean(conversion_times):.0f} conversions/sec")
    
    async def test_websocket_performance(self, num_connections=50):
        """Test WebSocket connection performance"""
        print(f"🔌 Testing WebSocket performance ({num_connections} connections)...")
        
        async def single_websocket_test():
            start_time = time.time()
            
            try:
                async with websockets.connect("ws://localhost:8083/media-stream", timeout=5) as websocket:
                    connection_time = (time.time() - start_time) * 1000  # ms
                    
                    # Send a test message
                    test_msg = {"event": "connected"}
                    await websocket.send(json.dumps(test_msg))
                    
                    return connection_time, True
            except Exception:
                return 0, False
        
        # Run concurrent connections
        tasks = [single_websocket_test() for _ in range(num_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        connection_times = []
        
        for result in results:
            if isinstance(result, tuple):
                conn_time, success = result
                if success:
                    successful += 1
                    connection_times.append(conn_time)
        
        self.results["websocket_connection_time"] = connection_times
        
        print(f"   ✅ WebSocket Performance:")
        print(f"      Success Rate: {successful}/{num_connections} ({successful/num_connections*100:.1f}%)")
        if connection_times:
            print(f"      Avg Connection Time: {statistics.mean(connection_times):.1f}ms")
            print(f"      Min Connection Time: {min(connection_times):.1f}ms")
            print(f"      Max Connection Time: {max(connection_times):.1f}ms")
    
    async def test_end_to_end_latency(self, num_tests=20):
        """Test end-to-end call latency"""
        print(f"⏱️  Testing end-to-end latency ({num_tests} calls)...")
        
        async def single_e2e_test():
            start_time = time.time()
            
            try:
                # Step 1: Webhook call
                async with aiohttp.ClientSession() as session:
                    call_data = {
                        "CallSid": f"e2e_test_{int(time.time() * 1000)}",
                        "From": "+1234567890",
                        "To": "+0987654321"
                    }
                    
                    async with session.post(
                        "http://localhost:8082/incoming-call",
                        data=call_data,
                        timeout=5
                    ) as response:
                        await response.text()
                
                # Step 2: Media stream connection and audio processing
                async with websockets.connect("ws://localhost:8083/media-stream") as websocket:
                    # Connected
                    await websocket.send(json.dumps({"event": "connected"}))
                    
                    # Start stream
                    start_msg = {
                        "event": "start",
                        "streamSid": f"e2e_stream_{int(time.time() * 1000)}",
                        "start": {"callSid": call_data["CallSid"]}
                    }
                    await websocket.send(json.dumps(start_msg))
                    
                    # Send audio
                    import base64
                    sample_audio = base64.b64encode(b'\x55' * 160).decode('utf-8')
                    media_msg = {
                        "event": "media",
                        "streamSid": start_msg["streamSid"],
                        "media": {"payload": sample_audio}
                    }
                    await websocket.send(json.dumps(media_msg))
                    
                    # Stop
                    stop_msg = {"event": "stop", "streamSid": start_msg["streamSid"]}
                    await websocket.send(json.dumps(stop_msg))
                
                total_time = (time.time() - start_time) * 1000  # ms
                return total_time, True
                
            except Exception as e:
                return 0, False
        
        # Run tests
        tasks = [single_e2e_test() for _ in range(num_tests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        latencies = []
        
        for result in results:
            if isinstance(result, tuple):
                latency, success = result
                if success:
                    successful += 1
                    latencies.append(latency)
        
        self.results["end_to_end_latency"] = latencies
        
        print(f"   ✅ End-to-End Performance:")
        print(f"      Success Rate: {successful}/{num_tests} ({successful/num_tests*100:.1f}%)")
        if latencies:
            print(f"      Avg Latency: {statistics.mean(latencies):.1f}ms")
            print(f"      Min Latency: {min(latencies):.1f}ms")
            print(f"      Max Latency: {max(latencies):.1f}ms")
    
    def generate_report(self):
        """Generate performance report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n📊 Performance Report - {timestamp}")
        print("=" * 60)
        
        # Webhook Performance
        if self.results["webhook_latency"]:
            latencies = self.results["webhook_latency"]
            print(f"📞 Webhook Performance:")
            print(f"   Average: {statistics.mean(latencies):.1f}ms")
            print(f"   95th Percentile: {statistics.quantiles(latencies, n=20)[18]:.1f}ms")
            print(f"   Requests/sec: {1000/statistics.mean(latencies):.0f}")
        
        # Audio Conversion Performance
        if self.results["audio_conversion_time"]:
            times = self.results["audio_conversion_time"]
            print(f"\n🎵 Audio Conversion Performance:")
            print(f"   Average: {statistics.mean(times):.2f}ms")
            print(f"   Throughput: {1000/statistics.mean(times):.0f} conversions/sec")
        
        # WebSocket Performance
        if self.results["websocket_connection_time"]:
            times = self.results["websocket_connection_time"]
            print(f"\n🔌 WebSocket Performance:")
            print(f"   Average Connection: {statistics.mean(times):.1f}ms")
        
        # End-to-End Performance
        if self.results["end_to_end_latency"]:
            latencies = self.results["end_to_end_latency"]
            print(f"\n⏱️  End-to-End Performance:")
            print(f"   Average: {statistics.mean(latencies):.1f}ms")
            print(f"   95th Percentile: {statistics.quantiles(latencies, n=20)[18]:.1f}ms")
        
        # Performance Assessment
        print(f"\n🎯 Performance Assessment:")
        
        webhook_avg = statistics.mean(self.results["webhook_latency"]) if self.results["webhook_latency"] else 0
        e2e_avg = statistics.mean(self.results["end_to_end_latency"]) if self.results["end_to_end_latency"] else 0
        
        if webhook_avg < 100:
            print("   ✅ Webhook latency: Excellent (<100ms)")
        elif webhook_avg < 200:
            print("   ⚠️  Webhook latency: Good (<200ms)")
        else:
            print("   ❌ Webhook latency: Needs optimization (>200ms)")
        
        if e2e_avg < 500:
            print("   ✅ End-to-end latency: Excellent (<500ms)")
        elif e2e_avg < 1000:
            print("   ⚠️  End-to-end latency: Acceptable (<1s)")
        else:
            print("   ❌ End-to-end latency: Needs optimization (>1s)")

async def run_performance_tests():
    """Run all performance tests"""
    print("🧪 Voice Query Agent - Performance Testing Suite")
    print("=" * 60)
    
    tester = PerformanceTester()
    
    # Run all tests
    await tester.test_webhook_performance(50)
    print()
    
    tester.test_audio_conversion_performance(500)
    print()
    
    await tester.test_websocket_performance(25)
    print()
    
    await tester.test_end_to_end_latency(10)
    
    # Generate report
    tester.generate_report()

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
