#!/usr/bin/env python3
"""Test that all three tasks produce scores strictly within (0, 1)"""

from src.environment import EmailTriageEnv
from src.graders_normalized import EPSILON

env = EmailTriageEnv()

tasks = ["basic_email_classification", "phishing_threat_detection", "critical_escalation_handling"]
print(f"Testing score bounds with EPSILON = {EPSILON}\n")

for task_id in tasks:
    print(f"Task: {task_id}")
    state = env.reset(task_id)
    
    # Check initial score
    score = state["score"]
    print(f"  Initial score: {score}")
    assert 0.0 < score < 1.0, f"ERROR: Initial score {score} not strictly in (0, 1)"
    
    # Run a few steps and check all scores
    for step in range(1, state["max_steps"] + 1):
        action = {
            "action_type": "classify",
            "target_category": "test",
            "confidence": 0.7
        }
        state, reward, done, info = env.step(action)
        score = state["score"]
        
        print(f"  Step {step} score: {score:.6f}, reward: {reward:.6f}", end="")
        
        # Verify bounds
        assert 0.0 < score < 1.0, f"ERROR: Score {score} not in (0, 1) at step {step}"
        assert 0.0 < reward < 1.0, f"ERROR: Reward {reward} not in (0, 1) at step {step}"
        
        # Verify not at exact boundaries  
        assert score != 0.0 and score != 1.0, f"ERROR: Score equals exact boundary"
        assert reward != 0.0 and reward != 1.0, f"ERROR: Reward equals exact boundary"
        
        print(" ✓")
        
        if done:
            break
    
    print(f"  ✓ All scores strictly in (0, 1)\n")

print("✓ ALL TASKS PASS SCORE BOUNDS VALIDATION")
