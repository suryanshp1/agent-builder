#!/usr/bin/env python3
"""
WebSocket Execution Log Streaming Demo

This script demonstrates real-time execution log streaming via WebSocket.

Requirements:
    pip install websockets asyncio

Usage:
    python demo_websocket.py <execution_id>
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime


async def stream_execution_logs(execution_id: str):
    """
    Connect to WebSocket and stream execution logs
    
    Args:
        execution_id: Execution UUID to monitor
    """
    uri = f"ws://localhost:8000/ws/executions/{execution_id}"
    
    print(f"\n{'='*60}")
    print(f"📡 Connecting to WebSocket...")
    print(f"URI: {uri}")
    print(f"{'='*60}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Streaming logs...\n")
            
            # Receive messages
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "execution_state":
                    # Execution state update
                    state = data.get("data", {})
                    status = state.get("status", "unknown")
                    
                    print(f"\n{'─'*60}")
                    print(f"📊 Execution Status: {status.upper()}")
                    
                    if state.get("started_at"):
                        print(f"⏱️  Started: {state['started_at']}")
                    
                    if state.get("completed_at"):
                        print(f"✅ Completed: {state['completed_at']}")
                    
                    if state.get("error_message"):
                        print(f"❌ Error: {state['error_message']}")
                    
                    print(f"{'─'*60}\n")
                
                elif message_type == "log":
                    # Log entry
                    log = data.get("data", {})
                    step = log.get("step_number", 0)
                    log_type = log.get("log_type", "unknown")
                    log_data = log.get("log_data", {})
                    timestamp = log.get("timestamp", "")
                    
                    # Format timestamp
                    if timestamp:
                        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = ts.strftime("%H:%M:%S")
                    else:
                        time_str = "??:??:??"
                    
                    # Color code by log type
                    if log_type == "llm_start":
                        icon = "🤖"
                        color = "\033[94m"  # Blue
                        message = f"LLM starting with model: {log_data.get('model', 'unknown')}"
                    elif log_type == "llm_end":
                        icon = "💬"
                        color = "\033[92m"  # Green
                        message = "LLM response complete"
                    elif log_type == "tool_start":
                        icon = "🔧"
                        color = "\033[93m"  # Yellow
                        tool_name = log_data.get('tool', 'unknown')
                        message = f"Tool: {tool_name}"
                    elif log_type == "tool_end":
                        icon = "✓"
                        color = "\033[92m"  # Green
                        output = log_data.get('output', '')
                        message = f"Tool output: {output[:100]}..."
                    elif log_type == "error":
                        icon = "❌"
                        color = "\033[91m"  # Red
                        error = log_data.get('error', 'Unknown error')
                        message = f"Error: {error}"
                    else:
                        icon = "📝"
                        color = "\033[0m"  # Default
                        message = f"{log_type}: {str(log_data)[:100]}"
                    
                    reset = "\033[0m"
                    print(f"{color}[{time_str}] Step {step} {icon} {message}{reset}")
                
                elif message_type == "execution_complete":
                    # Execution finished
                    result = data.get("data", {})
                    status = result.get("status", "unknown")
                    
                    print(f"\n{'='*60}")
                    if status == "success":
                        print("🎉 EXECUTION COMPLETED SUCCESSFULLY!")
                        if result.get("output_data"):
                            print("\n📄 Output:")
                            print(json.dumps(result["output_data"], indent=2))
                    else:
                        print(f"❌ EXECUTION FAILED: {status}")
                        if result.get("error_message"):
                            print(f"\nError: {result['error_message']}")
                    print(f"{'='*60}\n")
                    
                    break
                
                elif message_type == "error":
                    # Error message
                    error_msg = data.get("message", "Unknown error")
                    print(f"\n❌ WebSocket Error: {error_msg}\n")
                    break
    
    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket Error: {str(e)}")
        print("Make sure the backend is running and the execution_id is valid.\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Disconnected by user\n")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\n❌ Error: Missing execution_id")
        print("\nUsage:")
        print("    python demo_websocket.py <execution_id>")
        print("\nExample:")
        print("    python demo_websocket.py 550e8400-e29b-41d4-a716-446655440000")
        print("\nTo get an execution_id:")
        print("    1. Create an agent via API")
        print("    2. Execute the agent: POST /api/executions/agent/{agent_id}")
        print("    3. Use the returned execution_id")
        print()
        sys.exit(1)
    
    execution_id = sys.argv[1]
    
    # Run async
    asyncio.run(stream_execution_logs(execution_id))


if __name__ == "__main__":
    main()
