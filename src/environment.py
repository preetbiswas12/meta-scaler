"""
Email Triage OpenEnv Environment - Multi-Step Implementation
OpenEnv-compliant multi-step reasoning with normalized grading.
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field


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
    score: float = 0.0
    done: bool = False
    reward: float = 0.0
    ground_truth: Dict[str, Any] = Field(default_factory=dict)
    step_rewards: List[float] = Field(default_factory=list)


class EmailTriageEnv:
    """Email triage environment with multi-step reasoning."""

    def __init__(self):
        """Initialize environment."""
        self.episode_id: Optional[str] = None
        self.task_id: Optional[str] = None
        self.current_state: Optional[StateSchema] = None
        self.difficulty_config = {
            "easy": {"max_steps": 3, "base_reward_per_step": 0.30},
            "medium": {"max_steps": 4, "base_reward_per_step": 0.25},
            "hard": {"max_steps": 5, "base_reward_per_step": 0.20},
        }
        self.email_bank = self._create_email_bank()

    def _create_email_bank(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create a bank of sample emails for different difficulties."""
        return {
            "easy": [
                {
                    "email_id": "email_001",
                    "sender": "newsletter@company.com",
                    "subject": "Weekly newsletter",
                    "body": "Here's this week's updates...",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "is_spam": False,
                    "urgency_indicators": [],
                },
            ],
            "medium": [
                {
                    "email_id": "email_002",
                    "sender": "customer@example.com",
                    "subject": "Product bug report",
                    "body": "I found a bug in your software when trying to process large files. The system crashes and loses data.",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["urgent"],
                },
            ],
            "hard": [
                {
                    "email_id": "email_003",
                    "sender": "ceo@customer.com",
                    "subject": "CRITICAL: System down, data loss reported",
                    "body": "Our entire system is down and we've lost critical customer data. This is a critical emergency affecting 100+ clients.",
                    "timestamp": "2024-01-15T16:45:00Z",
                    "is_spam": False,
                    "urgency_indicators": ["critical", "urgent", "data_loss"],
                },
            ],
        }

    def reset(self, task_id: str = "easy") -> Dict[str, Any]:
        """Reset environment for a new episode."""
        # Validate task_id
        if task_id not in self.difficulty_config:
            raise ValueError(f"Invalid task_id '{task_id}'. Must be one of: {list(self.difficulty_config.keys())}")

        self.task_id = task_id
        self.episode_id = str(uuid.uuid4())
        
        config = self.difficulty_config[task_id]
        email_list = self.email_bank.get(task_id, self.email_bank["easy"])
        current_email = email_list[0] if email_list else {}

        self.current_state = StateSchema(
            task_id=task_id,
            episode_id=self.episode_id,
            difficulty=task_id,
            step=0,
            max_steps=config["max_steps"],
            current_email=current_email,
            actions_taken=[],
            score=0.0,
            done=False,
            reward=0.0,
            step_rewards=[],
            ground_truth=self._get_ground_truth(task_id),
        )

        return self._get_state_dict()

    def _get_ground_truth(self, task_id: str) -> Dict[str, Any]:
        """Get ground truth actions for a task."""
        ground_truths = {
            "easy": {
                "category": "newsletter",
                "priority": 1,
                "should_reply": False,
                "actions": ["classify", "prioritize", "archive"],
                "description": "Non-urgent newsletter that should be archived"
            },
            "medium": {
                "category": "phishing",
                "priority": 4,
                "should_reply": True,
                "actions": ["classify", "prioritize", "reply", "archive"],
                "description": "Phishing attempt requiring user warning and escalation"
            },
            "hard": {
                "category": "critical_incident",
                "priority": 5,
                "should_reply": True,
                "actions": ["classify", "prioritize", "escalate", "reply", "archive"],
                "description": "Critical data loss incident requiring immediate escalation to senior management"
            },
        }
        return ground_truths.get(task_id, {
            "category": "unknown",
            "priority": 2,
            "should_reply": False,
            "actions": ["classify"],
            "description": "Unknown email type"
        })

    def _get_state_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        if not self.current_state:
            return {}
        
        # Convert current_email to dict if it's a model instance
        email_dict = self.current_state.current_email
        if hasattr(email_dict, 'dict'):
            email_dict = email_dict.dict()
        
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
        
        # Compute reward for this action
        action_type = action.get("action_type", "unknown")
        confidence = min(1.0, max(0.0, action.get("confidence", 0.5)))
        
        # Check if this action is in the correct sequence
        expected_actions = self.current_state.ground_truth.get("actions", [])
        is_correct_sequence = (
            self.current_state.step - 1 < len(expected_actions) and
            action_type == expected_actions[self.current_state.step - 1]
        )
        
        # Compute reward based on sequence correctness
        if not is_correct_sequence:
            # Out-of-sequence penalty (fixed at -0.10)
            step_reward = -0.10
        else:
            # Base reward from action quality
            base_reward = self.difficulty_config[self.current_state.difficulty]["base_reward_per_step"]
            step_reward = base_reward * confidence  # Reward scaled by confidence [0, base_reward]
        
        # Clamp to [-0.10, 1.0]
        step_reward = max(-0.10, min(1.0, step_reward))
        
        self.current_state.reward = step_reward
        self.current_state.step_rewards.append(step_reward)
        self.current_state.actions_taken.append({
            "step": self.current_state.step,
            "action": action_type,
            "reward": step_reward,
            "is_correct_sequence": is_correct_sequence,
        })
        
        # Update cumulative score (normalized, only counting positive rewards)
        total_reward = sum(max(0, r) for r in self.current_state.step_rewards)
        self.current_state.score = min(1.0, total_reward)  # Cap at 1.0
        
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
