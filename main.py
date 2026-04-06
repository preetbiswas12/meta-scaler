#!/usr/bin/env python3
"""
Entry point for Code Test Generation OpenEnv Environment
"""
import sys
import argparse
from src.environment import CodeTestGenerationEnv
from src.tasks import list_all_tasks, get_task_by_id
from inference import run_inference_episode, OpenAIClient
import json


def show_tasks():
    """Display all available tasks"""
    print("Available Tasks:")
    print("=" * 60)
    for task_id in list_all_tasks():
        task = get_task_by_id(task_id)
        print(f"\n{task_id.upper()}: {task['name']}")
        print(f"  Description: {task['description']}")
        print(f"  Expected Tests: {task['expected_tests']}")
        print(f"  Edge Cases: {', '.join(task['edge_cases'][:3])}...")


def run_demo():
    """Run a simple demo"""
    print("Running Demo: Code Test Generation")
    print("=" * 60)

    env = CodeTestGenerationEnv()
    state = env.reset("easy")

    print(f"\nTask: {state['function_name']}")
    print(f"Code:\n{state['code_snippet']}")

    test_code = '''
def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0
'''

    print(f"\nGenerated Tests:\n{test_code}")

    state, reward, done, info = env.step(test_code)

    print(f"\nResults:")
    print(f"  Score: {state['score']:.3f}")
    print(f"  Reward: {reward:.3f}")
    print(f"  Done: {done}")
    print(f"  Metrics: {info['grading_details']['metrics']}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Code Test Generation OpenEnv Environment"
    )
    parser.add_argument(
        "command",
        choices=["demo", "tasks", "inference"],
        help="Command to run",
    )
    parser.add_argument(
        "--task",
        choices=["easy", "medium", "hard", "all"],
        default="easy",
        help="Task difficulty (for inference)",
    )
    parser.add_argument(
        "--steps", type=int, default=3, help="Max steps per episode"
    )
    parser.add_argument(
        "--episodes", type=int, default=1, help="Number of episodes"
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Use actual OpenAI API",
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "tasks":
        show_tasks()
    elif args.command == "inference":
        # Import here to avoid issues if inference modules not ready
        from inference import main as inference_main

        sys.argv = ["inference.py", "--task", args.task, "--steps", str(args.steps), "--episodes", str(args.episodes)]
        if args.use_api:
            sys.argv.append("--use-api")
        sys.exit(inference_main())


if __name__ == "__main__":
    main()
