#!/usr/bin/env python3
"""Test health check endpoint directly."""
import sys
import time

try:
    # Test imports
    print("[1/3] Testing imports...")
    from src.environment import EmailTriageEnv
    print("      ✓ EmailTriageEnv imported")
    
    from inference import OpenAIClient, run_inference_episode
    print("      ✓ OpenAIClient imported")
    
    from app import app
    print("      ✓ Flask app imported")
    
    # Test app.test_client
    print("\n[2/3] Testing health endpoint...")
    client = app.test_client()
    response = client.get('/health')
    print(f"      Status: {response.status_code}")
    print(f"      Response: {response.json}")
    
    if response.status_code != 200:
        print("      ✗ FAILED: Expected 200")
        sys.exit(1)
    
    # Test environment creation
    print("\n[3/3] Testing environment creation...")
    env = EmailTriageEnv()
    state = env.reset("easy")
    print(f"      ✓ Environment created successfully")
    print(f"      First email subject: {state['current_email']['subject'][:50]}")
    
    print("\n✅ All tests passed! App should work.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
