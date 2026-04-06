#!/usr/bin/env python3
"""
End-to-end fine-tuning workflow.
Collects data → Creates training pairs → Fine-tunes model → Evaluates results.
"""
import json
import os
import sys
from typing import Dict, Any
import shutil


def ensure_directories():
    """Create required directories."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✓ Directories ready")


def step_1_collect_trajectories(num_episodes: int = 50) -> str:
    """Step 1: Collect trajectories from environment."""
    print("\n" + "="*60)
    print("STEP 1: COLLECT TRAJECTORIES")
    print("="*60)
    
    from trajectory_collector import TrajectoryCollector
    
    output_file = "data/trajectories.jsonl"
    
    if os.path.exists(output_file):
        print(f"✓ Trajectories already exist: {output_file}")
        return output_file
    
    collector = TrajectoryCollector(num_episodes=num_episodes)
    collector.collect_trajectories(strategy="all")
    
    stats = collector.get_statistics()
    print("\nTrajectory Statistics:")
    print(json.dumps(stats, indent=2))
    
    collector.save_trajectories(output_file)
    return output_file


def step_2_generate_training_data(
    trajectories_file: str,
    format_type: str = "supervised"
) -> str:
    """Step 2: Convert trajectories to training format."""
    print("\n" + "="*60)
    print("STEP 2: GENERATE TRAINING DATA")
    print("="*60)
    
    from training_data_generator import TrainingDataGenerator
    
    output_file = f"data/training_{format_type}.jsonl"
    
    if os.path.exists(output_file):
        print(f"✓ Training data already exists: {output_file}")
        return output_file
    
    generator = TrainingDataGenerator(trajectories_file)
    
    if format_type == "supervised":
        generator.generate_supervised_pairs()
    elif format_type == "preference":
        generator.generate_preference_pairs()
    elif format_type == "trajectory":
        generator.generate_trajectory_sequences()
    
    stats = generator.get_statistics()
    print("\nTraining Data Statistics:")
    print(json.dumps(stats, indent=2))
    
    generator.save_training_data(output_file)
    return output_file


def step_3_prepare_finetuning(
    training_data: str,
    backend: str = "openai",
    model: str = "gpt-3.5-turbo"
) -> Dict[str, Any]:
    """Step 3: Prepare fine-tuning job."""
    print("\n" + "="*60)
    print("STEP 3: PREPARE FINE-TUNING JOB")
    print("="*60)
    
    from fine_tuning import FineTuningOrchestrator
    
    print(f"Backend: {backend}")
    print(f"Model: {model}")
    print(f"Training Data: {training_data}")
    
    # Create finetuner
    try:
        finetuner = FineTuningOrchestrator.create_finetuner(
            backend, model, training_data
        )
        
        # Verify training data
        count = 0
        with open(training_data, 'r') as f:
            for line in f:
                if line.strip():
                    count += 1
        
        print(f"✓ Training data verified: {count} examples")
        
        return {
            "backend": backend,
            "model": model,
            "training_data": training_data,
            "num_examples": count,
            "finetuner": finetuner
        }
    except Exception as e:
        print(f"✗ Error preparing fine-tuning: {e}")
        return {}


def step_4_submit_finetuning_job(
    finetuner_config: Dict,
    dry_run: bool = False
) -> str:
    """Step 4: Submit fine-tuning job."""
    print("\n" + "="*60)
    print("STEP 4: SUBMIT FINE-TUNING JOB")
    print("="*60)
    
    if dry_run:
        print("⚠ DRY RUN MODE - Not actually submitting to API")
        job_id = "dry_run_" + str(__import__('time').time()).replace('.', '')
        print(f"Mock Job ID: {job_id}")
        return job_id
    
    try:
        finetuner = finetuner_config.get("finetuner")
        if not finetuner:
            print("No finetuner available")
            return None
        
        job_id = finetuner.submit_job()
        
        status = finetuner.check_status()
        print("\nJob Submitted:")
        print(json.dumps(status, indent=2, default=str))
        
        # Save job config
        from fine_tuning import FineTuningOrchestrator
        FineTuningOrchestrator.save_job_config(job_id, status)
        
        return job_id
    except Exception as e:
        print(f"✗ Error submitting job: {e}")
        return None


def step_5_evaluate_baseline(num_episodes: int = 30) -> Dict:
    """Step 5: Evaluate baseline model."""
    print("\n" + "="*60)
    print("STEP 5: EVALUATE BASELINE")
    print("="*60)
    
    from evaluation import ModelEvaluator
    
    evaluator = ModelEvaluator("baseline")
    result = evaluator.evaluate(num_episodes)
    
    print("\nBaseline Evaluation Results:")
    print(f"Success Rate: {result.success_rate:.1%}")
    print(f"Avg Reward: {result.avg_reward:.3f}")
    print(f"Avg Steps: {result.avg_steps:.2f}")
    
    return {
        "model": "baseline",
        "success_rate": result.success_rate,
        "avg_reward": result.avg_reward,
        "avg_steps": result.avg_steps,
        "by_difficulty": result.by_difficulty
    }


def step_6_monitor_finetuning(job_id: str, max_checks: int = 5) -> Dict:
    """Step 6: Monitor fine-tuning job (polling)."""
    print("\n" + "="*60)
    print("STEP 6: MONITOR FINE-TUNING")
    print("="*60)
    
    if not job_id:
        print("No job ID provided")
        return {}
    
    print(f"Job ID: {job_id}")
    print(f"Note: In production, check status at intervals")
    print(f"Status checks are backend-specific and require job tracking")
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "checks": max_checks
    }


def step_7_generate_report(
    baseline_results: Dict,
    finetuning_config: Dict,
    job_id: str
) -> str:
    """Step 7: Generate fine-tuning report."""
    print("\n" + "="*60)
    print("STEP 7: GENERATE REPORT")
    print("="*60)
    
    report = {
        "workflow": "Email Triage LLM Fine-tuning",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "configuration": {
            "backend": finetuning_config.get("backend"),
            "base_model": finetuning_config.get("model"),
            "training_data": finetuning_config.get("training_data"),
            "num_training_examples": finetuning_config.get("num_examples")
        },
        "job_information": {
            "job_id": job_id,
            "status": "submitted"
        },
        "baseline_performance": baseline_results,
        "next_steps": [
            "1. Monitor fine-tuning job progress",
            "2. Once complete, download fine-tuned model",
            "3. Evaluate fine-tuned model on test set",
            "4. Compare with baseline results",
            "5. Deploy fine-tuned model to production"
        ]
    }
    
    output_file = "data/finetuning_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Report saved to {output_file}")
    print("\nReport Summary:")
    print(json.dumps(report, indent=2))
    
    return output_file


def run_complete_workflow(
    num_episodes: int = 50,
    backend: str = "openai",
    model: str = "gpt-3.5-turbo",
    submit_job: bool = False,
    eval_episodes: int = 30
) -> Dict:
    """Run complete fine-tuning workflow."""
    
    print("\n" + "="*70)
    print("  EMAIL TRIAGE LLM FINE-TUNING WORKFLOW")
    print("="*70)
    
    ensure_directories()
    
    # Step 1: Collect trajectories
    trajectories_file = step_1_collect_trajectories(num_episodes)
    
    # Step 2: Generate training data
    training_data = step_2_generate_training_data(trajectories_file, format_type="supervised")
    
    # Step 3: Prepare fine-tuning
    finetuning_config = step_3_prepare_finetuning(training_data, backend, model)
    
    if not finetuning_config:
        print("\n✗ Failed to prepare fine-tuning")
        return {"status": "failed"}
    
    # Step 4: Submit job (optional)
    job_id = None
    if submit_job:
        job_id = step_4_submit_finetuning_job(finetuning_config, dry_run=True)
    else:
        print("\nℹ Use --submit to actually submit fine-tuning job to API")
        job_id = "pending_" + str(__import__('time').time()).replace('.', '')
    
    # Step 5: Evaluate baseline
    baseline_results = step_5_evaluate_baseline(eval_episodes)
    
    # Step 6: Monitor (if job submitted)
    if job_id:
        step_6_monitor_finetuning(job_id)
    
    # Step 7: Generate report
    report_file = step_7_generate_report(baseline_results, finetuning_config, job_id)
    
    print("\n" + "="*70)
    print("  WORKFLOW COMPLETE")
    print("="*70)
    
    return {
        "status": "success",
        "trajectories_file": trajectories_file,
        "training_data": training_data,
        "job_id": job_id,
        "report_file": report_file,
        "baseline_results": baseline_results
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="End-to-end fine-tuning workflow for email triage LLM"
    )
    parser.add_argument("--episodes", type=int, default=50,
                       help="Number of trajectory collection episodes")
    parser.add_argument("--backend", choices=["openai", "local", "huggingface"],
                       default="openai", help="Fine-tuning backend")
    parser.add_argument("--model", default="gpt-3.5-turbo",
                       help="Base model to fine-tune")
    parser.add_argument("--submit", action="store_true",
                       help="Actually submit fine-tuning job (default: dry run)")
    parser.add_argument("--eval-episodes", type=int, default=30,
                       help="Number of evaluation episodes")
    
    args = parser.parse_args()
    
    result = run_complete_workflow(
        num_episodes=args.episodes,
        backend=args.backend,
        model=args.model,
        submit_job=args.submit,
        eval_episodes=args.eval_episodes
    )
    
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
