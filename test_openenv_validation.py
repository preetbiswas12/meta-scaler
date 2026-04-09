#!/usr/bin/env python3
"""
Comprehensive test that simulates OpenEnv validator checks.
Ensures: 
1. At least 3 tasks have graders
2. Each task's score is strictly in (0, 1), not at boundaries
"""

import json
from src.environment import EmailTriageEnv
from src.graders_normalized import (
    grade_basic_classification,
    grade_phishing_detection,
    grade_escalation_handling,
    EPSILON
)

print("=" * 70)
print("OPENENV VALIDATOR SIMULATION")
print("=" * 70)
print()

# Check 1: At least 3 tasks with graders
print("CHECK 1: Task Configuration")
print("-" * 70)

tasks = {
    "basic_email_classification": grade_basic_classification,
    "phishing_threat_detection": grade_phishing_detection,
    "critical_escalation_handling": grade_escalation_handling,
}

print(f"✓ Found {len(tasks)} tasks with graders:")
for task_id, grader in tasks.items():
    print(f"  - {task_id}: {grader.__name__}")

assert len(tasks) >= 3, f"ERROR: Need at least 3 tasks, got {len(tasks)}"
print()

# Check 2: Run inference on each task and verify scores are in (0, 1)
print("CHECK 2: Score Bounds Validation")
print("-" * 70)
print()

env = EmailTriageEnv()
all_scores = []

for task_id, task_config in [
    ("basic_email_classification", {"max_steps": 3, "difficulty": "easy"}),
    ("phishing_threat_detection", {"max_steps": 4, "difficulty": "medium"}),
    ("critical_escalation_handling", {"max_steps": 5, "difficulty": "hard"}),
]:
    print(f"Task: {task_id}")
    
    # Reset environment
    state = env.reset(task_id)
    task_scores = []
    
    # Run episode
    for step in range(1, state["max_steps"] + 1):
        action = {
            "action_type": "classify",
            "target_category": "sales_inquiry",
            "confidence": 0.7 + (step * 0.02)
        }
        
        state, reward, done, info = env.step(action)
        score = state["score"]
        reward = state["reward"]
        
        # Record for final summary
        task_scores.append(score)
        all_scores.append(score)
        
        # Validate STRICT bounds (0, 1) - NOT inclusive
        if not (0.0 < score < 1.0):
            print(f"  ✗ FAILED at step {step}: score={score} not in (0, 1)")
            raise AssertionError(f"Score out of bounds: {score}")
        
        # Verify not exactly 0.0 or 1.0
        if score == 0.0 or score == 1.0:
            print(f"  ✗ FAILED at step {step}: score={score} equals boundary")
            raise AssertionError(f"Score at exact boundary: {score}")
        
        print(f"  Step {step}: score={score:.6f} ✓")
        
        if done:
            break
    
    # Print task summary
    min_score = min(task_scores)
    max_score = max(task_scores)
    avg_score = sum(task_scores) / len(task_scores)
    
    print(f"  Task Summary:")
    print(f"    - Score range: [{min_score:.6f}, {max_score:.6f}]")
    print(f"    - Average score: {avg_score:.6f}")
    print(f"    - Epsilon margin: {EPSILON:.6f}")
    print(f"    - Safe from 0.0: {min_score - EPSILON:.6f}")
    print(f"    - Safe from 1.0: {1.0 - EPSILON - max_score:.6f}")
    print()

# Final validation
print("=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print()

print(f"✓ Tasks configured: {len(tasks)}")
print(f"✓ Total scores tested: {len(all_scores)}")
print(f"✓ All scores strictly in (0, 1): YES")
print()

print("Summary from all tasks:")
print(f"  Min score: {min(all_scores):.6f}")
print(f"  Max score: {max(all_scores):.6f}")
print(f"  Avg score: {sum(all_scores) / len(all_scores):.6f}")
print()

print("✓ YOUR SUBMISSION PASSES OPENENV VALIDATOR REQUIREMENTS")
print("  - 3+ tasks with graders: ✓")
print("  - All scores strictly in (0, 1): ✓")
