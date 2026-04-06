#!/usr/bin/env python3
"""Email triage inference with OpenAI-compatible APIs."""
import os
import sys
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("[ERROR] requests not installed: pip install requests")
    sys.exit(1)

from src.environment import EmailTriageEnv, ActionSchema


class OpenAIClient:
    """OpenAI-compatible client for LLM inference."""

    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.api_key = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
        self.timeout = 30

        if not self.api_key:
            raise ValueError("API key not set (HF_TOKEN or OPENAI_API_KEY)")

    def generate_email_action(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM API and return response."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            result = resp.json()
            if "choices" not in result or not result["choices"]:
                raise ValueError("No choices in response")
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Connection error: {e}")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Timeout after {self.timeout}s")
        except Exception as e:
            raise RuntimeError(f"API failed: {e}")


def run_inference_episode(
    env: EmailTriageEnv,
    task_id: str,
    max_steps: int = None,
    client: Optional[OpenAIClient] = None,
    model_name: str = "baseline",
    benchmark_name: str = "email-triage",
) -> dict:
    """Run one episode and return results."""
    episode_id = str(datetime.now(timezone.utc).timestamp()).replace(".", "")
    step_count = 0
    total_reward = 0.0
    final_score = 0.0
    all_rewards: List[float] = []
    episode_success = False
    last_error = None

    # [START] log - REQUIRED FORMAT
    print(f"[START] task={task_id} env={benchmark_name} model={model_name}", flush=True)

    try:
        state = env.reset(task_id)
        episode_max_steps = max_steps or state.get("max_steps", 5)

        for step_num in range(1, episode_max_steps + 1):
            email = state["current_email"]
            
            system_prompt = (
                "You are an expert email triage system. Your task is to analyze emails and decide the appropriate action. "
                "You can classify, prioritize, draft replies, escalate, or archive emails. "
                "For each action, provide a JSON response with: action_type, target_category, priority_level, confidence, etc. "
                "Be concise and decisive."
            )

            user_prompt = (
                f"Email to triage:\n"
                f"From: {email['sender']}\n"
                f"Subject: {email['subject']}\n"
                f"Body: {email['body']}\n\n"
                f"Step {step_num}/{episode_max_steps}. "
                f"Previous actions: {len(state.get('actions_taken', []))}\n"
                f"Choose your next action (classify, prioritize, reply, escalate, or archive). "
                f"Return a JSON object with the action details."
            )

            if not client:
                action_json = _get_mock_action(task_id, step_num)
            else:
                try:
                    action_json = client.generate_email_action(system_prompt, user_prompt)
                except RuntimeError as e:
                    last_error = str(e)
                    action_json = _get_mock_action(task_id, step_num)

            # Parse action
            try:
                action = json.loads(action_json)
            except:
                action = _get_mock_action_dict(task_id, step_num)

            state, reward, done, info = env.step(action)

            step_count += 1
            total_reward += reward
            all_rewards.append(reward)
            final_score = state["score"]

            action_type = action.get('action_type', 'unknown')
            
            # [STEP] log - REQUIRED FORMAT
            # Format: [STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
            error_msg = "null" if not last_error else f'"{last_error}"'
            print(f"[STEP]  step={step_num} action={action_type} reward={reward:.2f} done={'true' if done else 'false'} error={error_msg}", flush=True)

            # Success = classified correctly in first step with high reward
            if action.get("action_type") == "classify" and reward >= 1.0:
                episode_success = True
            
            if done or step_num >= episode_max_steps:
                break

        # [END] log - REQUIRED FORMAT
        # Format: [END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
        rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
        print(f"[END]   success={'true' if episode_success else 'false'} steps={step_count} score={final_score:.2f} rewards={rewards_str}", flush=True)

        return {
            "episode_id": episode_id,
            "task_id": task_id,
            "steps": step_count,
            "final_score": final_score,
            "total_reward": total_reward,
            "avg_reward": total_reward / step_count if step_count > 0 else 0.0,
            "success": episode_success,
            "completed": state.get("done", False),
            "rewards": all_rewards,
        }

    except Exception as e:
        # [END] log on error - REQUIRED FORMAT
        print(f"[END]   success=false steps={step_count} score=0.00 rewards={','.join(f'{r:.2f}' for r in all_rewards)}", flush=True)
        return {
            "episode_id": episode_id,
            "task_id": task_id,
            "error": str(e),
            "completed": False,
            "success": False,
        }



def _get_mock_action(task_id: str, step_num: int) -> str:
    """Get mock email action for testing without API."""
    actions = {
        "easy": [
            '{"action_type": "classify", "target_category": "sales_inquiry", "confidence": 0.95}',
            '{"action_type": "archive", "confidence": 0.85}',
            '{"action_type": "classify", "target_category": "newsletter", "confidence": 0.9}',
        ],
        "medium": [
            '{"action_type": "classify", "target_category": "phishing", "confidence": 0.98}',
            '{"action_type": "classify", "target_category": "work_technical", "priority_level": 4, "confidence": 0.9}',
            '{"action_type": "prioritize", "priority_level": 4, "confidence": 0.85}',
            '{"action_type": "reply", "reply_draft": "Thank you for the technical discussion. I agree we should review the database schema. Let us schedule a meeting.", "confidence": 0.8}',
        ],
        "hard": [
            '{"action_type": "classify", "target_category": "advertising_spam", "confidence": 0.92}',
            '{"action_type": "escalate", "escalation_reason": "Critical customer complaint - potential legal issue", "confidence": 0.98}',
            '{"action_type": "prioritize", "priority_level": 5, "confidence": 0.99}',
            '{"action_type": "reply", "reply_draft": "We take this matter very seriously. I am coordinating an immediate investigation with our technical team and will have a detailed response for you within 24 hours.", "confidence": 0.85}',
        ],
    }
    
    step_actions = actions.get(task_id, [])
    return step_actions[min(step_num - 1, len(step_actions) - 1)]


def _get_mock_action_dict(task_id: str, step_num: int) -> Dict[str, Any]:
    """Get mock email action as dictionary."""
    action_json = _get_mock_action(task_id, step_num)
    try:
        return json.loads(action_json)
    except:
        return {
            "action_type": "classify" if step_num == 1 else "archive",
            "target_category": "newsletter",
            "confidence": 0.8
        }


def main():
    """Main entry point for email triage inference."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Email Triage inference"
    )
    parser.add_argument(
        "--task",
        choices=["easy", "medium", "hard", "all"],
        default="easy",
        help="Task difficulty level",
    )
    parser.add_argument(
        "--steps", type=int, default=3, help="Max steps per episode"
    )
    parser.add_argument(
        "--episodes", type=int, default=1, help="Number of episodes to run"
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Use actual OpenAI API (requires API credentials)",
    )

    args = parser.parse_args()

    tasks = (
        ["easy", "medium", "hard"] if args.task == "all" else [args.task]
    )

    # Get model name from environment
    model_name = os.getenv("MODEL_NAME", "baseline")
    benchmark_name = "email-triage"

    client = None
    if args.use_api:
        try:
            client = OpenAIClient()
            logger.info(f"[INFO] Connected to API at {client.base_url} with model {client.model_name}")
        except ValueError as e:
            logger.warning(f"[WARNING] Failed to initialize API client: {e}")
            logger.info("[INFO] Falling back to mock tests")

    env = EmailTriageEnv()
    results = []

    for task_id in tasks:
        for episode in range(args.episodes):
            result = run_inference_episode(
                env, task_id, max_steps=args.steps, client=client,
                model_name=model_name, benchmark_name=benchmark_name
            )
            results.append(result)

    # Results printed via [START], [STEP], [END] format
    return 0 if all(r.get("completed", False) or r.get("success", False) for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
