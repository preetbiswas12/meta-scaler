#!/usr/bin/env python3
"""Collect trajectories from email triage environment for fine-tuning."""
import json
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from src.environment import EmailTriageEnv
from src.graders_normalized import EmailTriageGrader


@dataclass
class TrajectoryStep:
    """Single step in trajectory."""
    step_number: int
    email: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    ground_truth: Dict[str, Any]
    metrics: Dict[str, Any]
    is_correct: bool


@dataclass
class Trajectory:
    """Complete episode trajectory."""
    episode_id: str
    task_id: str
    total_reward: float
    final_score: float
    num_steps: int
    success: bool
    steps: List[TrajectoryStep]
    timestamp: str


class TrajectoryCollector:
    """Collect high-quality trajectories from environment."""
    
    def __init__(self, num_episodes: int = 50, seed: Optional[int] = None):
        self.env = EmailTriageEnv()
        self.grader = EmailTriageGrader()
        self.num_episodes = num_episodes
        self.seed = seed
        self.trajectories: List[Trajectory] = []
        
    def collect_trajectories(self, strategy: str = "all") -> List[Trajectory]:
        """Collect trajectories using specified strategy ('all', 'high_reward', 'optimal')."""
        print(f"Collecting {self.num_episodes} trajectories with strategy: {strategy}")
        
        for episode_num in range(self.num_episodes):
            # Cycle through difficulties
            difficulty = ["easy", "medium", "hard"][episode_num % 3]
            
            trajectory = self._run_episode(difficulty)
            
            # Filter based on strategy
            if strategy == "all":
                self.trajectories.append(trajectory)
            elif strategy == "high_reward" and trajectory.total_reward > 0.5:
                self.trajectories.append(trajectory)
            elif strategy == "optimal" and trajectory.success and trajectory.num_steps <= 2:
                self.trajectories.append(trajectory)
            
            if (episode_num + 1) % 10 == 0:
                print(f"  Collected {episode_num + 1}/{self.num_episodes} episodes")
        
        print(f"✓ Collected {len(self.trajectories)} valid trajectories")
        return self.trajectories
    
    def _run_episode(self, difficulty: str) -> Trajectory:
        """Run single episode and collect trajectory."""
        episode_id = f"{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        state = self.env.reset(difficulty)
        max_steps = state["max_steps"]
        
        steps: List[TrajectoryStep] = []
        total_reward = 0.0
        success = False
        
        # Simulate optimal agent behavior based on ground truth
        ground_truth = state["ground_truth"]
        email_data = state["current_email"]
        
        for step_num in range(1, max_steps + 1):
            # Generate optimal action based on step and ground truth
            action = self._generate_optimal_action(step_num, max_steps, ground_truth)
            
            # Execute step
            state, reward, done, info = self.env.step(action)
            total_reward += reward
            
            metrics = info.get("grading_details", {}).get("metrics", {})
            is_correct = metrics.get("correct_category", metrics.get("priority_correct", metrics.get("archive_appropriate", False)))
            
            # Record step
            step = TrajectoryStep(
                step_number=step_num,
                email=email_data,
                action=action,
                reward=reward,
                ground_truth=ground_truth,
                metrics=metrics,
                is_correct=is_correct
            )
            steps.append(step)
            
            if action.get("action_type") == "classify" and metrics.get("correct_category"):
                success = True
            
            if done or step_num >= max_steps:
                break
        
        trajectory = Trajectory(
            episode_id=episode_id,
            task_id=difficulty,
            total_reward=total_reward,
            final_score=state["score"],
            num_steps=len(steps),
            success=success,
            steps=steps,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return trajectory
    
    def _generate_optimal_action(self, step_num: int, max_steps: int, ground_truth: Dict) -> Dict:
        """Generate optimal action for given step."""
        category = ground_truth.get("category", "")
        priority = ground_truth.get("priority", 3)
        should_reply = ground_truth.get("should_reply", False)
        
        # Strategy: classify early, then prioritize/reply
        if step_num == 1:
            return {
                "action_type": "classify",
                "target_category": category,
                "confidence": 0.95
            }
        elif step_num == 2 and should_reply:
            return {
                "action_type": "prioritize",
                "priority_level": priority,
                "confidence": 0.9
            }
        elif step_num == 2 and not should_reply:
            return {
                "action_type": "archive",
                "confidence": 0.9
            }
        elif step_num == 3 and should_reply:
            return {
                "action_type": "reply",
                "reply_draft": f"Thank you for your message. I will address this promptly. Best regards.",
                "confidence": 0.85
            }
        else:
            # Escalate if needed
            if category == "escalation_required":
                return {
                    "action_type": "escalate",
                    "escalation_reason": "This matter requires management attention and investigation.",
                    "confidence": 0.95
                }
            else:
                return {
                    "action_type": "archive",
                    "confidence": 0.8
                }
    
    def save_trajectories(self, filepath: str):
        """Save trajectories to JSONL file."""
        with open(filepath, 'w') as f:
            for trajectory in self.trajectories:
                # Convert dataclass to dict
                traj_dict = {
                    "episode_id": trajectory.episode_id,
                    "task_id": trajectory.task_id,
                    "total_reward": trajectory.total_reward,
                    "final_score": trajectory.final_score,
                    "num_steps": trajectory.num_steps,
                    "success": trajectory.success,
                    "timestamp": trajectory.timestamp,
                    "steps": [
                        {
                            "step_number": step.step_number,
                            "action": step.action,
                            "reward": step.reward,
                            "ground_truth": step.ground_truth,
                            "is_correct": step.is_correct
                        }
                        for step in trajectory.steps
                    ]
                }
                f.write(json.dumps(traj_dict) + '\n')
        
        print(f"✓ Saved {len(self.trajectories)} trajectories to {filepath}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected trajectories."""
        if not self.trajectories:
            return {}
        
        total_reward = sum(t.total_reward for t in self.trajectories)
        successful = sum(1 for t in self.trajectories if t.success)
        avg_steps = sum(t.num_steps for t in self.trajectories) / len(self.trajectories)
        
        by_difficulty = {}
        for difficulty in ["easy", "medium", "hard"]:
            trajs = [t for t in self.trajectories if t.task_id == difficulty]
            if trajs:
                by_difficulty[difficulty] = {
                    "count": len(trajs),
                    "success_rate": sum(1 for t in trajs if t.success) / len(trajs),
                    "avg_reward": sum(t.total_reward for t in trajs) / len(trajs),
                    "avg_steps": sum(t.num_steps for t in trajs) / len(trajs)
                }
        
        return {
            "total_episodes": len(self.trajectories),
            "successful_episodes": successful,
            "success_rate": successful / len(self.trajectories),
            "avg_reward": total_reward / len(self.trajectories),
            "avg_steps": avg_steps,
            "by_difficulty": by_difficulty
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect trajectories for fine-tuning")
    parser.add_argument("--episodes", type=int, default=50, help="Number of episodes to collect")
    parser.add_argument("--strategy", choices=["all", "high_reward", "optimal"], default="all")
    parser.add_argument("--output", default="data/trajectories.jsonl", help="Output file")
    
    args = parser.parse_args()
    
    collector = TrajectoryCollector(num_episodes=args.episodes)
    collector.collect_trajectories(strategy=args.strategy)
    
    stats = collector.get_statistics()
    print("\n" + "="*60)
    print("TRAJECTORY COLLECTION STATISTICS")
    print("="*60)
    print(json.dumps(stats, indent=2))
    
    collector.save_trajectories(args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
