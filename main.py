#!/usr/bin/env python3
"""Integration tests for EmailTriageEnv."""

import json
import sys
from typing import Dict, Any

from src.environment import EmailTriageEnv, ActionSchema


def test_easy_episode():
    """Test an easy difficulty episode."""
    print("\n" + "=" * 80)
    print("TEST: Easy Episode (3 required steps)")
    print("=" * 80)
    
    env = EmailTriageEnv()
    state = env.reset(task_id="easy")
    
    print(f"\nInitial State:")
    print(f"  Episode ID: {state['episode_id']}")
    print(f"  Email: {state['current_email']['subject']}")
    print(f"  Required Actions: {state['ground_truth']['description']}")
    
    # Simulate required actions: classify -> prioritize -> archive
    actions = [
        {
            "action_type": "classify",
            "target_category": state['ground_truth']['category'],
            "confidence": 0.9
        },
        {
            "action_type": "prioritize",
            "priority_level": state['ground_truth']['priority'],
            "confidence": 0.8
        },
        {
            "action_type": "archive",
            "confidence": 0.7
        }
    ]
    
    total_reward = 0
    for i, action_dict in enumerate(actions, 1):
        print(f"\nStep {i}: Taking action '{action_dict['action_type']}'")
        
        # Convert to ActionSchema
        action = ActionSchema(**action_dict)
        
        # Execute step
        state, reward, done, info = env.step(action_dict)
        
        print(f"  Reward: {reward:.4f}")
        print(f"  Done: {done}")
        print(f"  Info: {json.dumps(info, indent=2, default=str)}")
        
        total_reward += reward
        
        if done:
            print(f"\n[OK] Episode completed after {i} steps")
            break
    
    print(f"\nFinal Score: {state['score']:.4f}")
    print(f"Total Episode Reward: {total_reward:.4f}")
    
    # Test passes if episode completed (all required actions taken in sequence)
    all_required_completed = state.get('actions_taken') and len(state['actions_taken']) >= 3
    assert all_required_completed, "Easy episode should complete with 3+ actions"


def test_medium_episode():
    """Test a medium difficulty episode."""
    print("\n" + "=" * 80)
    print("TEST: Medium Episode (4 required steps)")
    print("=" * 80)
    
    env = EmailTriageEnv()
    state = env.reset(task_id="medium")
    
    print(f"\nInitial State:")
    print(f"  Episode ID: {state['episode_id']}")
    print(f"  Email: {state['current_email']['subject']}")
    print(f"  Required Actions: {state['ground_truth']['description']}")
    
    # Simulate required actions: classify -> prioritize -> reply -> archive
    actions = [
        {
            "action_type": "classify",
            "target_category": state['ground_truth']['category'],
            "confidence": 0.9
        },
        {
            "action_type": "prioritize",
            "priority_level": state['ground_truth']['priority'],
            "confidence": 0.8
        },
        {
            "action_type": "reply",
            "reply_draft": "Thank you for your inquiry. We are looking into this matter and will follow up shortly.",
            "confidence": 0.8
        },
        {
            "action_type": "archive",
            "confidence": 0.7
        }
    ]
    
    total_reward = 0
    for i, action_dict in enumerate(actions, 1):
        print(f"\nStep {i}: Taking action '{action_dict['action_type']}'")
        
        action = ActionSchema(**action_dict)
        state, reward, done, info = env.step(action_dict)
        
        print(f"  Reward: {reward:.4f}")
        print(f"  Done: {done}")
        
        total_reward += reward
        
        if done:
            print(f"\n[OK] Episode completed after {i} steps")
            break
    
    print(f"\nFinal Score: {state['score']:.4f}")
    print(f"Total Episode Reward: {total_reward:.4f}")
    
    # Test passes if episode completed (all required actions taken in sequence)
    all_required_completed = state.get('actions_taken') and len(state['actions_taken']) >= 4
    assert all_required_completed, "Medium episode should complete with 4+ actions"


def test_hard_episode():
    """Test a hard difficulty episode."""
    print("\n" + "=" * 80)
    print("TEST: Hard Episode (5 required steps)")
    print("=" * 80)
    
    env = EmailTriageEnv()
    state = env.reset(task_id="hard")
    
    print(f"\nInitial State:")
    print(f"  Episode ID: {state['episode_id']}")
    print(f"  Email: {state['current_email']['subject']}")
    print(f"  Required Actions: {state['ground_truth']['description']}")
    
    # Simulate required actions: classify -> prioritize -> escalate -> reply -> archive
    actions = [
        {
            "action_type": "classify",
            "target_category": state['ground_truth']['category'],
            "confidence": 0.95
        },
        {
            "action_type": "prioritize",
            "priority_level": state['ground_truth']['priority'],
            "confidence": 0.9
        },
        {
            "action_type": "escalate",
            "escalation_reason": "Critical business issue requiring immediate action",
            "confidence": 0.9
        },
        {
            "action_type": "reply",
            "reply_draft": "We take this matter seriously and have escalated to our executive team for immediate investigation. We will provide a detailed update within 2 hours.",
            "confidence": 0.85
        },
        {
            "action_type": "archive",
            "confidence": 0.7
        }
    ]
    
    total_reward = 0
    for i, action_dict in enumerate(actions, 1):
        print(f"\nStep {i}: Taking action '{action_dict['action_type']}'")
        
        action = ActionSchema(**action_dict)
        state, reward, done, info = env.step(action_dict)
        
        print(f"  Reward: {reward:.4f}")
        print(f"  Done: {done}")
        
        total_reward += reward
        
        if done:
            print(f"\n[OK] Episode completed after {i} steps")
            break
    
    print(f"\nFinal Score: {state['score']:.4f}")
    print(f"Total Episode Reward: {total_reward:.4f}")
    
    # Test passes if episode completed (all required actions taken in sequence)
    all_required_completed = state.get('actions_taken') and len(state['actions_taken']) >= 5
    assert all_required_completed, "Hard episode should complete with 5+ actions"


def test_out_of_sequence():
    """Test that out-of-sequence actions are penalized."""
    print("\n" + "=" * 80)
    print("TEST: Out-of-Sequence Actions")
    print("=" * 80)
    
    env = EmailTriageEnv()
    state = env.reset(task_id="easy")
    
    print(f"\nTrying to take 'archive' as first action (should be 'classify')...")
    
    action = {
        "action_type": "archive",
        "confidence": 0.5
    }
    
    state, reward, done, info = env.step(action)
    
    print(f"  Reward: {reward:.4f}")
    print(f"  Is correct sequence: {info.get('is_correct_sequence', 'N/A')}")
    
    # Normalized system: out-of-sequence penalty is -0.10 (small, bounded)
    # Should have negative reward
    assert reward < -0.05, f"Out-of-sequence penalty should be negative, got {reward}"


def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("EMAIL TRIAGE ENVIRONMENT - INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Easy Episode", test_easy_episode),
        ("Medium Episode", test_medium_episode),
        ("Hard Episode", test_hard_episode),
        ("Out-of-Sequence Penalty", test_out_of_sequence),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            test_func()  # Assertions now handle pass/fail
            results[test_name] = ("PASS", None)
        except AssertionError as e:
            results[test_name] = ("FAIL", str(e))
            print(f"\n[FAIL] {test_name}: {e}")
        except Exception as e:
            results[test_name] = ("ERROR", str(e))
            print(f"\n[ERROR] {test_name}: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, (status, error) in results.items():
        if error:
            print(f"  {test_name}: {status} - {error}")
        else:
            print(f"  {test_name}: {status}")
    
    # Exit code
    passed = sum(1 for status, _ in results.values() if status == "PASS")
    failed = sum(1 for status, _ in results.values() if status in ("FAIL", "ERROR"))
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
