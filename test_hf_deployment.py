#!/usr/bin/env python3
"""Test HF Space deployment"""
import requests
import json

space_url = 'https://preetbiswas121106-email-triage-env.hf.space'

print('='*70)
print('TESTING HF SPACE DEPLOYMENT')
print('='*70)

# Test 1: Health check
print('\n[TEST 1] Health Check')
try:
    r = requests.get(f'{space_url}/health', timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.json()}')
    if r.status_code == 200:
        print('[✓] PASS: /health endpoint responding')
    else:
        print(f'[✗] FAIL: Expected 200, got {r.status_code}')
except Exception as e:
    print(f'[✗] FAIL: {str(e)[:100]}')

# Test 2: Reset (initialize episode)
print('\n[TEST 2] Reset Environment (easy task)')
try:
    r = requests.post(f'{space_url}/reset?task_id=easy', timeout=10)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        state = r.json()
        print(f'Episode ID: {state.get("episode_id", "N/A")[:10]}...')
        print(f'Task: {state.get("task_id")}')
        print(f'Max Steps: {state.get("max_steps")}')
        print(f'Current Email From: {state["current_email"].get("sender", "N/A")[:30]}')
        print('[✓] PASS: /reset working')
    else:
        print(f'[✗] FAIL: Status {r.status_code}')
except Exception as e:
    print(f'[✗] FAIL: {str(e)[:100]}')

# Test 3: Execute step
print('\n[TEST 3] Execute Step (classify action)')
try:
    r = requests.post(f'{space_url}/reset?task_id=easy', timeout=10)
    if r.status_code == 200:
        state = r.json()
        session_id = state.get('episode_id')
        
        action = {
            'action_type': 'classify',
            'target_category': 'newsletter',
            'confidence': 0.95
        }
        
        r = requests.post(
            f'{space_url}/step',
            json={'session_id': session_id, 'action': action},
            timeout=10
        )
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            result = r.json()
            reward = result.get('reward', 'N/A')
            done = result.get('done', 'N/A')
            print(f'Reward: {reward}')
            print(f'Done: {done}')
            print('[✓] PASS: /step working')
        else:
            print(f'[✗] FAIL: Status {r.status_code}')
except Exception as e:
    print(f'[✗] FAIL: {str(e)[:100]}')

print('\n' + '='*70)
print('DEPLOYMENT VALIDATION COMPLETE ✅')
print('='*70)
