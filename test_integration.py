"""
Integration tests for Email Triage environment
"""
import sys
import json
from src.environment import EmailTriageEnv, ActionSchema
from src.graders_normalized import EmailTriageGrader


def test_environment_initialization():
    """Test environment can be initialized"""
    env = EmailTriageEnv()
    assert env is not None
    print("✓ Environment initialization OK")


def test_reset_easy():
    """Test reset on easy task"""
    env = EmailTriageEnv()
    state = env.reset("easy")
    assert state["difficulty"] == "easy"
    assert state["current_email"]["sender"] != ""
    assert state["step"] == 0
    # Score must be strictly in (0, 1), initialized to 0.5
    assert 0.0 < state["score"] < 1.0, f"Score {state['score']} not in (0, 1)"
    assert state["done"] == False
    assert state["max_steps"] == 3
    print("✓ Reset easy task OK")


def test_reset_medium():
    """Test reset on medium task"""
    env = EmailTriageEnv()
    state = env.reset("medium")
    assert state["difficulty"] == "medium"
    assert state["current_email"]["subject"] != ""
    assert state["max_steps"] == 4
    print("✓ Reset medium task OK")


def test_reset_hard():
    """Test reset on hard task"""
    env = EmailTriageEnv()
    state = env.reset("hard")
    assert state["difficulty"] == "hard"
    assert state["current_email"]["email_id"] != ""
    assert state["max_steps"] == 5
    print("✓ Reset hard task OK")


def test_step_execution_classify():
    """Test step execution with classify action"""
    env = EmailTriageEnv()
    state = env.reset("easy")

    action = {
        "action_type": "classify",
        "target_category": "sales_inquiry",
        "confidence": 0.9
    }

    state, reward, done, info = env.step(action)
    assert state["step"] == 1
    assert isinstance(reward, float)
    assert isinstance(state["score"], float)
    assert -1.0 <= state["score"] <= 1.0
    print("✓ Step execution classify OK")


def test_step_execution_prioritize():
    """Test step execution with prioritize action"""
    env = EmailTriageEnv()
    state = env.reset("easy")

    action = {
        "action_type": "prioritize",
        "priority_level": 2,
        "confidence": 0.8
    }

    state, reward, done, info = env.step(action)
    assert state["step"] == 1
    assert isinstance(reward, float)
    print("✓ Step execution prioritize OK")


def test_step_execution_reply():
    """Test step execution with reply action"""
    env = EmailTriageEnv()
    state = env.reset("easy")

    action = {
        "action_type": "reply",
        "reply_draft": "Thank you for your inquiry",
        "confidence": 0.75
    }

    state, reward, done, info = env.step(action)
    assert state["step"] == 1
    print("✓ Step execution reply OK")


def test_step_execution_escalate():
    """Test step execution with escalate action"""
    env = EmailTriageEnv()
    state = env.reset("medium")

    action = {
        "action_type": "escalate",
        "escalation_reason": "Requires management attention",
        "confidence": 0.85
    }

    state, reward, done, info = env.step(action)
    assert state["step"] == 1
    print("✓ Step execution escalate OK")


def test_step_execution_archive():
    """Test step execution with archive action"""
    env = EmailTriageEnv()
    state = env.reset("easy")

    action = {
        "action_type": "archive",
        "confidence": 0.8
    }

    state, reward, done, info = env.step(action)
    assert state["step"] == 1
    print("✓ Step execution archive OK")


def test_email_grader_classification():
    """Test email grader classification scoring"""
    grader = EmailTriageGrader()
    
    action = ActionSchema(
        action_type="classify",
        target_category="sales_inquiry",
        confidence=0.95
    )
    
    email = {"email_id": "test"}
    ground_truth = {"category": "sales_inquiry"}
    
    reward, info = grader.grade_action(action, email, ground_truth, is_correct_sequence=True, step_number=1, total_steps=3, difficulty="easy")
    
    assert reward > 0, "Correct classification should have positive reward"
    assert info["metrics"]["quality"] in ["perfect", "correct", "low_confidence"], f"Expected good quality, got {info['metrics']['quality']}"
    print("✓ Email grader classification OK")


def test_grader_deterministic():
    """Test email grader produces deterministic results"""
    grader = EmailTriageGrader()
    
    action = ActionSchema(
        action_type="classify",
        target_category="phishing",
        confidence=0.98
    )
    
    email = {"email_id": "test"}
    ground_truth = {"category": "phishing", "priority": 4}
    
    reward1, info1 = grader.grade_action(action, email, ground_truth, is_correct_sequence=True, step_number=1, total_steps=4, difficulty="easy")
    reward2, info2 = grader.grade_action(action, email, ground_truth, is_correct_sequence=True, step_number=1, total_steps=4, difficulty="easy")
    
    assert reward1 == reward2, "Grading should be deterministic"
    print("✓ Grader deterministic OK")


def test_multi_step_episode():
    """Test multi-step email triage episode"""
    env = EmailTriageEnv()
    state = env.reset("medium")
    
    actions = [
        {"action_type": "classify", "target_category": "phishing", "confidence": 0.9},
        {"action_type": "prioritize", "priority_level": 4, "confidence": 0.85},
        {"action_type": "escalate", "escalation_reason": "Phishing threat", "confidence": 0.95}
    ]
    
    total_reward = 0.0
    for i, action in enumerate(actions):
        state, reward, done, info = env.step(action)
        total_reward += reward
        assert state["step"] == i + 1
        assert len(state["actions_taken"]) == i + 1
        if done:
            break
    
    assert total_reward is not None
    print(f"✓ Multi-step episode OK (total_reward: {total_reward:.3f})")


def test_state_consistency():
    """Test state() method returns consistent data"""
    env = EmailTriageEnv()
    state1 = env.reset("easy")
    state2 = env.state()
    
    assert state1 == state2, "state() should return same data as reset()"
    assert state2["step"] == 0
    print("✓ State consistency OK")


def test_error_handling_invalid_task():
    """Test error handling for invalid task"""
    env = EmailTriageEnv()
    
    try:
        env.reset("invalid_task")
        assert False, "Should raise ValueError"
    except ValueError:
        print("✓ Error handling invalid task OK")


def test_error_handling_invalid_action():
    """Test error handling for invalid action"""
    env = EmailTriageEnv()
    state = env.reset("easy")
    
    try:
        # Missing required fields
        invalid_action = {"invalid_field": "value"}
        state, reward, done, info = env.step(invalid_action)
        # Should handle gracefully
        assert state is not None
        print("✓ Error handling invalid action OK")
    except Exception as e:
        # Also acceptable to raise
        print(f"✓ Error handling invalid action OK (raised: {type(e).__name__})")


def test_mock_actions_valid():
    """Test mock actions are valid JSON"""
    from inference import _get_mock_action
    
    for difficulty in ["easy", "medium", "hard"]:
        for step in range(1, 6):
            action_json = _get_mock_action(difficulty, step)
            action = json.loads(action_json)
            assert "action_type" in action
            print(f"✓ Mock action {difficulty} step {step} valid")


def test_all_email_scenarios():
    """Test all email scenarios can be loaded"""
    env = EmailTriageEnv()
    
    for difficulty in ["easy", "medium", "hard"]:
        state = env.reset(difficulty)
        email = state["current_email"]
        
        assert email["email_id"] != ""
        assert email["sender"] != ""
        assert email["subject"] != ""
        assert email["body"] != ""
        assert "category" in state["ground_truth"]
        assert "priority" in state["ground_truth"]
        print(f"✓ Email scenario {difficulty} OK")


def test_ground_truth_labels():
    """Test ground truth labels are complete"""
    env = EmailTriageEnv()
    state = env.reset("hard")
    
    gt = state["ground_truth"]
    assert "category" in gt
    assert "priority" in gt
    assert "should_reply" in gt
    assert "description" in gt
    assert 1 <= gt["priority"] <= 5
    print("✓ Ground truth labels OK")


def test_reward_range():
    """Test reward values are in reasonable range"""
    env = EmailTriageEnv()
    state = env.reset("easy")
    
    action = {
        "action_type": "classify",
        "target_category": "sales_inquiry",
        "confidence": 0.9
    }
    
    state, reward, done, info = env.step(action)
    
    # Rewards should be bounded
    assert -2.0 <= reward <= 2.0, f"Reward {reward} out of bounds"
    print(f"✓ Reward range OK (reward: {reward:.3f})")


def test_action_schema_validation():
    """Test ActionSchema validates properly"""
    valid_action = ActionSchema(
        action_type="classify",
        target_category="phishing",
        confidence=0.95
    )
    assert valid_action is not None
    print("✓ ActionSchema validation OK")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_environment_initialization,
        test_reset_easy,
        test_reset_medium,
        test_reset_hard,
        test_step_execution_classify,
        test_step_execution_prioritize,
        test_step_execution_reply,
        test_step_execution_escalate,
        test_step_execution_archive,
        test_email_grader_classification,
        test_grader_deterministic,
        test_multi_step_episode,
        test_state_consistency,
        test_error_handling_invalid_task,
        test_error_handling_invalid_action,
        test_mock_actions_valid,
        test_all_email_scenarios,
        test_ground_truth_labels,
        test_reward_range,
        test_action_schema_validation,
    ]

    print("=" * 60)
    print("Running Email Triage Integration Tests")
    print("=" * 60)

    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    total = len(tests)
    passed = total - failed
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
