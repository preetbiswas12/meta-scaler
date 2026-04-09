#!/usr/bin/env python3
"""Verify all 3 tasks have correct graders."""
from inference import run_inference_episode
from src.environment import EmailTriageEnv

tasks = ['easy', 'medium', 'hard']
expected_graders = {
    'easy': 'easy_grader',
    'medium': 'medium_grader', 
    'hard': 'hard_grader'
}

print('Task → Grader Mapping Verification')
print('='*60)

all_correct = True
for task in tasks:
    env = EmailTriageEnv()
    result = run_inference_episode(env, task)
    actual_grader = result['grader_id']
    expected_grader = expected_graders[task]
    score = result['final_score']
    
    match = "✓" if actual_grader == expected_grader else "✗"
    print(f"{match} {task:8} → {actual_grader:14} (expected: {expected_grader:14}) score: {score:.2f}")
    
    if actual_grader != expected_grader:
        all_correct = False

print('='*60)
if all_correct:
    print("✓ All 3 tasks have correct graders!")
else:
    print("✗ Some graders are mismatched!")
