#!/usr/bin/env python3
"""
Test script for Chainlit server at localhost:8000
Uses WebSocket to simulate chat messages
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_chainlit_message(message="Hey!"):
    """Send a test message to Chainlit WebSocket"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[OK] Connected to Chainlit at {uri}")
            
            # Send a chat message
            message_data = {
                "type": "user_message",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(message_data))
            print(f"[SENT] {message}")
            
            # Wait for response
            print("[WAIT] Waiting for response...")
            
            response_count = 0
            while response_count < 10:  # Wait for up to 10 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    
                    print(f"[RECV] Response {response_count + 1}: {response_data}")
                    response_count += 1
                    
                    # Break if we get a complete message
                    if response_data.get("type") == "message" and response_data.get("content"):
                        break
                        
                except asyncio.TimeoutError:
                    print("[TIMEOUT] Timeout waiting for response")
                    break
                except json.JSONDecodeError:
                    print(f"[RAW] Raw response: {response}")
                    
    except ConnectionRefusedError:
        print("[ERROR] Failed to connect to localhost:8000 - is Chainlit running?")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False
    
    print("[OK] Test completed")
    return True

async def simple_http_test():
    """Simple HTTP test to check if server is running"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000') as response:
                print(f"[OK] HTTP Status: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    if "chainlit" in text.lower() or "freibot" in text.lower():
                        print("[OK] Chainlit app is running")
                        return True
                    else:
                        print("[WARN] Server running but may not be Chainlit")
                        
    except Exception as e:
        print(f"[ERROR] HTTP test failed: {e}")
        
    return False

async def main():
    """Main test function"""
    print("Testing Chainlit server at localhost:8000")
    print("=" * 50)
    
    # First check if server is reachable via HTTP
    print("1. Testing HTTP connection...")
    http_ok = await simple_http_test()
    
    if not http_ok:
        print("[ERROR] HTTP test failed - server may not be running")
        return
    
    print("\n2. Testing WebSocket chat...")
    
    # Test with the message that was failing
    messages_to_test = [
        "Hey!",
        "Hallo",
        "Wie viele Einwohner hat Freiburg?"
    ]
    
    for msg in messages_to_test:
        print(f"\n--- Testing: '{msg}' ---")
        success = await test_chainlit_message(msg)
        if not success:
            print(f"[ERROR] Test failed for: {msg}")
        await asyncio.sleep(2)  # Brief pause between tests

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow custom message from command line
        message = " ".join(sys.argv[1:])
        asyncio.run(test_chainlit_message(message))
    else:
        asyncio.run(main())