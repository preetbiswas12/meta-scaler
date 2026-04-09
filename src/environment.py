"""
Email Triage OpenEnv Environment - Multi-Step Implementation
OpenEnv-compliant multi-step reasoning with normalized grading.
"""
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from .graders_normalized import EmailTriageGrader, clamp_score, EPSILON

logger = logging.getLogger(__name__)


class EmailSchema(BaseModel):
    """Email message schema."""
    email_id: str
    sender: str
    subject: str
    body: str
    timestamp: str
    is_reply_to: str = ""
    is_spam: bool = False
    urgency_indicators: List[str] = Field(default_factory=list)


class ActionSchema(BaseModel):
    """Action schema for email triage."""
    action_type: str
    target_category: str = ""
    priority_level: int = 0
    reply_draft: str = ""
    escalation_reason: str = ""
    confidence: float = 0.5


class StateSchema(BaseModel):
    """Environment state schema."""
    task_id: str
    episode_id: str
    difficulty: str
    step: int = 0
    max_steps: int = 5
    current_email: Dict[str, Any]
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    score: float = Field(default=0.5, description="Must be in (0, 1)")  # Default to 0.5 (middle - epsilon of bound)
    done: bool = False
    reward: float = Field(default=0.5, description="Must be in (0, 1)")  # Default to 0.5 (middle - epsilon of bound)
    ground_truth: Dict[str, Any] = Field(default_factory=dict)
    step_rewards: List[float] = Field(default_factory=list)


class EmailTriageEnv:
    """Email triage environment with multi-step reasoning."""

    # Map actual task IDs to internal difficulty levels
    TASK_ID_TO_DIFFICULTY = {
        "basic_email_classification": "easy",
        "phishing_threat_detection": "medium",
        "critical_escalation_handling": "hard",
        # Legacy aliases for backward compatibility
        "easy": "easy",
        "medium": "medium",
        "hard": "hard",
    }

    def __init__(self):
        """Initialize environment."""
        self.episode_id: Optional[str] = None
        self.task_id: Optional[str] = None
        self.difficulty: Optional[str] = None
        self.current_state: Optional[StateSchema] = None
        self.difficulty_config = {
            "easy": {"max_steps": 3, "base_reward_per_step": 0.30},
            "medium": {"max_steps": 4, "base_reward_per_step": 0.25},
            "hard": {"max_steps": 5, "base_reward_per_step": 0.20},
        }
        self.email_bank = self._create_email_bank()

    def _create_email_bank(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create a bank of sample emails for different difficulties.
        
        Includes messy real-world variants with:
        - Ambiguous intent (unclear classification)
        - Multiple actions (chain of steps required)
        - Conflicting signals (priority vs urgency mismatch)
        """
        return {
            "easy": [
                # Primary: straightforward newsletter
                {
                    "email_id": "email_001",
                    "sender": "newsletter@company.com",
                    "subject": "Weekly newsletter",
                    "body": "Here's this week's updates...",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": [],
                },
                # Messy variant 1: Ambiguous - could be newsletter or promo
                {
                    "email_id": "email_001_messy_1",
                    "sender": "updates@partner.io",
                    "subject": "Check out what's new",
                    "body": "We have new features! Learn more at our site. Special offer inside.",
                    "timestamp": "2024-01-16T09:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": [],
                },
                # Messy variant 2: Conflicting signals - spam-like but low urgency
                {
                    "email_id": "email_001_messy_2",
                    "sender": "info@newsletters.org",
                    "subject": "!!!IMPORTANT UPDATES!!!",
                    "body": "Check our latest posts. You might miss something. Click here now!!!",
                    "timestamp": "2024-01-16T10:30:00Z",
                    "is_spam": False,
                    "urgency_indicators": [],
                },
            ],
            "medium": [
                # Primary: clear bug report with urgency
                {
                    "email_id": "email_002",
                    "sender": "customer@example.com",
                    "subject": "Product bug report",
                    "body": "I found a bug in your software when trying to process large files. The system crashes and loses data.",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["urgent"],
                },
                # Messy variant 1: Ambiguous - feature request or complaint?
                {
                    "email_id": "email_002_messy_1",
                    "sender": "john.doe@corporate.com",
                    "subject": "Question about the system",
                    "body": "Hi, when I use the report feature with my 500K records, it seems slow. Is this normal? Other tools do it faster. Wondering if there's a way to optimize?",
                    "timestamp": "2024-01-15T15:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["performance_issue"],
                },
                # Messy variant 2: Conflicting signals - unclear sender importance
                {
                    "email_id": "email_002_messy_2",
                    "sender": "support-bot+urgent@vendor.com",
                    "subject": "URGENT: Review needed on invoice",
                    "body": "We need someone from accounting to review this. It got marked urgent by mistake but we need it ASAP anyway. Invoice #12345",
                    "timestamp": "2024-01-15T15:45:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["urgent"],
                },
                # Messy variant 3: Multiple actions needed - classify + escalate + reply
                {
                    "email_id": "email_002_messy_3",
                    "sender": "unknown@hotmail.com",
                    "subject": "Something happened with my payment",
                    "body": "I was charged twice. Please fix this. I have 3 children to feed and cannot afford this mistake.",
                    "timestamp": "2024-01-15T16:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["financial", "escalation_needed"],
                },
            ],
            "hard": [
                # Primary: clear critical incident
                {
                    "email_id": "email_003",
                    "sender": "ceo@customer.com",
                    "subject": "CRITICAL: System down, data loss reported",
                    "body": "Our entire system is down and we've lost critical customer data. This is a critical emergency affecting 100+ clients.",
                    "timestamp": "2024-01-15T16:45:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["critical", "urgent", "data_loss"],
                },
                # Messy variant 1: Ambiguous critical - is it really critical?
                {
                    "email_id": "email_003_messy_1",
                    "sender": "manager@bigcorp.com",
                    "subject": "Production alert - need immediate attention",
                    "body": "System is showing warnings. Database query times increased 10%. Response times up from 100ms to 150ms. Should we be concerned? Tests still passing.",
                    "timestamp": "2024-01-16T07:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["critical", "production"],
                },
                # Messy variant 2: Multiple conflicting signals
                {
                    "email_id": "email_003_messy_2",
                    "sender": "team@internal.company",
                    "subject": "FW: FW: URGENT - Security breach mentioned",
                    "body": "Subject was marked urgent. Forwarded to you. In original: someone said they saw suspicious activity. Not confirmed yet. Might be false alarm.",
                    "timestamp": "2024-01-16T08:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["critical", "urgent"],
                },
                # Messy variant 3: Chain-action required - classify + investigate + escalate + reply
                {
                    "email_id": "email_003_messy_3",
                    "sender": "legal@external-firm.com",
                    "subject": "RE: Notification of Potential Compliance Violation",
                    "body": "We believe we may have discovered a data handling issue in your processing. Regulatory timeline is 72 hours. Our team needs clarification on your data retention policy. CEO and board should be informed.",
                    "timestamp": "2024-01-16T09:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["critical", "urgent", "legal"],
                },
            ],
        }

    def reset(self, task_id: str = "easy") -> Dict[str, Any]:
        """Reset environment for a new episode."""
        import random
        
        # Map task_id to difficulty level
        difficulty = self.TASK_ID_TO_DIFFICULTY.get(task_id, "easy")
        
        # Validate mapped difficulty
        if difficulty not in self.difficulty_config:
            raise ValueError(f"Invalid task_id '{task_id}' maps to unknown difficulty '{difficulty}'. Must be one of: {list(self.difficulty_config.keys())}")

        self.task_id = task_id
        self.difficulty = difficulty
        self.episode_id = str(uuid.uuid4())
        
        config = self.difficulty_config[difficulty]
        email_list = self.email_bank.get(difficulty, self.email_bank["easy"])
        # Select random email from the list for variety
        current_email = random.choice(email_list) if email_list else {}

        # Initialize scores - must clamp to (EPSILON, 1-EPSILON)
        initial_score = clamp_score(0.5, f"initial_score[{difficulty}]")
        initial_reward = clamp_score(0.5, f"initial_reward[{difficulty}]")

        self.current_state = StateSchema(
            task_id=task_id,
            episode_id=self.episode_id,
            difficulty=difficulty,
            step=0,
            max_steps=config["max_steps"],
            current_email=current_email,
            actions_taken=[],
            score=initial_score,  # Explicitly clamped
            done=False,
            reward=initial_reward,  # Explicitly clamped
            step_rewards=[],
            ground_truth=self._get_ground_truth(current_email, difficulty),
        )

        return self._get_state_dict()

    def _get_ground_truth(self, email: Dict[str, Any], task_id: str = "easy") -> Dict[str, Any]:
        """Get ground truth actions for a task based on email_id.
        
        Maps specific email IDs to their expected categories, priorities, and action sequences.
        Handles both primary and messy variants with ambiguous/conflicting signals.
        """
        email_id = email.get("email_id", "")
        
        # Map email_id to ground truth
        email_ground_truths = {
            # EASY emails
            "email_001": {
                "category": "newsletter",
                "priority": 1,
                "should_reply": False,
                "actions": ["classify", "prioritize", "archive"],
                "description": "Non-urgent newsletter that should be archived",
                "ambiguity": "low",
            },
            "email_001_messy_1": {
                "category": "marketing",
                "priority": 1,
                "should_reply": False,
                "actions": ["classify", "prioritize", "archive"],
                "description": "Marketing/promotional email - low priority",
                "ambiguity": "medium",  # Unclear if newsletter or promo
            },
            "email_001_messy_2": {
                "category": "newsletter",
                "priority": 1,
                "should_reply": False,
                "actions": ["classify", "prioritize", "archive"],
                "description": "Newsletter with spam-like formatting but legitimate - requires nuanced handling",
                "ambiguity": "high",  # Looks like spam but is newsletter
            },
            
            # MEDIUM emails
            "email_002": {
                "category": "bug_report",
                "priority": 4,
                "should_reply": True,
                "actions": ["classify", "prioritize", "reply", "archive"],
                "description": "Critical bug report with data loss - requires investigation and escalation",
                "ambiguity": "low",
            },
            "email_002_messy_1": {
                "category": "performance_issue",
                "priority": 3,
                "should_reply": True,
                "actions": ["classify", "prioritize", "reply"],
                "description": "Performance complaint - could be feature request or support issue",
                "ambiguity": "high",  # Unclear: feature request? complaint? actual issue?
            },
            "email_002_messy_2": {
                "category": "finance_request",
                "priority": 3,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "reply"],
                "description": "Invoice review with conflicting urgency signals - needs accounting escalation",
                "ambiguity": "medium",  # Marked urgent but sender says it was by mistake
            },
            "email_002_messy_3": {
                "category": "financial_escalation",
                "priority": 4,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "reply", "archive"],
                "description": "Customer payment issue with escalation indicators - requires empathetic response and escalation",
                "ambiguity": "medium",  # Multiple action chain needed
            },
            
            # HARD emails
            "email_003": {
                "category": "critical_incident",
                "priority": 5,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "reply", "archive"],
                "description": "Critical data loss incident - requires immediate escalation to senior management",
                "ambiguity": "low",
            },
            "email_003_messy_1": {
                "category": "performance_alert",
                "priority": 3,
                "should_reply": True,
                "actions": ["classify", "prioritize", "investigate"],
                "description": "Production alert with mild indicators - investigate if truly critical or false alarm",
                "ambiguity": "high",  # Looks critical but might be false alarm
            },
            "email_003_messy_2": {
                "category": "unconfirmed_security",
                "priority": 4,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "investigate"],
                "description": "Security concern forwarded multiple times with unconfirmed status - requires investigation and escalation",
                "ambiguity": "high",  # Multiple forwards, unconfirmed threat
            },
            "email_003_messy_3": {
                "category": "legal_compliance",
                "priority": 5,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "reply", "investigate"],
                "description": "Legal/compliance issue with regulatory timeline - requires immediate escalation and investigation",
                "ambiguity": "medium",  # Multiple action chain, legal timeline constraint
            },
        }
        
        # Return mapped ground truth or default based on task_id
        if email_id in email_ground_truths:
            return email_ground_truths[email_id]
        
        # Fallback to task-level defaults
        defaults = {
            "easy": {
                "category": "newsletter",
                "priority": 1,
                "should_reply": False,
                "actions": ["classify", "prioritize", "archive"],
                "description": "Non-urgent newsletter",
                "ambiguity": "low",
            },
            "medium": {
                "category": "bug_report",
                "priority": 4,
                "should_reply": True,
                "actions": ["classify", "prioritize", "reply", "archive"],
                "description": "Bug report requiring investigation",
                "ambiguity": "low",
            },
            "hard": {
                "category": "critical_incident",
                "priority": 5,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "reply", "archive"],
                "description": "Critical incident",
                "ambiguity": "low",
            },
        }
        return defaults.get(task_id, defaults["easy"])

    def _get_state_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        if not self.current_state:
            return {}
        
        # Convert current_email to dict if it's a model instance
        email_dict: Any = self.current_state.current_email
        if not isinstance(email_dict, dict):
            # Pydantic v2 uses model_dump(), v1 uses dict()
            try:
                email_dict = email_dict.model_dump()
            except (AttributeError, TypeError):
                email_dict = email_dict.dict()
        
        # Ensure email_dict is a dictionary
        if not isinstance(email_dict, dict):
            email_dict = {}
        
        return {
            "task_id": self.current_state.task_id,
            "episode_id": self.current_state.episode_id,
            "difficulty": self.current_state.difficulty,
            "step": self.current_state.step,
            "max_steps": self.current_state.max_steps,
            "current_email": email_dict,
            "actions_taken": self.current_state.actions_taken,
            "score": round(self.current_state.score, 2),
            "done": self.current_state.done,
            "reward": round(self.current_state.reward, 2),
            "step_rewards": [round(r, 2) for r in self.current_state.step_rewards],
            "ground_truth": self.current_state.ground_truth,
        }
    
    def state(self) -> Dict[str, Any]:
        """Return current state."""
        return self._get_state_dict()

    def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """Execute one step in the environment."""
        if not self.current_state:
            raise RuntimeError("Must call reset() first")

        self.current_state.step += 1
        
        # Compute reward for this action using the grader
        action_type = action.get("action_type", "unknown")
        confidence = min(1.0, max(0.0, action.get("confidence", 0.5)))
        
        # Check if this action is in the correct sequence
        expected_actions = self.current_state.ground_truth.get("actions", [])
        is_correct_sequence = (
            self.current_state.step - 1 < len(expected_actions) and
            action_type == expected_actions[self.current_state.step - 1]
        )
        
        # GRADER: Use EmailTriageGrader to compute step reward
        if not is_correct_sequence:
            # Out-of-sequence: small positive penalty (clamped to valid range)
            step_reward = EmailTriageGrader.OUT_OF_SEQUENCE_PENALTY
            step_reward = clamp_score(step_reward, f"step_reward[out_of_sequence]")
            logger.warning(f"[OUT_OF_SEQUENCE] Step {self.current_state.step}: expected {expected_actions[self.current_state.step-1] if self.current_state.step-1 < len(expected_actions) else 'unknown'}, got {action_type}")
        else:
            # Use grader to compute reward based on difficulty and confidence
            step_reward = EmailTriageGrader.compute_step_reward(
                difficulty=self.current_state.difficulty,
                step_number=self.current_state.step,
                action_type=action_type,
                confidence=confidence,
            )
        
        # Ensure step_reward is always clamped (double-check)
        step_reward = clamp_score(step_reward, f"step_reward[final_{self.current_state.step}]")
        
        self.current_state.reward = step_reward
        self.current_state.step_rewards.append(step_reward)
        self.current_state.actions_taken.append({
            "step": self.current_state.step,
            "action": action_type,
            "reward": step_reward,
            "is_correct_sequence": is_correct_sequence,
        })
        
        # Update cumulative score (clamped rewards sum)
        # ALL rewards must be clamped at entry
        total_reward = sum(self.current_state.step_rewards)
        new_score = clamp_score(total_reward, f"score[summed_{self.current_state.step}_steps]")
        
        self.current_state.score = new_score
        
        # Validate final score
        validation = EmailTriageGrader.validate_bounds(step_reward, new_score)
        if not validation["all_valid"]:
            logger.error(f"[VALIDATION FAILED] Step {self.current_state.step}: {validation}")
        
        # Check if episode is done
        done = (
            self.current_state.step >= self.current_state.max_steps
            or action_type == "archive"  # Terminal action
        )
        
        self.current_state.done = done
        
        return (
            self._get_state_dict(),
            step_reward,
            done,
            {
                "action_type": action_type,
                "step": self.current_state.step,
                "max_steps": self.current_state.max_steps,
                "is_correct_sequence": is_correct_sequence,
            },
        )
