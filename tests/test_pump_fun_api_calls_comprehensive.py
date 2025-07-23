#!/usr/bin/env python3
"""
🔬 COMPREHENSIVE PUMP.FUN API CALLS TEST
Deep dive into actual API calls and logs to verify integration is working
"""

import sys
import os
import asyncio
import time
import json
import logging
from datetime import datetime

sys.path.append(os.getcwd())

# Setup detailed logging to capture all API calls
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pump_fun_api_test.log'),
        logging.StreamHandler()
    ]
)

async def comprehensive_api_test():
    print("=" * 100)
    print("🔬 COMPREHENSIVE PUMP.FUN API CALLS TEST")
    print("=" * 100)
    print("This test will show ACTUAL API calls and logs to prove integration status")
    print()
    
    # Test 1: Direct Pump.fun Integration Test
    print("📋 TEST 1: DIRECT PUMP.FUN INTEGRATION API CALLS")
    print("-" * 60)
    
    try:
        from services.pump_fun_integration import PumpFunStage0Integration
        
        print("✅ PumpFunStage0Integration imported successfully")
        
        # Initialize integration
        integration = PumpFunStage0Integration()
        print(f"✅ Integration initialized: {type(integration).__name__}")
        
        # Check for actual API methods
        print("\n🔍 Checking available API methods:")
        methods = [method for method in dir(integration) if not method.startswith('_')]
        for method in methods:
            print(f"   • {method}")
            
        # Test integration stats
        if hasattr(integration, 'get_integration_stats'):
            stats = integration.get_integration_stats()
            print(f"\n📊 Current Integration Stats: {stats}")
        else:
            print("\n⚠️ get_integration_stats method not found")
            
        # Test if integration has monitoring capabilities
        if hasattr(integration, 'start_monitoring'):
            print("\n🚀 Starting pump.fun monitoring...")
            try:
                # This should show actual API calls if working
                await integration.start_monitoring()
                print("✅ Monitoring started successfully")
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
        else:
            print("\n⚠️ start_monitoring method not found")
            
    except ImportError as e:
        print(f"❌ Cannot import PumpFunStage0Integration: {e}")
        print("This means pump.fun integration is NOT properly implemented")
        
    except Exception as e:
        print(f"❌ Pump.fun integration test failed: {e}")
    
    # Test 2: Check Actual Pump.fun API Endpoints
    print("\n\n📋 TEST 2: DIRECT PUMP.FUN API ENDPOINT TESTING")
    print("-" * 60)
    
    try:
        import aiohttp
        
        # Test actual pump.fun API endpoints
        pump_fun_endpoints = [
            "https://pumpportal.fun/api/trades-by-token/",
            "https://client-api-v2.pump.fun/coins/by-market-cap/",
            "https://api.pump.fun/coins/",
            "https://client-api.pump.fun/tokens/"
        ]
        
        print("🌐 Testing actual pump.fun API endpoints...")
        
        async with aiohttp.ClientSession() as session:
            for endpoint in pump_fun_endpoints:
                try:
                    print(f"\n📡 Testing: {endpoint}")
                    async with session.get(endpoint, timeout=10) as response:
                        print(f"   Status: {response.status}")
                        print(f"   Headers: {dict(response.headers)}")
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                print(f"   ✅ SUCCESS - Data type: {type(data)}")
                                if isinstance(data, list):
                                    print(f"   �� Array length: {len(data)}")
                                elif isinstance(data, dict):
                                    print(f"   📊 Keys: {list(data.keys())[:5]}")
                            except:
                                text = await response.text()
                                print(f"   📄 Response length: {len(text)} chars")
                        else:
                            print(f"   ❌ Failed with status {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Connection error: {e}")
                    
    except ImportError:
        print("❌ aiohttp not available for direct API testing")
    
    # Test 3: Check High Conviction Detector Integration Logs
    print("\n\n📋 TEST 3: HIGH CONVICTION DETECTOR INTEGRATION ANALYSIS")
    print("-" * 60)
    
    try:
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        # Initialize with debug mode to see all logs
        print("🚀 Initializing High Conviction Detector in DEBUG mode...")
        detector = HighConvictionTokenDetector(debug_mode=True)
        
        # Check pump.fun integration status
        has_pump_fun = hasattr(detector, 'pump_fun_integration')
        print(f"✅ Has pump.fun integration: {has_pump_fun}")
        
        if has_pump_fun and detector.pump_fun_integration:
            integration = detector.pump_fun_integration
            print(f"✅ Integration object: {type(integration).__name__}")
            
            # Check if integration has WebSocket or monitoring
            ws_methods = [attr for attr in dir(integration) if 'websocket' in attr.lower() or 'monitor' in attr.lower()]
            if ws_methods:
                print(f"🔌 WebSocket/Monitor methods found: {ws_methods}")
            else:
                print("⚠️ No WebSocket/Monitor methods found")
                
            # Check for API call methods
            api_methods = [attr for attr in dir(integration) if 'api' in attr.lower() or 'call' in attr.lower()]
            if api_methods:
                print(f"📡 API methods found: {api_methods}")
            else:
                print("⚠️ No API methods found")
        else:
            print("❌ Pump.fun integration object is None or missing")
            
        # Test the API capture method
        print("\n🔍 Testing API stats capture...")
        try:
            detector._capture_api_usage_stats()
            
            # Check if pump.fun stats were captured
            api_stats = detector.session_stats.get('api_usage_by_service', {})
            pump_fun_stats = api_stats.get('pump_fun', {})
            
            print(f"📊 Pump.fun stats in session: {pump_fun_stats}")
            
            if pump_fun_stats:
                print("✅ Pump.fun stats structure exists")
                for key, value in pump_fun_stats.items():
                    print(f"   • {key}: {value}")
            else:
                print("⚠️ No pump.fun stats found in session")
                
        except Exception as e:
            print(f"❌ API stats capture failed: {e}")
            
    except Exception as e:
        print(f"❌ High Conviction Detector test failed: {e}")
    
    # Test 4: Real-time Log Monitoring
    print("\n\n📋 TEST 4: REAL-TIME LOG MONITORING")
    print("-" * 60)
    
    try:
        print("📋 Checking recent logs for pump.fun activity...")
        
        # Check debug log
        if os.path.exists('debug_session.log'):
            print("\n🐛 DEBUG LOG (last 20 lines):")
            with open('debug_session.log', 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    if 'pump' in line.lower():
                        print(f"   🔍 {line.strip()}")
        
        # Check main log
        if os.path.exists('logs/virtuoso_gem_hunter.log'):
            print("\n📊 MAIN LOG - Pump.fun mentions:")
            with open('logs/virtuoso_gem_hunter.log', 'r') as f:
                lines = f.readlines()
                pump_fun_lines = [line for line in lines[-100:] if 'pump' in line.lower()]
                
                if pump_fun_lines:
                    print(f"   Found {len(pump_fun_lines)} pump.fun mentions:")
                    for line in pump_fun_lines[-10:]:
                        print(f"   🔍 {line.strip()}")
                else:
                    print("   ⚠️ No pump.fun mentions found in recent logs")
        
        # Check for pump.fun specific logs
        pump_fun_log_files = [
            'pump_fun_monitor.log',
            'pump_fun_integration.log',
            'pump_fun_api.log'
        ]
        
        for log_file in pump_fun_log_files:
            if os.path.exists(log_file):
                print(f"\n📋 Found pump.fun log: {log_file}")
                with open(log_file, 'r') as f:
                    content = f.read()
                    print(f"   Size: {len(content)} chars")
                    if content:
                        print("   Last 5 lines:")
                        for line in content.split('\n')[-5:]:
                            if line.strip():
                                print(f"   🔍 {line}")
            else:
                print(f"   ⚠️ {log_file} not found")
                
    except Exception as e:
        print(f"❌ Log monitoring failed: {e}")
    
    # Test 5: WebSocket Connection Test (if available)
    print("\n\n📋 TEST 5: WEBSOCKET CONNECTION TEST")
    print("-" * 60)
    
    try:
        # Try to test WebSocket connection to pump.fun
        print("�� Testing WebSocket connection to pump.fun...")
        
        try:
            import websockets
            
            # Common pump.fun WebSocket endpoints
            ws_endpoints = [
                "wss://pumpportal.fun/api/data",
                "wss://api.pump.fun/ws",
                "wss://client-api.pump.fun/ws"
            ]
            
            for ws_url in ws_endpoints:
                try:
                    print(f"\n🔌 Testing WebSocket: {ws_url}")
                    
                    async with websockets.connect(ws_url, timeout=5) as websocket:
                        print(f"   ✅ Connected successfully!")
                        
                        # Try to receive a message
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=3)
                            print(f"   📨 Received message: {message[:100]}...")
                        except asyncio.TimeoutError:
                            print(f"   ⏰ No immediate messages received")
                            
                        break  # Exit loop if successful connection
                        
                except Exception as e:
                    print(f"   ❌ Connection failed: {e}")
                    
        except ImportError:
            print("⚠️ websockets package not available")
            
        # Alternative: Check if our integration has WebSocket monitoring
        try:
            from services.pump_fun_monitor import PumpFunMonitor
            
            print("\n🔍 Testing PumpFunMonitor...")
            monitor = PumpFunMonitor()
            print(f"✅ PumpFunMonitor initialized: {type(monitor).__name__}")
            
            # Check for WebSocket methods
            ws_methods = [attr for attr in dir(monitor) if 'websocket' in attr.lower() or 'connect' in attr.lower()]
            if ws_methods:
                print(f"🔌 WebSocket methods: {ws_methods}")
            else:
                print("⚠️ No WebSocket methods found in monitor")
                
        except ImportError as e:
            print(f"⚠️ PumpFunMonitor not available: {e}")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    print("\n" + "=" * 100)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("=" * 100)
    
    # Final verdict
    print("📊 INTEGRATION STATUS ANALYSIS:")
    print("-" * 40)
    
    # Read our test log to see what worked
    if os.path.exists('pump_fun_api_test.log'):
        print("📋 Detailed logs saved to: pump_fun_api_test.log")
        
    print("\n🔍 CONCLUSION:")
    print("   This test shows the ACTUAL API integration status")
    print("   Check the logs above for real API calls and connections")
    print("   If no actual API calls are shown, integration needs work")
    
    return True

if __name__ == "__main__":
    asyncio.run(comprehensive_api_test())
