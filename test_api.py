#!/usr/bin/env python3
"""
Quick test of the Flask app API endpoints.
"""

import os
import json
import subprocess
import time
import requests
import signal
import sys
from pathlib import Path

def test_api_locally():
    """Start Flask app and test endpoints."""
    print("=" * 70)
    print("TESTING FLASK API LOCALLY")
    print("=" * 70 + "\n")
    
    # Start Flask app in background
    print("→ Starting Flask app on port 8000...")
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).parent
    )
    
    # Wait for app to start
    time.sleep(3)
    
    try:
        base_url = "http://localhost:8000"
        
        # Test 1: Health check
        print("\n✓ Test 1: GET /health")
        resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
        assert resp.status_code == 200, "Health check failed"
        
        # Test 2: Index/docs
        print("\n✓ Test 2: GET /")
        resp = requests.get(base_url, timeout=5)
        print(f"  Status: {resp.status_code}")
        print(f"  Name: {resp.json().get('name')}")
        assert resp.status_code == 200, "Index failed"
        
        # Test 3: Reset environment
        print("\n✓ Test 3: POST /reset?task_id=easy")
        resp = requests.post(f"{base_url}/reset?task_id=easy", timeout=5)
        print(f"  Status: {resp.status_code}")
        data = resp.json()
        session_id = data.get("session_id")
        print(f"  Session ID: {session_id}")
        assert resp.status_code == 200, "Reset failed"
        assert session_id, "No session ID returned"
        
        # Test 4: Execute step
        print("\n✓ Test 4: POST /step")
        action = {
            "action_type": "classify",
            "target_category": "sales_inquiry",
            "confidence": 0.9
        }
        resp = requests.post(
            f"{base_url}/step",
            json={
                "session_id": session_id,
                "action": action
            },
            timeout=5
        )
        print(f"  Status: {resp.status_code}")
        data = resp.json()
        print(f"  Reward: {data.get('reward')}")
        print(f"  Done: {data.get('done')}")
        assert resp.status_code == 200, "Step failed"
        
        # Test 5: List sessions
        print("\n✓ Test 5: GET /sessions")
        resp = requests.get(f"{base_url}/sessions", timeout=5)
        print(f"  Status: {resp.status_code}")
        sessions = resp.json().get("sessions", [])
        print(f"  Active sessions: {len(sessions)}")
        assert resp.status_code == 200, "List sessions failed"
        
        # Test 6: Run full episode
        print("\n✓ Test 6: POST /episode?task_id=easy")
        resp = requests.post(f"{base_url}/episode?task_id=easy", timeout=30)
        print(f"  Status: {resp.status_code}")
        data = resp.json()
        print(f"  Final score: {data.get('final_score')}")
        print(f"  Steps: {data.get('steps')}")
        print(f"  Success: {data.get('success')}")
        assert resp.status_code == 200, "Episode failed"
        
        # Test 7: Delete session
        print("\n✓ Test 7: DELETE /sessions/{session_id}")
        resp = requests.delete(f"{base_url}/sessions/{session_id}", timeout=5)
        print(f"  Status: {resp.status_code}")
        assert resp.status_code == 200, "Delete session failed"
        
        print("\n" + "=" * 70)
        print("✓ ALL API TESTS PASSED")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}\n")
        raise
    
    finally:
        # Kill the Flask app
        print("→ Stopping Flask app...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    try:
        test_api_locally()
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
