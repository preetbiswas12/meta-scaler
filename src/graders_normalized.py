from typing import Dict, Any, List, Tuple, Optional


class EmailTriageGrader:
    """Deterministic grader for email triage with normalized bounds."""

    # Step weights per difficulty as dicts (sum = 1.0)
    STEP_WEIGHTS = {
        "easy": {
            "step_1": 0.33,
            "step_2": 0.33,
            "step_3": 0.34,
        },
        "medium": {
            "step_1": 0.25,
            "step_2": 0.25,
            "step_3": 0.25,
            "step_4": 0.25,
        },
        "hard": {
            "step_1": 0.20,
            "step_2": 0.20,
            "step_3": 0.20,
            "step_4": 0.20,
            "step_5": 0.20,
        },
    }

    # Quality multipliers (confidence-based scaling)
    # Maps confidence [0, 1] to quality multiplier [0.05, 1.0]
    QUALITY_MULTIPLIERS = {
        "low": 0.05,  # confidence <= 0.4
        "medium": 0.5,  # 0.4 < confidence <= 0.7
        "high": 1.0,  # confidence > 0.7
    }
    
    # Out-of-sequence penalty
    OUT_OF_SEQUENCE_PENALTY = -0.10

    @staticmethod
    def get_quality_multiplier(confidence: float) -> float:
        """Get quality multiplier based on confidence."""
        confidence = max(0.0, min(1.0, confidence))
        if confidence <= 0.4:
            return 0.05
        elif confidence <= 0.7:
            return 0.5
        else:
            return 1.0

    @staticmethod
    def compute_step_reward(
        difficulty: str,
        step_number: int,
        action_type: str,
        confidence: float,
    ) -> float:
        """
        Compute reward for a single step.

        Args:
            difficulty: "easy", "medium", or "hard"
            step_number: 1-indexed step number
            action_type: Type of action taken
            confidence: Model confidence [0.0, 1.0]

        Returns:
            Reward value in [0.0, 1.0]
        """
        # Validate inputs
        if difficulty not in EmailTriageGrader.STEP_WEIGHTS:
            difficulty = "easy"
        
        step_number = max(1, step_number)
        confidence = max(0.0, min(1.0, confidence))

        # Get base weight for this step (already normalized)
        weights_dict = EmailTriageGrader.STEP_WEIGHTS[difficulty]
        weights_list = list(weights_dict.values())
        
        if step_number - 1 >= len(weights_list):
            step_weight = weights_list[-1]
        else:
            step_weight = weights_list[step_number - 1]

        # Get quality multiplier
        quality_multiplier = EmailTriageGrader.get_quality_multiplier(confidence)

        # Compute reward: weight * quality
        reward = step_weight * quality_multiplier

        # Clamp to (0.001, 0.999) - strictly between 0 and 1, not inclusive
        # Validator requires scores strictly in range (0, 1), not [0, 1]
        reward = max(0.001, min(0.999, reward))

        return reward

    @staticmethod
    def compute_final_score(
        step_rewards: List[float],
        num_steps: Optional[int] = None,
    ) -> float:
        """
        Compute final episode score from step rewards.

        Args:
            step_rewards: List of per-step rewards
            num_steps: Total steps (optional, for compatibility)

        Returns:
            Final score in [0.0, 1.0]
        """
        if not step_rewards:
            return 0.5  # Default to middle of valid range if no rewards

        # Normalize step rewards to (0.001, 0.999)
        step_rewards = [max(0.001, min(0.999, r)) for r in step_rewards]

        # Sum rewards (may exceed 1.0)
        total_reward = sum(step_rewards)

        # Apply final normalization: cap at 0.999 (strictly less than 1.0)
        final_score = min(0.999, max(0.001, total_reward))

        return final_score

    @staticmethod
    def validate_bounds(
        reward: float,
        score: float,
    ) -> Dict[str, Any]:
        """
        Validate that rewards and scores are properly bounded.
        Validator requires scores STRICTLY between 0 and 1 (not inclusive).

        Args:
            reward: Step reward value
            score: Episode score value

        Returns:
            Validation result dict
        """
        # Scores must be strictly between 0 and 1 (exclusive on both ends)
        is_reward_valid = 0.0 < reward < 1.0
        is_score_valid = 0.0 < score < 1.0

        return {
            "reward_valid": is_reward_valid,
            "score_valid": is_score_valid,
            "all_valid": is_reward_valid and is_score_valid,
            "reward_range": f"({reward:.4f})",
            "score_range": f"({score:.4f})",
        }

    def grade_action(
        self,
        action: Any,
        email: Dict[str, Any],
        ground_truth: Dict[str, Any],
        is_correct_sequence: bool = True,
        step_number: int = 1,
        total_steps: int = 3,
        difficulty: str = "easy",
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Grade an action for email triage with ambiguity awareness.

        Handles:
        - Standard emails: Reward correct classification with confidence
        - Ambiguous emails: Reward conservative/cautious approaches
        - Multi-action chains: Reward investigation before escalation

        Args:
            action: ActionSchema object with action_type and confidence
            email: Email dict
            ground_truth: Ground truth dict with expected category, priority, etc.
            is_correct_sequence: Whether action is in correct sequence
            step_number: Current step number
            total_steps: Total steps in episode
            difficulty: Task difficulty

        Returns:
            (reward, info) tuple
        """
        # Extract fields with defaults
        action_type = getattr(action, 'action_type', 'unknown')
        confidence = getattr(action, 'confidence', 0.5)
        target_category = getattr(action, 'target_category', '')
        
        # Normalize confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # Get ambiguity level (default to "low" if not specified)
        ambiguity = ground_truth.get("ambiguity", "low")
        
        # Check if action is correct
        is_correct = False
        quality = "low_confidence"
        ambiguity_bonus = 0.0  # Bonus for handling ambiguity well
        
        if action_type == "classify":
            # Classification should match ground truth category
            is_correct = target_category == ground_truth.get("category", "")
            
            # For highly ambiguous emails, reward appropriate uncertainty
            if ambiguity == "high":
                if confidence <= 0.5:
                    # Appropriately cautious on ambiguous classification
                    ambiguity_bonus = 0.05
                elif confidence > 0.8 and not is_correct:
                    # Overconfident on ambiguous email - penalty already applied
                    ambiguity_bonus = -0.05
            
            if confidence > 0.8:
                quality = "perfect" if is_correct else "incorrect"
            elif confidence > 0.6:
                quality = "correct" if is_correct else "low_confidence"
            else:
                quality = "appropriately_cautious" if ambiguity in ["medium", "high"] else "low_confidence"
        else:
            # Other actions (prioritize, escalate, reply, investigate)
            is_correct = is_correct_sequence
            
            # Reward investigation/escalation on ambiguous emails
            if ambiguity in ["medium", "high"]:
                if action_type in ["investigate", "escalate"]:
                    ambiguity_bonus = 0.05  # Bonus for conservative approach
            
            if confidence > 0.8:
                quality = "perfect"
            elif confidence > 0.6:
                quality = "correct"
            else:
                quality = "low_confidence"
        
        # Compute reward
        if not is_correct_sequence:
            reward = self.OUT_OF_SEQUENCE_PENALTY  # Penalty for wrong sequence
        else:
            # Get step weight from dict
            weights_dict = self.STEP_WEIGHTS.get(difficulty, self.STEP_WEIGHTS["easy"])
            weights_list = list(weights_dict.values())
            
            if step_number - 1 >= len(weights_list):
                step_weight = weights_list[-1]
            else:
                step_weight = weights_list[step_number - 1]
            
            # Get quality multiplier based on confidence
            quality_multiplier = self.get_quality_multiplier(confidence)
            
            # Compute reward
            reward = step_weight * quality_multiplier
            
            # Apply ambiguity bonus
            reward += ambiguity_bonus
        
        # Ensure bounds
        reward = max(0.0, min(1.0, reward))
        
        return reward, {
            "metrics": {
                "quality": quality,
                "is_correct": is_correct,
                "confidence": confidence,
                "ambiguity": ambiguity,
                "ambiguity_bonus": ambiguity_bonus,
            },
            "step": step_number,
            "total_steps": total_steps,
        }
