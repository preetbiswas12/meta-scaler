#!/usr/bin/env python3
"""Test validator readiness - checks if all components are discoverable."""

import sys
from pathlib import Path

def test_imports():
    """Test if all graders can be imported."""
    print("\n[TEST 1] Testing grader imports...")
    try:
        from src.graders_normalized import (
            grade_action,
            grade_basic_classification,
            grade_phishing_detection,
            grade_escalation_handling,
        )
        print("  ✓ All grader functions imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_environment():
    """Test if environment can be initialized with all task IDs."""
    print("\n[TEST 2] Testing environment initialization...")
    from src.environment import EmailTriageEnv
    
    tasks = [
        "basic_email_classification",
        "phishing_threat_detection",
        "critical_escalation_handling",
    ]
    
    all_passed = True
    for task_id in tasks:
        try:
            env = EmailTriageEnv()
            state = env.reset(task_id)
            
            # Verify state contains required fields
            assert "task_id" in state, f"Missing task_id in state"
            assert "difficulty" in state, f"Missing difficulty in state"
            assert state["task_id"] == task_id, f"task_id mismatch"
            
            print(f"  ✓ {task_id:40s} → difficulty: {state['difficulty']}")
        except Exception as e:
            print(f"  ✗ {task_id:40s} failed: {e}")
            all_passed = False
    
    return all_passed

def test_grader_callable():
    """Test if graders can be called with expected arguments."""
    print("\n[TEST 3] Testing grader callability...")
    from src.graders_normalized import grade_basic_classification
    
    try:
        # Mock objects
        action = type('Action', (), {'action_type': 'classify', 'confidence': 0.8})()
        email = {'email_id': 'test_001', 'subject': 'Test'}
        ground_truth = {'category': 'test', 'priority': 1, 'ambiguity': 'low'}
        
        reward, info = grade_basic_classification(
            action=action,
            email=email,
            ground_truth=ground_truth,
            step_number=1,
        )
        
        assert isinstance(reward, float), f"Reward should be float, got {type(reward)}"
        assert 0 < reward < 1, f"Reward should be in (0, 1), got {reward}"
        assert isinstance(info, dict), f"Info should be dict, got {type(info)}"
        
        print(f"  ✓ Grader callable with correct signature")
        print(f"    Reward: {reward:.6f}")
        return True
    except Exception as e:
        print(f"  ✗ Grader call failed: {e}")
        return False

def test_yaml_validity():
    """Check if openenv.yaml exists and is not shadowed."""
    print("\n[TEST 4] Checking openenv.yaml configuration...")
    
    root_yaml = Path("openenv.yaml")
    config_yaml = Path("config/openenv.yaml")
    
    if root_yaml.exists():
        print(f"  ✓ Root openenv.yaml found")
    else:
        print(f"  ✗ Root openenv.yaml NOT found")
        return False
    
    if config_yaml.exists():
        print(f"  ⚠ Warning: config/openenv.yaml exists (shadow YAML)")
        print(f"    The validator will use the root openenv.yaml only")
        return False
    else:
        print(f"  ✓ No shadow YAML config/openenv.yaml (good!)")
    
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("VALIDATOR READINESS TEST")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_environment,
        test_grader_callable,
        test_yaml_validity,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 70)
    if all(results):
        print("✓ ALL TESTS PASSED - Ready for validator submission!")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME TESTS FAILED - Fix issues before submitting")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
