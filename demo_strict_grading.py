#!/usr/bin/env python3
"""
Demonstration of stricter, more deterministic grading.
Shows reward differences between correct/incorrect actions.
"""
import sys
import json
from src.environment import EmailTriageEnv, ActionSchema
from src.graders_normalized import EmailTriageGrader

def demo_classification_strictness():
    print("\n" + "="*70)
    print("DEMO 1: Classification Strictness")
    print("="*70)
    
    env = EmailTriageEnv()
    state = env.reset("easy")
    ground_truth = state["ground_truth"]
    email = state["current_email"]
    
    grader = EmailTriageGrader()
    
    # Correct classification with high confidence
    action_correct_confident = {
        "action_type": "classify",
        "target_category": ground_truth["category"],
        "confidence": 0.95
    }
    reward_c_c, info_c_c = grader.grade_action(
        action_correct_confident, email, ground_truth, True, 1, 3
    )
    
    # Correct but low confidence
    action_correct_tentative = {
        "action_type": "classify",
        "target_category": ground_truth["category"],
        "confidence": 0.6
    }
    reward_c_t, info_c_t = grader.grade_action(
        action_correct_tentative, email, ground_truth, True, 1, 3
    )
    
    # Wrong classification
    action_wrong = {
        "action_type": "classify",
        "target_category": "phishing",  # Likely wrong
        "confidence": 0.9
    }
    reward_w, info_w = grader.grade_action(
        action_wrong, email, ground_truth, True, 1, 3
    )
    
    # Invalid category
    action_invalid = {
        "action_type": "classify",
        "target_category": "invalid_category",
        "confidence": 0.95
    }
    reward_inv, info_inv = grader.grade_action(
        action_invalid, email, ground_truth, True, 1, 3
    )
    
    print(f"[+] Correct + High Confidence (95%):  {reward_c_c:+.2f}")
    print(f"[+] Correct + Low Confidence (60%):   {reward_c_t:+.2f}  (50% reward penalty)")
    print(f"[-] Wrong Classification:              {reward_w:+.2f}  (harsh penalty)")
    print(f"[-] Invalid Category:                  {reward_inv:+.2f}  (very harsh penalty)")
    print(f"\nReward Range: {reward_inv:.2f} to {reward_c_c:.2f}")


def demo_efficiency_strictness():
    print("\n" + "="*70)
    print("DEMO 2: Efficiency Penalties (Step-Based, Deterministic)")
    print("="*70)
    
    env = EmailTriageEnv()
    state = env.reset("hard")  # max_steps = 5
    ground_truth = state["ground_truth"]
    email = state["current_email"]
    
    grader = EmailTriageGrader()
    
    # Same correct action, different steps
    action_template = {
        "action_type": "classify",
        "target_category": ground_truth["category"],
        "confidence": 0.95
    }
    
    print("\nClassify correctly at different steps (hard difficulty, max_steps=5):")
    for step in range(1, 7):
        reward, info = grader.grade_action(
            action_template, email, ground_truth, True, step, 5
        )
        quality = info["metrics"]["quality"]
        print(f"  Step {step}: {reward:+.2f}  (quality: {quality})")
    
    print("\nKey insight: Penalties are DISCRETE per step (deterministic):") 
    print("  - Step 1-2: Bonus for speed")
    print("  - Step 3: Baseline")
    print("  - Step 4-5: Cumulative penalties")


def demo_priority_strictness():
    print("\n" + "="*70)
    print("DEMO 3: Priority Grading (Strict, No Partial Credit)")
    print("="*70)
    
    env = EmailTriageEnv()
    state = env.reset("medium")
    ground_truth = state["ground_truth"]
    email = state["current_email"]
    
    grader = EmailTriageGrader()
    correct_priority = ground_truth["priority"]
    
    print(f"\nCorrect priority: {correct_priority}")
    print("\nGrading prioritize action at different values:")
    
    for priority_guess in range(1, 6):
        action = {
            "action_type": "prioritize",
            "priority_level": priority_guess,
            "confidence": 0.85
        }
        reward, info = grader.grade_action(
            action, email, ground_truth, True, 2, 4
        )
        diff = abs(priority_guess - correct_priority)
        quality = info['metrics']['quality']
        print(f"  Priority {priority_guess}: {reward:+.2f}  (diff={diff}, quality={quality})")
    
    print("\nKey insight: Strict scoring - only exact gets full credit (1.0)")


def demo_reply_strictness():
    print("\n" + "="*70)
    print("DEMO 4: Reply Quality (Strict Length & Professionalism)")
    print("="*70)
    
    env = EmailTriageEnv()
    state = env.reset("medium")
    ground_truth = state["ground_truth"]
    email = state["current_email"]
    
    grader = EmailTriageGrader()
    
    if not ground_truth.get("should_reply"):
        print("Skipping - email doesn't require reply")
        return
    
    print("\nGrading reply quality:")
    
    # Too short
    reply_too_short = "Hi"  # 2 chars
    action_short = {
        "action_type": "reply",
        "reply_draft": reply_too_short,
        "confidence": 0.85
    }
    reward_short, info_short = grader.grade_action(
        action_short, email, ground_truth, True, 2, 4
    )
    print(f"[-] Too short (2 chars):          {reward_short:+.2f}")
    
    # Acceptable length
    reply_good = "Thank you for your message. I will review this and get back to you."  # 65 chars
    action_good = {
        "action_type": "reply",
        "reply_draft": reply_good,
        "confidence": 0.85
    }
    reward_good, info_good = grader.grade_action(
        action_good, email, ground_truth, True, 2, 4
    )
    print(f"[+] Good length (65 chars):       {reward_good:+.2f}")
    
    # Unprofessional
    reply_unprofessional = "OMG yeah ur totally right!!! HAHA this is awesome LOL"
    action_unprofessional = {
        "action_type": "reply",
        "reply_draft": reply_unprofessional,
        "confidence": 0.85
    }
    reward_unprofessional, info_unprofessional = grader.grade_action(
        action_unprofessional, email, ground_truth, True, 2, 4
    )
    print(f"[-] Unprofessional tone:         {reward_unprofessional:+.2f}")


def demo_determinism():
    print("\n" + "="*70)
    print("DEMO 5: Determinism Verification")
    print("="*70)
    
    env = EmailTriageEnv()
    state = env.reset("easy")
    ground_truth = state["ground_truth"]
    email = state["current_email"]
    
    grader = EmailTriageGrader()
    
    action = {
        "action_type": "classify",
        "target_category": ground_truth["category"],
        "confidence": 0.92
    }
    
    print("\nRunning same action 5 times (verify deterministic results):")
    rewards = []
    for i in range(5):
        reward, info = grader.grade_action(
            action, email, ground_truth, True, 1, 3
        )
        rewards.append(reward)
        print(f"  Run {i+1}: {reward:+.2f}")
    
    if len(set(rewards)) == 1:
        print(f"\n[OK] DETERMINISTIC: All runs produced {rewards[0]:+.2f}")
    else:
        print(f"\n[FAIL] NOT DETERMINISTIC: Got {set(rewards)}")


def main():
    print("\n" + "#"*70)
    print("# STRICTER & MORE DETERMINISTIC GRADER DEMONSTRATION")
    print("#"*70)
    
    demo_classification_strictness()
    demo_efficiency_strictness()
    demo_priority_strictness()
    demo_reply_strictness()
    demo_determinism()
    
    print("\n" + "#"*70)
    print("# KEY IMPROVEMENTS")
    print("#"*70)
    print("""
1. Classification: -1.0 for wrong (was -0.5) - 2x harsher
2. Priority: 0.0 for off-by-one (was 0.3) - strict exact match only
3. Reply: -1.0 for missing (was -0.3) - enforce substantive replies
4. Escalation: Requires reason (was optional)
5. Efficiency: Step-based discrete (was continuous ratio)
6. Confidence threshold: 70% minimum (was soft scaling)
7. Determinism: No fuzzy logic, pure rules-based
8. Reproducibility: Same input -> Same output, always
    """)


if __name__ == "__main__":
    sys.exit(main() or 0)
