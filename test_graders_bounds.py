#!/usr/bin/env python3
"""Test graders for all three tasks"""

from src.graders_normalized import (
    grade_basic_classification,
    grade_phishing_detection,
    grade_escalation_handling,
    EPSILON
)

print(f"Testing graders with EPSILON = {EPSILON}\n")

# Test data
email = {
    "email_id": "test_001",
    "sender": "test@example.com",
    "subject": "Test email",
    "body": "Test body"
}

ground_truth = {
    "category": "sales_inquiry",
    "priority": 2,
    "should_reply": True,
    "actions": ["classify", "prioritize", "reply"],
    "ambiguity": "low"
}

class MockAction:
    def __init__(self, action_type, **kwargs):
        self.action_type = action_type
        self.confidence = kwargs.get("confidence", 0.7)
        self.target_category = kwargs.get("target_category", "sales_inquiry")
        self.priority_level = kwargs.get("priority_level", 2)

# Test each grader
granders = [
    ("basic_email_classification", grade_basic_classification, 3),
    ("phishing_threat_detection", grade_phishing_detection, 4),
    ("critical_escalation_handling", grade_escalation_handling, 5),
]

for task_name, grader_func, max_steps in granders:
    print(f"Task: {task_name}")
    
    for step in range(1, max_steps + 1):
        action = MockAction("classify", confidence=0.8, target_category="sales_inquiry")
        
        reward, info = grader_func(
            action=action,
            email=email,
            ground_truth=ground_truth,
            step_number=step
        )
        
        print(f"  Step {step}: reward={reward:.6f}", end="")
        
        # Verify bounds
        assert 0.0 < reward < 1.0, f"ERROR: Reward {reward} not in (0, 1)"
        assert reward != 0.0 and reward != 1.0, f"ERROR: Reward equals exact boundary"
        
        print(" ✓")
    
    print(f"  ✓ Grader passes bounds validation\n")

print("✓ ALL GRADERS PASS SCORE BOUNDS VALIDATION")
