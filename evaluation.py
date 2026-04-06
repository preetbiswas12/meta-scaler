#!/usr/bin/env python3
"""Model evaluation on email triage task."""
import json
import sys
import time
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

from src.environment import EmailTriageEnv
from src.graders_normalized import EmailTriageGrader


@dataclass
class EvaluationResult:
    """Result of evaluating a model."""
    model_name: str
    total_episodes: int
    success_rate: float
    avg_reward: float
    avg_steps: float
    median_reward: float
    min_reward: float
    max_reward: float
    by_difficulty: Dict[str, Dict]
    by_action_type: Dict[str, Dict]
    avg_latency_ms: float


class ModelEvaluator:
    """Evaluates models on email triage task."""
    
    def __init__(self, model_name: str = "baseline"):
        self.env = EmailTriageEnv()
        self.grader = EmailTriageGrader()
        self.model_name = model_name
    
    def evaluate(self, num_episodes: int = 30) -> EvaluationResult:
        """Evaluate model and return performance metrics."""
        print(f"Evaluating {self.model_name}...")
        print(f"Running {num_episodes} episodes...")
        
        all_rewards = []
        all_steps = []
        successful = 0
        by_difficulty = {"easy": [], "medium": [], "hard": []}
        by_action = {"classify": [], "prioritize": [], "reply": [], "escalate": [], "archive": []}
        latencies = []
        
        for episode_num in range(num_episodes):
            difficulty = ["easy", "medium", "hard"][episode_num % 3]
            
            start_time = time.time()
            episode_reward, steps, action_counts = self._run_evaluation_episode(difficulty)
            latency = (time.time() - start_time) * 1000  # ms
            latencies.append(latency)
            
            all_rewards.append(episode_reward)
            all_steps.append(steps)
            
            if episode_reward > 1.0:  # Good performance threshold
                successful += 1
            
            by_difficulty[difficulty].append(episode_reward)
            
            for action_type, count in action_counts.items():
                if count > 0:
                    by_action[action_type].append(episode_reward)
            
            if (episode_num + 1) % 10 == 0:
                print(f"  Completed {episode_num + 1}/{num_episodes} episodes")
        
        # Compute statistics
        success_rate = successful / num_episodes
        avg_reward = sum(all_rewards) / len(all_rewards)
        median_reward = sorted(all_rewards)[len(all_rewards) // 2]
        avg_steps = sum(all_steps) / len(all_steps)
        avg_latency = sum(latencies) / len(latencies)
        
        # By difficulty stats
        difficulty_stats = {}
        for difficulty in ["easy", "medium", "hard"]:
            if by_difficulty[difficulty]:
                rewards = by_difficulty[difficulty]
                difficulty_stats[difficulty] = {
                    "episodes": len(rewards),
                    "avg_reward": sum(rewards) / len(rewards),
                    "success_rate": sum(1 for r in rewards if r > 1.0) / len(rewards)
                }
        
        # By action type stats
        action_stats = {}
        for action_type in by_action:
            if by_action[action_type]:
                rewards = by_action[action_type]
                action_stats[action_type] = {
                    "avg_reward": sum(rewards) / len(rewards),
                    "count": len(rewards)
                }
        
        result = EvaluationResult(
            model_name=self.model_name,
            total_episodes=num_episodes,
            success_rate=success_rate,
            avg_reward=avg_reward,
            avg_steps=avg_steps,
            median_reward=median_reward,
            min_reward=min(all_rewards),
            max_reward=max(all_rewards),
            by_difficulty=difficulty_stats,
            by_action_type=action_stats,
            avg_latency_ms=avg_latency
        )
        
        return result
    
    def _run_evaluation_episode(self, difficulty: str) -> Tuple[float, int, Dict]:
        """Run single evaluation episode."""
        state = self.env.reset(difficulty)
        max_steps = state["max_steps"]
        ground_truth = state["ground_truth"]
        
        total_reward = 0.0
        action_counts = {
            "classify": 0,
            "prioritize": 0,
            "reply": 0,
            "escalate": 0,
            "archive": 0
        }
        
        for step_num in range(1, max_steps + 1):
            # Generate action (using mock optimal policy)
            action = self._generate_model_action(step_num, max_steps, ground_truth)
            action_counts[action.get("action_type", "unknown")] += 1
            
            state, reward, done, info = self.env.step(action)
            total_reward += reward
            
            if done:
                break
        
        return total_reward, step_num, action_counts
    
    def _generate_model_action(self, step: int, max_steps: int, ground_truth: Dict) -> Dict:
        """Generate action (placeholder - would use actual model)."""
        # Mock implementation with high accuracy
        category = ground_truth.get("category", "")
        priority = ground_truth.get("priority", 3)
        
        if step == 1:
            return {
                "action_type": "classify",
                "target_category": category,
                "confidence": 0.92  # Good baseline
            }
        elif step == 2:
            if ground_truth.get("should_reply"):
                return {
                    "action_type": "prioritize",
                    "priority_level": priority,
                    "confidence": 0.88
                }
            else:
                return {
                    "action_type": "archive",
                    "confidence": 0.85
                }
        elif step == 3 and ground_truth.get("should_reply"):
            return {
                "action_type": "reply",
                "reply_draft": "Thank you for reaching out. I'll get back to you shortly.",
                "confidence": 0.80
            }
        else:
            return {
                "action_type": "archive",
                "confidence": 0.75
            }


class ComparisonEvaluator:
    """Compares multiple models."""
    
    def __init__(self, models: Dict[str, str]):
        """
        Initialize with models to compare.
        
        Args:
            models: Dict of {model_name: model_path/model_id}
        """
        self.models = models
        self.results = {}
    
    def evaluate_all(self, num_episodes: int = 30) -> Dict[str, EvaluationResult]:
        """Evaluate all models."""
        for model_name in self.models:
            print(f"\n{'='*60}")
            print(f"Evaluating: {model_name}")
            print(f"{'='*60}")
            
            evaluator = ModelEvaluator(model_name)
            result = evaluator.evaluate(num_episodes)
            self.results[model_name] = result
        
        return self.results
    
    def compare(self) -> Dict[str, Any]:
        """Generate comparison report."""
        if not self.results:
            return {}
        
        comparison = {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "models_evaluated": len(self.results),
            "metrics": {}
        }
        
        # Collect all metrics
        for model_name, result in self.results.items():
            comparison["metrics"][model_name] = {
                "success_rate": result.success_rate,
                "avg_reward": result.avg_reward,
                "median_reward": result.median_reward,
                "avg_steps": result.avg_steps,
                "avg_latency_ms": result.avg_latency_ms,
                "by_difficulty": result.by_difficulty
            }
        
        # Calculate improvements
        if len(self.results) >= 2:
            model_names = list(self.results.keys())
            baseline = self.results[model_names[0]]
            
            comparison["improvements"] = {}
            for model_name in model_names[1:]:
                model_result = self.results[model_name]
                
                improvement = {
                    "success_rate_delta": model_result.success_rate - baseline.success_rate,
                    "reward_delta": model_result.avg_reward - baseline.avg_reward,
                    "steps_delta": model_result.avg_steps - baseline.avg_steps,
                    "latency_delta_ms": model_result.avg_latency_ms - baseline.avg_latency_ms
                }
                comparison["improvements"][model_name] = improvement
        
        return comparison
    
    def save_results(self, output_file: str = "data/evaluation_results.json"):
        """Save evaluation results."""
        results_dict = {}
        for model_name, result in self.results.items():
            results_dict[model_name] = {
                "success_rate": result.success_rate,
                "avg_reward": result.avg_reward,
                "median_reward": result.median_reward,
                "avg_steps": result.avg_steps,
                "min_reward": result.min_reward,
                "max_reward": result.max_reward,
                "avg_latency_ms": result.avg_latency_ms,
                "by_difficulty": result.by_difficulty,
                "by_action_type": result.by_action_type
            }
        
        with open(output_file, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"✓ Results saved to {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate models on email triage task")
    parser.add_argument("--episodes", type=int, default=30, help="Episodes per model")
    parser.add_argument("--compare", action="store_true", help="Compare multiple models")
    parser.add_argument("--models", nargs="+", default=["baseline"], help="Model names to evaluate")
    parser.add_argument("--output", default="data/evaluation_results.json", help="Output file")
    
    args = parser.parse_args()
    
    print("="*60)
    print("MODEL EVALUATION")
    print("="*60)
    
    if args.compare and len(args.models) > 1:
        # Compare multiple models
        models_dict = {name: name for name in args.models}
        comparator = ComparisonEvaluator(models_dict)
        comparator.evaluate_all(args.episodes)
        
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        
        comparison = comparator.compare()
        print(json.dumps(comparison, indent=2))
        
        comparator.save_results(args.output)
    else:
        # Evaluate single model
        model_name = args.models[0] if args.models else "baseline"
        evaluator = ModelEvaluator(model_name)
        result = evaluator.evaluate(args.episodes)
        
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        print(f"Model: {result.model_name}")
        print(f"Episodes: {result.total_episodes}")
        print(f"Success Rate: {result.success_rate:.1%}")
        print(f"Avg Reward: {result.avg_reward:.3f}")
        print(f"Median Reward: {result.median_reward:.3f}")
        print(f"Avg Steps: {result.avg_steps:.2f}")
        print(f"Avg Latency: {result.avg_latency_ms:.1f}ms")
        
        print(f"\nBy Difficulty:")
        for difficulty, stats in result.by_difficulty.items():
            print(f"  {difficulty}: {stats['avg_reward']:.3f} reward, {stats['success_rate']:.1%} success")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
