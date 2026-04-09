#!/usr/bin/env python3
"""Check variance of scores and rewards across multiple episodes."""
import subprocess
import json
import re
from statistics import mean, stdev, variance

def extract_scores_from_output(output: str) -> list:
    """Extract final scores from inference output."""
    scores = []
    for line in output.split('\n'):
        if '[END]' in line:
            match = re.search(r'score=([\d.]+)', line)
            if match:
                scores.append(float(match.group(1)))
    return scores

def run_test(task: str, episodes: int) -> list:
    """Run inference and extract scores."""
    cmd = f"python inference.py --task {task} --episodes {episodes}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    return extract_scores_from_output(output)

# Test each task with 10 episodes
tasks = ["easy", "medium", "hard"]
for task in tasks:
    print(f"\n{'='*60}")
    print(f"Task: {task.upper()} (10 episodes)")
    print('='*60)
    
    scores = run_test(task, 10)
    
    if scores:
        print(f"Scores: {[f'{s:.2f}' for s in scores]}")
        print(f"\nStatistics:")
        print(f"  Min:      {min(scores):.4f}")
        print(f"  Max:      {max(scores):.4f}")
        print(f"  Mean:     {mean(scores):.4f}")
        print(f"  Std Dev:  {stdev(scores):.4f}" if len(scores) > 1 else "")
        print(f"  Variance: {variance(scores):.6f}" if len(scores) > 1 else "")
        
        # Check bounds
        in_bounds = all(0.0 < s < 1.0 for s in scores)
        print(f"\n✓ All scores in (0,1): {in_bounds}")
        
        if not in_bounds:
            out_of_bounds = [s for s in scores if not (0.0 < s < 1.0)]
            print(f"  ✗ Out of bounds: {out_of_bounds}")
    else:
        print("No scores found!")
