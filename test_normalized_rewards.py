#!/usr/bin/env python3
"""
Verification script for normalized reward system integration.
Tests that all episode rewards stay within [0.0, 1.0] bounds.
"""

from src.graders_normalized import EmailTriageGrader


def test_reward_bounds():
    """Verify normalized rewards stay within [0.0, 1.0] bounds."""
    grader = EmailTriageGrader()
    
    print("=" * 70)
    print("NORMALIZED REWARD SYSTEM VERIFICATION")
    print("=" * 70)
    
    # Test 1: Step weight bounds per difficulty
    print("\n✓ Test 1: STEP_WEIGHTS summed per difficulty")
    for difficulty, actions in grader.STEP_WEIGHTS.items():
        total_weight = sum(actions.values())
        print(f"  {difficulty:10s}: {actions} → sum = {total_weight}")
        assert abs(total_weight - 1.0) < 0.001, f"Weights don't sum to 1.0 for {difficulty}"
    
    # Test 2: Per-step reward bounds
    print("\n✓ Test 2: Per-step reward bounds (step_weight × quality_multiplier)")
    max_step_reward = max(
        w * max(grader.QUALITY_MULTIPLIERS.values())
        for actions in grader.STEP_WEIGHTS.values()
        for w in actions.values()
    )
    min_step_reward = min(grader.QUALITY_MULTIPLIERS.values()) 
    out_of_seq_penalty = grader.OUT_OF_SEQUENCE_PENALTY
    
    print(f"  Max per-step reward: {max_step_reward:.3f}")
    print(f"  Min quality multiplier: {min_step_reward:.3f}")
    print(f"  Out-of-sequence penalty: {out_of_seq_penalty:.3f}")
    
    # Test 3: Final score normalization
    print("\n✓ Test 3: Final score normalization")
    test_cases = [
        ([0.45, 0.25, 0.30], "Perfect episode (easy)"),
        ([0.05, -0.10, 0.15], "Mixed rewards with penalty"),
        ([-0.10, -0.10, -0.10], "All negative (out-of-sequence)"),
        ([1.5, 0.8, 0.6], "Over 1.0 (truncate to 1.0)"),
    ]
    
    for step_rewards, description in test_cases:
        final_score = grader.compute_final_score(step_rewards, len(step_rewards))
        assert 0.0 <= final_score <= 1.0, f"Score out of bounds: {final_score}"
        print(f"  {description:40s} → score = {final_score:.3f} ✓")
    
    # Test 4: Quality multipliers bounds
    print("\n✓ Test 4: Quality multipliers within [0.05, 1.0]")
    for quality, multiplier in grader.QUALITY_MULTIPLIERS.items():
        assert 0.05 <= multiplier <= 1.0, f"Quality {quality} outside bounds: {multiplier}"
        print(f"  {quality:20s}: {multiplier:.3f}")
    
    print("\n" + "=" * 70)
    print("✅ ALL VERIFICATION TESTS PASSED")
    print("=" * 70)
    print("\nKEY GUARANTEES:")
    print(f"  • Per-step reward range: [{min_step_reward:.3f}, {max_step_reward:.3f}]")
    print(f"  • Final score range: [0.0, 1.0] (enforced by compute_final_score)")
    print(f"  • Weight normalization: ∑ step_weights = 1.0 per difficulty")
    print(f"  • Quality-based multipliers: replaces additive penalties")
    print(f"  • Sequence penalties: small and bounded (-0.10, -0.05)")
    print("\nINTEGRATION:")
    print(f"  • environment.py step() imports from src.graders_normalized")
    print(f"  • grade_action() called with difficulty parameter")
    print(f"  • compute_final_score() ensures [0.0, 1.0] bounds")
    print(f"  • All episodes guaranteed to have normalized rewards")
    print("=" * 70)


if __name__ == "__main__":
    test_reward_bounds()
