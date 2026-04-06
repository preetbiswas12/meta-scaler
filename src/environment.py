"""
Email Triage OpenEnv Environment
Following OpenEnv specification with step(), reset(), and state() APIs
Realistic email triage with classification, priority, reply drafting, escalation
"""
import json
import uuid
from typing import Dict, Any, Tuple, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field


class EmailSchema(BaseModel):
    email_id: str
    sender: str
    subject: str
    body: str
    timestamp: str
    is_reply_to: str = ""
    is_spam: bool = False
    urgency_indicators: List[str] = Field(default_factory=list)


class ActionSchema(BaseModel):
    action_type: str
    target_category: str = ""
    priority_level: int = 0
    reply_draft: str = ""
    escalation_reason: str = ""
    confidence: float = 0.5


class StateSchema(BaseModel):
    task_id: str
    episode_id: str
    difficulty: str
    step: int = 0
    max_steps: int = 5
    current_email: EmailSchema
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    score: float = 0.0
    done: bool = False
    reward: float = 0.0
    ground_truth: Dict[str, Any] = Field(default_factory=dict)


class EmailTriageEnv:
    """Email triage environment with OpenEnv spec (step, reset, state APIs)."""

    EMAIL_SCENARIOS = {
        "easy": [
            {
                "email_id": "easy_1",
                "sender": "customer@example.com",
                "subject": "Question about product pricing",
                "body": "Hi, I want to know the price of your premium plan. Can you help me?",
                "is_spam": False,
                "urgency_indicators": [],
                "category": "sales_inquiry",
                "priority": 2,
                "should_reply": True,
                "reply_keywords": ["price", "premium"],
                "description": "Simple sales inquiry - standard response"
            },
            {
                "email_id": "easy_2",
                "sender": "newsletter@domain.com",
                "subject": "Weekly Newsletter - May 2026",
                "body": "Check out this week's top articles...",
                "is_spam": False,
                "urgency_indicators": [],
                "category": "newsletter",
                "priority": 1,
                "should_reply": False,
                "reply_keywords": [],
                "description": "Regular newsletter - archive without reply"
            },
            {
                "email_id": "easy_3",
                "sender": "support@vendor.com",
                "subject": "Your order #12345 has shipped",
                "body": "Your package has shipped. Tracking: xyz123",
                "is_spam": False,
                "urgency_indicators": [],
                "category": "transactional",
                "priority": 1,
                "should_reply": False,
                "reply_keywords": [],
                "description": "Order confirmation - archive"
            }
        ],
        "medium": [
            {
                "email_id": "med_1",
                "sender": "unknown@sketchy-domain.xyz",
                "subject": "URGENT: Verify your account NOW!!!",
                "body": "Click here immediately to verify your account: [malicious_link]",
                "is_spam": True,
                "urgency_indicators": ["URGENT", "NOW", "!!!"],
                "category": "phishing",
                "priority": 4,
                "should_reply": False,
                "reply_keywords": [],
                "description": "Phishing attempt - classify and discard"
            },
            {
                "email_id": "med_2",
                "sender": "colleague@company.com",
                "subject": "Re: Project deadline - question about architecture",
                "body": "I reviewed the proposal. The database schema in Section 3 might cause performance issues. Can we discuss alternatives? This needs resolving before Thursday.",
                "is_spam": False,
                "urgency_indicators": ["Thursday", "deadline"],
                "category": "work_technical",
                "priority": 4,
                "should_reply": True,
                "reply_keywords": ["database", "performance", "architecture"],
                "description": "Urgent technical discussion in thread"
            },
            {
                "email_id": "med_3",
                "sender": "hr@company.com",
                "subject": "Benefits enrollment deadline reminder",
                "body": "Friendly reminder: Benefits enrollment closes December 31st. Please complete your enrollment: [link]",
                "is_spam": False,
                "urgency_indicators": ["deadline", "December 31"],
                "category": "hr_admin",
                "priority": 3,
                "should_reply": False,
                "reply_keywords": [],
                "description": "Internal admin notice - archive"
            }
        ],
        "hard": [
            {
                "email_id": "hard_1",
                "sender": "customer-support@similar-company.net",
                "subject": "We're so much better - Switch today!",
                "body": "You should really consider switching to our service. We're cheaper and better. Call now: 1-800-SPAM123",
                "is_spam": True,
                "urgency_indicators": ["now", "cheaper"],
                "category": "advertising_spam",
                "priority": 1,
                "should_reply": False,
                "reply_keywords": [],
                "description": "Subtle spam - looks legitimate but is solicitation"
            },
            {
                "email_id": "hard_2",
                "sender": "manager@company.com",
                "subject": "FW: Customer complaint - HIGH PRIORITY",
                "body": "I'm forwarding this complaint from a major customer. They claim our software caused data loss. " +
                        "This is critical. The customer is considering legal action. " +
                        "We need to investigate immediately and provide a response. " +
                        "Customer contact: vip@client.com. They're expecting our response by tomorrow.",
                "is_spam": False,
                "urgency_indicators": ["HIGH PRIORITY", "critical", "immediately", "tomorrow"],
                "category": "escalation_required",
                "priority": 5,
                "should_reply": True,
                "reply_keywords": ["escalate", "investigation", "legal"],
                "description": "Critical escalation - requires immediate action and investigation"
            },
            {
                "email_id": "hard_3",
                "sender": "analyst@company.com",
                "subject": "Re: Quarterly revenue analysis - thoughts on Q2 projections?",
                "body": "I've attached the Q2 revenue projections. " +
                        "Looking at the data, there's an interesting anomaly in the APAC region. " +
                        "Our growth projection assumes 15% YoY, but historical variance suggests we should be more conservative. " +
                        "What are your thoughts? Also, should we flag the supply chain risks to the board? " +
                        "I noticed our competitors are seeing margin compression.",
                "is_spam": False,
                "urgency_indicators": [],
                "category": "internal_strategic",
                "priority": 3,
                "should_reply": True,
                "reply_keywords": ["analysis", "projection", "strategic", "board"],
                "description": "Strategic discussion with multiple issues - requires thoughtful multi-point reply"
            }
        ]
    }

    def __init__(self):
        self._state = None
        self.episode_id = str(uuid.uuid4())
        self.current_difficulty = None
        self.current_email = None

    def reset(self, task_id: str = "easy") -> Dict[str, Any]:
        """Reset environment and return initial state."""
        if task_id not in self.EMAIL_SCENARIOS:
            raise ValueError(f"Invalid task_id: {task_id}")

        self.current_difficulty = task_id
        scenarios = self.EMAIL_SCENARIOS[task_id]
        
        # Select random email from scenario
        import random
        email_data = random.choice(scenarios)
        
        self.current_email = EmailSchema(
            email_id=email_data["email_id"],
            sender=email_data["sender"],
            subject=email_data["subject"],
            body=email_data["body"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            is_reply_to="",
            is_spam=email_data.get("is_spam", False),
            urgency_indicators=email_data.get("urgency_indicators", [])
        )

        max_steps_map = {"easy": 3, "medium": 4, "hard": 5}

        self._state = StateSchema(
            task_id=str(uuid.uuid4()),
            episode_id=str(uuid.uuid4()),
            difficulty=task_id,
            step=0,
            max_steps=max_steps_map[task_id],
            current_email=self.current_email,
            actions_taken=[],
            score=0.0,
            done=False,
            reward=0.0,
            ground_truth={
                "category": email_data["category"],
                "priority": email_data["priority"],
                "should_reply": email_data["should_reply"],
                "description": email_data["description"]
            }
        )

        return self.state()

    def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """Execute environment step and return (state, reward, done, info)."""
        if self._state.done:
            raise RuntimeError("Episode already done. Call reset() first.")

        # Parse and validate action
        try:
            parsed_action = ActionSchema(**action)
        except Exception as e:
            # Invalid action format
            reward = -0.5
            parsed_action = action
        else:
            # Grade the action
            from src.graders import EmailTriageGrader
            
            grader = EmailTriageGrader()
            reward, grading_info = grader.grade_action(
                action=parsed_action,
                email=self.current_email,
                ground_truth=self._state.ground_truth,
                step_count=self._state.step + 1,
                max_steps=self._state.max_steps
            )
            
            info = {
                "grading_details": grading_info,
                "episode_id": self._state.episode_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_parsed": parsed_action.model_dump() if hasattr(parsed_action, 'model_dump') else parsed_action
            }
        
        self._state.step += 1
        self._state.actions_taken.append({
            "step": self._state.step,
            "action": parsed_action.model_dump() if hasattr(parsed_action, 'model_dump') else parsed_action,
            "reward": reward
        })
        self._state.reward = reward
        
        # Accumulate score
        self._state.score = sum(a["reward"] for a in self._state.actions_taken) / len(self._state.actions_taken)

        # Episode ends when:
        # 1. Max steps reached
        # 2. Final action taken (reply, escalate, or archive)
        action_type = action.get("action_type", "") if isinstance(action, dict) else getattr(action, "action_type", "")
        is_final_action = action_type in ["reply", "escalate", "archive"]
        
        done = (
            self._state.step >= self._state.max_steps
            or is_final_action
        )
        self._state.done = done

        return self.state(), reward, done, info

    def state(self) -> Dict[str, Any]:
        """Return current state as dictionary."""
        return json.loads(self._state.model_dump_json())

    def render(self) -> str:
        """Return state as formatted JSON."""
        return json.dumps(self.state(), indent=2)


if __name__ == "__main__":
    env = EmailTriageEnv()
    state = env.reset("easy")
    print("Initial state:", json.dumps(state, indent=2))

    action = {
        "action_type": "classify",
        "target_category": "sales_inquiry",
        "priority_level": 2,
        "confidence": 0.95
    }

    state, reward, done, info = env.step(action)
    print(f"\nScore: {state['score']}")
    print(f"Reward: {reward}")
    print(f"Done: {done}")



if __name__ == "__main__":
    env = CodeTestGenerationEnv()
    state = env.reset("easy")
    print("Initial state:", json.dumps(state, indent=2))

    tests = '''import pytest
from main import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0

def test_add_mixed():
    assert add(5, -3) == 2
'''

    state, reward, done, info = env.step(tests)
    print(f"\nScore: {state['score']}")
    print(f"Reward: {reward}")
    print(f"Done: {done}")
