"""Deterministic grader for email triage actions."""
import re
from typing import Tuple, Dict, Any


class EmailTriageGrader:
    """Strict deterministic grader (no randomness, fully reproducible)."""

    VALID_CATEGORIES = {
        "sales_inquiry", "newsletter", "transactional", "phishing",
        "work_technical", "hr_admin", "advertising_spam", "escalation_required", "internal_strategic",
    }

    MIN_CONFIDENCE_FOR_ACTION = 0.7
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MIN_REPLY_LENGTH = 30
    MIN_ESCALATION_REASON_LENGTH = 20

    # Reward structure
    CLASSIFICATION_CORRECT = 1.0
    CLASSIFICATION_WRONG = -1.0
    CLASSIFICATION_UNKNOWN_ACTION = -2.0

    PRIORITY_EXACT = 1.0
    PRIORITY_OFF_BY_ONE = 0.0
    PRIORITY_OFF_BY_TWO_PLUS = -0.5

    REPLY_PERFECT_LENGTH = (50, 500)
    REPLY_ACCEPTABLE_LENGTH = (30, 800)

    ESCALATION_CORRECT_WITH_REASON = 0.8
    ESCALATION_CORRECT_NO_REASON = -0.3
    ESCALATION_UNNECESSARY = -0.8

    ARCHIVE_CORRECT = 0.3
    ARCHIVE_WRONG = -0.5

    # Efficiency bonuses/penalties
    EFFICIENCY_STEP_1_BONUS = 0.3
    EFFICIENCY_STEP_2_BONUS = 0.1
    EFFICIENCY_STEP_3_BASELINE = 0.0
    EFFICIENCY_STEP_4_PENALTY = -0.2
    EFFICIENCY_STEP_5_PENALTY = -0.4
    EFFICIENCY_OVER_MAX = -0.5

    def grade_action(
        self,
        action: Dict[str, Any],
        email: Any,
        ground_truth: Dict[str, Any],
        step_count: int,
        max_steps: int
    ) -> Tuple[float, Dict[str, Any]]:
        """Return (reward, grading_info) for given action."""
        reward = 0.0
        metrics = {}

        action_type = action.action_type if hasattr(action, 'action_type') else action.get('action_type', 'unknown')
        valid_actions = {"classify", "prioritize", "reply", "escalate", "archive"}
        if action_type not in valid_actions:
            reward = self.CLASSIFICATION_UNKNOWN_ACTION
            metrics = {"error": f"Unknown action type: {action_type}", "valid_actions": list(valid_actions)}
            info = {
                "metrics": metrics,
                "reward": reward,
                "action_type": action_type,
                "ground_truth": ground_truth,
                "deterministic": True
            }
            return reward, info
        
        # Grade based on action type
        if action_type == "classify":
            reward, metrics = self._grade_classification(action, email, ground_truth, step_count, max_steps)
        elif action_type == "prioritize":
            reward, metrics = self._grade_prioritization(action, ground_truth, step_count)
        elif action_type == "reply":
            reward, metrics = self._grade_reply(action, email, ground_truth, step_count)
        elif action_type == "escalate":
            reward, metrics = self._grade_escalation(action, ground_truth, step_count)
        elif action_type == "archive":
            reward, metrics = self._grade_archive(action, email, ground_truth, step_count)
        
        # Apply strict efficiency penalty (step-based, not ratio-based)
        efficiency_penalty = self._calculate_efficiency_penalty_strict(step_count, max_steps)
        reward += efficiency_penalty
        
        info = {
            "metrics": metrics,
            "reward": reward,
            "action_type": action_type,
            "ground_truth": ground_truth,
            "deterministic": True,
            "efficiency_penalty": efficiency_penalty
        }
        
        return reward, info

    def _grade_classification(
        self,
        action: Dict[str, Any],
        email: Any,
        ground_truth: Dict[str, Any],
        step_count: int,
        max_steps: int
    ) -> Tuple[float, Dict[str, Any]]:
        """Grade classification action with strict deterministic rules."""
        target_category = action.target_category if hasattr(action, 'target_category') else action.get('target_category', '')
        confidence = action.confidence if hasattr(action, 'confidence') else action.get('confidence', 0.0)
        
        correct_category = ground_truth.get("category", "")
        is_correct = target_category == correct_category
        
        # Validate category is in valid set
        if target_category not in self.VALID_CATEGORIES:
            reward = -1.5  # Very harsh for invalid category
            metrics = {
                "correct_category": False,
                "target_category": target_category,
                "expected_category": correct_category,
                "confidence": confidence,
                "reason": "Invalid category",
                "valid_categories": list(self.VALID_CATEGORIES)
            }
            return reward, metrics
        
        # Check confidence threshold - must be >= MIN_CONFIDENCE for any credit
        if confidence < self.MIN_CONFIDENCE_FOR_ACTION:
            # Too low confidence - gets harsh penalty even if correct
            base_score = self.CLASSIFICATION_CORRECT * 0.5 if is_correct else self.CLASSIFICATION_WRONG * 1.2
            reward = base_score
            metrics = {
                "correct_category": is_correct,
                "target_category": target_category,
                "expected_category": correct_category,
                "confidence": confidence,
                "reason": f"Confidence too low (required >= {self.MIN_CONFIDENCE_FOR_ACTION})",
                "confidence_penalty_applied": True
            }
            return reward, metrics
        
        # Correct classification
        if is_correct:
            # Classification is part of multi-step chain, not full solution
            # Base reward: 0.3 (30% of total solution)
            reward = 0.3
            
            # Bonus for high confidence
            if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                reward += 0.1
            
            reason = "Classification (step 1)"
        else:
            # Wrong classification - harsh penalty
            reward = -0.7
            reason = "Wrong category"
        
        metrics = {
            "correct_category": is_correct,
            "target_category": target_category,
            "expected_category": correct_category,
            "confidence": confidence,
            "step": step_count,
            "reason": reason
        }
        
        return reward, metrics

    def _grade_prioritization(
        self,
        action: Dict[str, Any],
        ground_truth: Dict[str, Any],
        step_count: int
    ) -> Tuple[float, Dict[str, Any]]:
        """Grade priority assignment action with strict deterministic rules."""
        assigned_priority = action.priority_level if hasattr(action, 'priority_level') else action.get('priority_level', 0)
        confidence = action.confidence if hasattr(action, 'confidence') else action.get('confidence', 0.0)
        correct_priority = ground_truth.get("priority", 0)
        
        # Validate priority is in range [1, 5]
        if not isinstance(assigned_priority, int) or assigned_priority < 1 or assigned_priority > 5:
            reward = -1.0  # Invalid priority
            metrics = {
                "priority_correct": False,
                "assigned_priority": assigned_priority,
                "expected_priority": correct_priority,
                "reason": "Invalid priority (must be 1-5)"
            }
            return reward, metrics
        
        # Calculate priority difference
        priority_diff = abs(assigned_priority - correct_priority)
        
        # Strict deterministic scoring - no partial credit
        if priority_diff == 0:
            # Exact match - excellent
            reward = self.PRIORITY_EXACT
            if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                reward += 0.1
            reason = "Exact priority"
        elif priority_diff == 1:
            # Off by one - NO CREDIT (strict)
            reward = self.PRIORITY_OFF_BY_ONE
            reason = "Off by one"
        else:
            # Off by two or more - harsh penalty
            reward = self.PRIORITY_OFF_BY_TWO_PLUS * priority_diff
            reason = f"Off by {priority_diff}"
        
        # Check confidence
        if confidence < self.MIN_CONFIDENCE_FOR_ACTION:
            reward *= 0.5  # Halve reward if low confidence
        
        metrics = {
            "priority_correct": priority_diff == 0,
            "assigned_priority": assigned_priority,
            "expected_priority": correct_priority,
            "priority_diff": priority_diff,
            "confidence": confidence,
            "reason": reason
        }
        
        return reward, metrics

    def _grade_reply(
        self,
        action: Dict[str, Any],
        email: Any,
        ground_truth: Dict[str, Any],
        step_count: int
    ) -> Tuple[float, Dict[str, Any]]:
        """Grade reply drafting action with strict deterministic rules."""
        reply_draft = action.reply_draft if hasattr(action, 'reply_draft') else action.get('reply_draft', '')
        confidence = action.confidence if hasattr(action, 'confidence') else action.get('confidence', 0.0)
        should_reply = ground_truth.get("should_reply", False)
        
        # Case 1: Should NOT reply
        if not should_reply:
            if reply_draft and len(reply_draft.strip()) > 0:
                # Replying when shouldn't - HARSH penalty
                reward = -1.2
                reason = "Replied when no reply needed"
            else:
                # Correctly didn't reply - modest reward
                reward = 0.2
                reason = "Correctly avoided replying"
            
            metrics = {
                "should_reply": should_reply,
                "reply_draft_length": len(reply_draft) if reply_draft else 0,
                "reason": reason
            }
            return reward, metrics
        
        # Case 2: Should reply but didn't
        if not reply_draft or len(reply_draft.strip()) < self.MIN_REPLY_LENGTH:
            # Missing reply or too short - HARSH penalty
            reward = -1.0
            reason = f"Reply too short or missing (need >= {self.MIN_REPLY_LENGTH} chars)"
            
            metrics = {
                "should_reply": should_reply,
                "reply_draft_length": len(reply_draft) if reply_draft else 0,
                "min_required": self.MIN_REPLY_LENGTH,
                "reason": reason
            }
            return reward, metrics
        
        # Case 3: Has reply - grade quality strictly
        quality_score = self._evaluate_reply_quality_strict(reply_draft, email, ground_truth)
        
        # Base score plus quality adjustment
        reward = 0.4 + (quality_score * 0.6)
        
        # Low confidence penalty
        if confidence < self.MIN_CONFIDENCE_FOR_ACTION:
            reward *= 0.6
        
        metrics = {
            "should_reply": should_reply,
            "reply_draft_length": len(reply_draft),
            "quality_score": quality_score,
            "confidence": confidence,
            "professional": self._check_professionalism_strict(reply_draft),
            "reason": f"Reply quality: {quality_score:.1f}"
        }
        
        return reward, metrics

    def _grade_escalation(
        self,
        action: Dict[str, Any],
        ground_truth: Dict[str, Any],
        step_count: int
    ) -> Tuple[float, Dict[str, Any]]:
        """Grade escalation action with strict deterministic rules."""
        category = ground_truth.get("category", "")
        priority = ground_truth.get("priority", 0)
        needs_escalation = category in ["escalation_required"] or priority >= 5
        
        escalation_reason = action.escalation_reason if hasattr(action, 'escalation_reason') else action.get('escalation_reason', '')
        confidence = action.confidence if hasattr(action, 'confidence') else action.get('confidence', 0.0)
        
        # Validate reason exists and is substantial
        has_valid_reason = escalation_reason and len(escalation_reason.strip()) >= self.MIN_ESCALATION_REASON_LENGTH
        
        if needs_escalation:
            # Should escalate
            if not escalation_reason or len(escalation_reason.strip()) == 0:
                # Escalating without reason - PENALTY
                reward = -0.5
                reason = "Escalation requires a reason"
            elif not has_valid_reason:
                # Reason too short
                reward = -0.2
                reason = f"Reason too short (need >= {self.MIN_ESCALATION_REASON_LENGTH} chars)"
            else:
                # Correct escalation with proper reason
                reward = self.ESCALATION_CORRECT_WITH_REASON
                if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                    reward += 0.1
                reason = "Correct escalation with reason"
        else:
            # Should NOT escalate but did
            reward = self.ESCALATION_UNNECESSARY
            if escalation_reason and len(escalation_reason.strip()) > 0:
                # Made false claim with explanation - still wrong
                reward -= 0.2
            reason = "Unnecessary escalation"
        
        # Apply confidence penalty if low
        if confidence < self.MIN_CONFIDENCE_FOR_ACTION:
            reward *= 0.7
        
        metrics = {
            "escalation_needed": needs_escalation,
            "escalation_done": bool(escalation_reason),
            "reason_provided": has_valid_reason,
            "reason_length": len(escalation_reason.strip()) if escalation_reason else 0,
            "confidence": confidence,
            "explanation": reason
        }
        
        return reward, metrics

    def _grade_archive(
        self,
        action: Dict[str, Any],
        email: Any,
        ground_truth: Dict[str, Any],
        step_count: int
    ) -> Tuple[float, Dict[str, Any]]:
        """Grade archive action with strict deterministic rules."""
        should_reply = ground_truth.get("should_reply", False)
        category = ground_truth.get("category", "")
        confidence = action.confidence if hasattr(action, 'confidence') else action.get('confidence', 0.0)
        
        # Explicitly check what can be archived
        needs_action = should_reply or category in ["escalation_required", "work_technical", "phishing"]
        can_archive = not needs_action
        
        if can_archive:
            # Correct archive decision
            reward = self.ARCHIVE_CORRECT
            if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                reward += 0.1
            reason = "Appropriate archive"
        else:
            # Wrong archive decision - HARSH penalty
            reward = self.ARCHIVE_WRONG
            reason = "Archiving item that needs action"
        
        metrics = {
            "archive_appropriate": can_archive,
            "needs_action": needs_action,
            "category": category,
            "should_reply": should_reply,
            "confidence": confidence,
            "reason": reason
        }
        
        return reward, metrics

    def _evaluate_reply_quality_strict(
        self,
        reply_draft: str,
        email: Any,
        ground_truth: Dict[str, Any]
    ) -> float:
        """Evaluate reply quality with strict deterministic rules."""
        if not reply_draft or len(reply_draft) < self.MIN_REPLY_LENGTH:
            return 0.0  # No credit for insufficient reply
        
        score = 0.0
        
        # Length scoring (stricter range)
        reply_len = len(reply_draft.strip())
        if self.REPLY_PERFECT_LENGTH[0] <= reply_len <= self.REPLY_PERFECT_LENGTH[1]:
            score += 0.4  # Perfect length range
        elif self.REPLY_ACCEPTABLE_LENGTH[0] <= reply_len <= self.REPLY_ACCEPTABLE_LENGTH[1]:
            score += 0.2  # Acceptable but not ideal
        else:
            score -= 0.2  # Too long or too short (still within acceptable but penalized)
        
        # Professional tone check (strict)
        if self._check_professionalism_strict(reply_draft):
            score += 0.3
        else:
            score -= 0.3  # Unprofessional gets penalty
        
        # Keyword matching (must cover most keywords to get credit)
        keywords = ground_truth.get("reply_keywords", [])
        if keywords:
            matching_keywords = sum(1 for kw in keywords if kw.lower() in reply_draft.lower())
            keyword_ratio = matching_keywords / len(keywords)
            
            if keyword_ratio >= 0.8:  # 80% or more keywords
                score += 0.3
            elif keyword_ratio >= 0.5:  # 50% or more keywords
                score += 0.1
            else:  # Less than 50% - penalty
                score -= 0.2
        
        # Ensure score is in [0, 1]
        return max(0.0, min(1.0, score))

    def _check_professionalism_strict(self, text: str) -> bool:
        """Check if text is professional with strict rules."""
        if not text or len(text) < self.MIN_REPLY_LENGTH:
            return False  # Too short to be professional
        
        # Unprofessional patterns - STRICT checking
        unprofessional_patterns = [
            r'!!!+',           # Excessive exclamation marks
            r'\?\?+',          # Excessive question marks
            r'[A-Z]{5,}',      # SHOUTING (5+ caps in a row)
            r'lol|haha|omg|wtf|brb|fyi|btw',  # Casual slang
            r'u|ur|thru',      # Text speak
            r'@+|#+|&+',       # Excessive punctuation
        ]
        
        text_lower = text.lower()
        for pattern in unprofessional_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Professional should start with greeting or formal opening
        professional_openings = ['hi', 'hello', 'dear', 'thank', 'i', 'we', 'regards', 'sincerely']
        first_word = text_lower.split()[0] if text.split() else ''
        has_professional_start = any(first_word.startswith(opening) for opening in professional_openings)
        
        return has_professional_start

    def _check_professionalism(self, text: str) -> bool:
        """Check if text is professional (deprecated - use strict version)."""
        return self._check_professionalism_strict(text)

    def _calculate_efficiency_penalty_strict(self, step_count: int, max_steps: int) -> float:
        """
        Strict step-based efficiency penalty (no ratio calculation).
        Deterministic rules based on exact step number.
        """
        if step_count == 1:
            return self.EFFICIENCY_STEP_1_BONUS
        elif step_count == 2:
            return self.EFFICIENCY_STEP_2_BONUS
        elif step_count == 3:
            return self.EFFICIENCY_STEP_3_BASELINE
        elif step_count == 4:
            return self.EFFICIENCY_STEP_4_PENALTY
        elif step_count == 5:
            return self.EFFICIENCY_STEP_5_PENALTY
        else:  # step_count > max_steps or other invalid
            return self.EFFICIENCY_OVER_MAX

    def _calculate_efficiency_penalty(self, step_count: int, max_steps: int) -> float:
        """Penalty for inefficient (slow) decision-making (deprecated - use strict version)."""
        return self._calculate_efficiency_penalty_strict(step_count, max_steps)


class ActionSequenceAnalyzer:
    """Analyzes sequences of actions for optimality."""
    
    def analyze_sequence(self, actions: list) -> Dict[str, Any]:
        """Analyze a sequence of actions."""
        if not actions:
            return {"error": "No actions"}
        
        has_classification = any(a.get("action_type") == "classify" for a in actions)
        classification_position = None
        for i, a in enumerate(actions):
            if a.get("action_type") == "classify":
                classification_position = i + 1
                break
        
        return {
            "total_actions": len(actions),
            "has_classification": has_classification,
            "classification_step": classification_position,
            "is_efficient": classification_position and classification_position <= 2
        }


if __name__ == "__main__":
    from src.environment import EmailTriageEnv, ActionSchema
    
    env = EmailTriageEnv()
    state = env.reset("easy")
    
    action = ActionSchema(
        action_type="classify",
        target_category="sales_inquiry",
        priority_level=2,
        confidence=0.95
    )
    
    grader = EmailTriageGrader()
    reward, info = grader.grade_action(action, state["current_email"], state["ground_truth"], 1, 3)
    print(f"Reward: {reward}")
    print(f"Info: {info}")
