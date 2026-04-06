#!/usr/bin/env python3
"""Training data formatter for fine-tuning."""
import json
import sys
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone


class TrainingDataGenerator:
    """Convert trajectories to various training formats."""
    
    def __init__(self, trajectories_file: str):
        self.trajectories = self._load_trajectories(trajectories_file)
        self.training_examples = []
    
    def _load_trajectories(self, filepath: str) -> List[Dict]:
        """Load trajectories from JSONL file."""
        trajectories = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    trajectories.append(json.loads(line))
        return trajectories

    def generate_supervised_pairs(self) -> List[Dict]:
        """Generate (prompt, completion) pairs for supervised fine-tuning."""
        print("Generating supervised learning pairs...")
        pairs = []
        
        for trajectory in self.trajectories:
            email_data = trajectory["steps"][0]["action"].get("email", {}) if trajectory["steps"] else {}
            
            # Create prompt from email content
            prompt = self._create_email_prompt(email_data, trajectory["task_id"])
            
            # Use first (classify) step's action as golden completion
            if trajectory["steps"]:
                first_step = trajectory["steps"][0]
                action = first_step["action"]
                
                # Build completion string
                completion = self._action_to_completion(action)
                
                pair = {
                    "prompt": prompt,
                    "completion": completion,
                    "episode_id": trajectory["episode_id"],
                    "reward": trajectory["total_reward"],
                    "difficulty": trajectory["task_id"]
                }
                pairs.append(pair)
        
        self.training_examples = pairs
        print(f"✓ Generated {len(pairs)} supervised pairs")
        return pairs
    
    def generate_preference_pairs(self) -> List[Dict]:
        """Generate preference pairs for preference learning (DPO, IPO, etc)."""
        print("Generating preference learning pairs...")
        pairs = []
        
        for trajectory in self.trajectories:
            email_data = trajectory["steps"][0].get("action", {}) if trajectory["steps"] else {}
            prompt = self._create_email_prompt(email_data, trajectory["task_id"])
            
            # Take first step (classification)
            if trajectory["steps"]:
                step = trajectory["steps"][0]
                correct_action = step["action"]
                correct_reward = step["reward"]
                
                # Generate alternative (incorrect) action
                incorrect_action = self._generate_alternative_action(correct_action)
                
                pair = {
                    "prompt": prompt,
                    "chosen": self._action_to_completion(correct_action),
                    "rejected": self._action_to_completion(incorrect_action),
                    "chosen_reward": correct_reward,
                    "episode_id": trajectory["episode_id"],
                    "difficulty": trajectory["task_id"]
                }
                pairs.append(pair)
        
        self.training_examples = pairs
        print(f"✓ Generated {len(pairs)} preference pairs")
        return pairs
    
    def generate_trajectory_sequences(self) -> List[Dict]:
        """
        Generate full multi-step trajectories with trajectory-level rewards.
        Useful for RL fine-tuning approaches.
        """
        print("Generating trajectory sequences...")
        sequences = []
        
        for trajectory in self.trajectories:
            # Build conversation
            messages = []
            
            # Initial system message
            messages.append({
                "role": "system",
                "content": "You are an expert email triage assistant. Analyze emails and take appropriate actions."
            })
            
            # Add email context in first step
            if trajectory["steps"]:
                first_step = trajectory["steps"][0]
                email_context = first_step.get("email", {})
                prompt = self._create_email_prompt(email_context, trajectory["task_id"])
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
            # Add all steps as conversation
            trajectory_actions = []
            for step in trajectory["steps"]:
                action = step["action"]
                reward = step["reward"]
                
                trajectory_actions.append({
                    "action": action,
                    "reward": reward,
                    "step": step["step_number"]
                })
                
                # Add assistant response
                completion = self._action_to_completion(action)
                messages.append({
                    "role": "assistant",
                    "content": completion
                })
            
            sequence = {
                "messages": messages,
                "trajectory_reward": trajectory["total_reward"],
                "final_score": trajectory["final_score"],
                "success": trajectory["success"],
                "num_steps": trajectory["num_steps"],
                "difficulty": trajectory["task_id"],
                "episode_id": trajectory["episode_id"]
            }
            sequences.append(sequence)
        
        self.training_examples = sequences
        print(f"✓ Generated {len(sequences)} trajectory sequences")
        return sequences
    
    def _create_email_prompt(self, email: Dict, difficulty: str) -> str:
        """Create prompt from email data."""
        subject = email.get("subject", "No subject")
        body = email.get("body", "No content")
        sender = email.get("sender", "Unknown sender")
        
        return f"""Email Triage Task [{difficulty.upper()}]

FROM: {sender}
SUBJECT: {subject}

BODY:
{body}

Please analyze this email and take the appropriate action. What category does this belong to? Should it be prioritized, archived, replied to, or escalated?"""
    
    def _action_to_completion(self, action: Dict) -> str:
        """Convert action dict to completion string."""
        action_type = action.get("action_type", "unknown")
        
        if action_type == "classify":
            category = action.get("target_category", "unknown")
            confidence = action.get("confidence", 1.0)
            return f"ACTION: Classify as [{category}] (confidence: {confidence:.2f})"
        
        elif action_type == "prioritize":
            priority = action.get("priority_level", 3)
            confidence = action.get("confidence", 1.0)
            return f"ACTION: Set priority to [{priority}] (confidence: {confidence:.2f})"
        
        elif action_type == "reply":
            reply = action.get("reply_draft", "")[:100]
            confidence = action.get("confidence", 1.0)
            return f"ACTION: Reply with message (confidence: {confidence:.2f})\nReply: {reply}..."
        
        elif action_type == "escalate":
            reason = action.get("escalation_reason", "")[:100]
            confidence = action.get("confidence", 1.0)
            return f"ACTION: Escalate (confidence: {confidence:.2f})\nReason: {reason}..."
        
        elif action_type == "archive":
            confidence = action.get("confidence", 1.0)
            return f"ACTION: Archive (confidence: {confidence:.2f})"
        
        else:
            return f"ACTION: {action_type}"
    
    def _generate_alternative_action(self, correct_action: Dict) -> Dict:
        """Generate an incorrect alternative action."""
        action_type = correct_action.get("action_type", "classify")
        
        # Simple strategy: swap to different category/action
        alternatives = {
            "classify": {
                "action_type": "archive",
                "confidence": 0.5
            },
            "archive": {
                "action_type": "classify",
                "target_category": "spam",
                "confidence": 0.4
            },
            "prioritize": {
                "action_type": "archive",
                "confidence": 0.3
            },
            "reply": {
                "action_type": "archive",
                "confidence": 0.4
            },
            "escalate": {
                "action_type": "archive",
                "confidence": 0.3
            }
        }
        
        return alternatives.get(action_type, {"action_type": "archive", "confidence": 0.3})
    
    def save_training_data(self, output_file: str, format_type: str = "jsonl"):
        """Save training data to file."""
        if not self.training_examples:
            print("No training examples generated")
            return
        
        if format_type == "jsonl":
            with open(output_file, 'w') as f:
                for example in self.training_examples:
                    f.write(json.dumps(example) + '\n')
        
        elif format_type == "json":
            with open(output_file, 'w') as f:
                json.dump(self.training_examples, f, indent=2)
        
        print(f"✓ Saved {len(self.training_examples)} examples to {output_file}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about training data."""
        if not self.training_examples:
            return {}
        
        return {
            "total_examples": len(self.training_examples),
            "by_difficulty": self._count_by_difficulty(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _count_by_difficulty(self) -> Dict[str, int]:
        """Count examples by difficulty."""
        counts = {"easy": 0, "medium": 0, "hard": 0}
        for example in self.training_examples:
            difficulty = example.get("difficulty", "unknown")
            if difficulty in counts:
                counts[difficulty] += 1
        return counts


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate training data from trajectories")
    parser.add_argument("--trajectories", default="data/trajectories.jsonl", help="Trajectories file")
    parser.add_argument("--format", choices=["supervised", "preference", "trajectory"], 
                       default="supervised", help="Training format")
    parser.add_argument("--output", help="Output file (auto-named if not specified)")
    
    args = parser.parse_args()
    
    generator = TrainingDataGenerator(args.trajectories)
    
    if args.format == "supervised":
        examples = generator.generate_supervised_pairs()
    elif args.format == "preference":
        examples = generator.generate_preference_pairs()
    elif args.format == "trajectory":
        examples = generator.generate_trajectory_sequences()
    
    output_file = args.output or f"data/training_{args.format}.jsonl"
    generator.save_training_data(output_file)
    
    stats = generator.get_statistics()
    print("\n" + "="*60)
    print("TRAINING DATA STATISTICS")
    print("="*60)
    print(json.dumps(stats, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
