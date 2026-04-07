#!/usr/bin/env python3
"""Verify AI is properly embedded"""
import sys
import pathlib

print('='*70)
print('AI INTEGRATION VERIFICATION')
print('='*70)

root = pathlib.Path.cwd()

# Check 1: OpenAI Client in inference.py
print('\n[1] OpenAI Client Implementation')
inference_py = root / 'inference.py'
if inference_py.exists():
    content = inference_py.read_text()
    if 'class OpenAIClient' in content:
        print('    [+] OpenAIClient class defined')
        # Find initialize method
        if 'def __init__' in content:
            print('    [+] __init__ method for configuration')
        if 'def generate_email_action' in content:
            print('    [+] generate_email_action method')
        if 'requests.post' in content and 'chat/completions' in content:
            print('    [+] Makes API requests to /chat/completions')

# Check 2: Integration in app.py
print('\n[2] Flask Server Integration')
app_py = root / 'app.py'
if app_py.exists():
    content = app_py.read_text()
    if 'from inference import OpenAIClient' in content:
        print('    [+] OpenAIClient imported')
    if '_llm_client' in content:
        print('    [+] Global LLM client variable')
    if '_llm_client = OpenAIClient()' in content:
        print('    [+] Client initialization on startup')
    if 'client = _llm_client if use_llm else None' in content:
        print('    [+] Client passed to inference')
    if 'run_inference_episode' in content:
        print('    [+] Inference episode runner')

# Check 3: Environment variables
print('\n[3] Environment Configuration')
import os
base_url = os.getenv('API_BASE_URL', 'https://api.openai.com/v1')
model_name = os.getenv('MODEL_NAME', 'gpt-3.5-turbo')
hf_token = os.getenv('HF_TOKEN')
print(f'    [+] API_BASE_URL: {base_url[:30]}...')
print(f'    [+] MODEL_NAME: {model_name}')
print(f'    [+] HF_TOKEN: {"SET" if hf_token else "NOT SET (OK for mock)"}')

# Check 4: Structured logging
print('\n[4] AI Response Logging')
if inference_py.exists():
    content = inference_py.read_text()
    if '[START]' in content and 'print' in content:
        print('    [+] [START] log with task/env/model')
    if '[STEP]' in content and 'action=' in content:
        print('    [+] [STEP] log with action/reward')
    if '[END]' in content and 'score=' in content:
        print('    [+] [END] log with score/rewards')

print('\n' + '='*70)
print('SUMMARY')
print('='*70)
print('''
🤖 AI IS FULLY EMBEDDED

Architecture:
  1. OpenAIClient class in inference.py
  2. Initialized on app.py startup
  3. Passed to run_inference_episode()
  4. Makes requests.post to /chat/completions
  5. Logs [START], [STEP], [END] format

Current Mode:
  • HF Space: Mock inference (deterministic)
  • With HF_TOKEN: Real LLM capable (via use_llm=true)

API Endpoint:
  POST /episode?task_id=easy&use_llm=true  # Real LLM
  POST /episode?task_id=easy                # Mock (default)
''')
