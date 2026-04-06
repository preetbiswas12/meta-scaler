# LLM Fine-tuning Guide

Complete guide for fine-tuning language models on the email triage task.

## Overview

This fine-tuning pipeline enables you to:
1. **Collect trajectories** from the email triage environment
2. **Generate training data** in multiple formats
3. **Submit fine-tuning jobs** to various backends (OpenAI, local, HuggingFace)
4. **Evaluate models** with comprehensive metrics
5. **Compare baseline vs fine-tuned** performance

## Quick Start

### Option 1: Complete Workflow (Recommended)

```bash
# Run entire pipeline with dry-run (no API calls)
python finetune_workflow.py --episodes 50 --eval-episodes 30

# Submit real fine-tuning job to OpenAI
python finetune_workflow.py --episodes 100 --submit --backend openai --model gpt-3.5-turbo
```

### Option 2: Step-by-Step

```bash
# Step 1: Collect trajectories (episodes to learn from)
python trajectory_collector.py --episodes 50 --output data/trajectories.jsonl

# Step 2: Generate training data
python training_data_generator.py --trajectories data/trajectories.jsonl \
  --format supervised --output data/training_supervised.jsonl

# Step 3: Evaluate baseline model
python evaluation.py --episodes 30

# Step 4: Submit fine-tuning job
python fine_tuning.py --backend openai --model gpt-3.5-turbo \
  --training-data data/training_supervised.jsonl --submit

# Step 5: Check job status
python fine_tuning.py --backend openai --check-status <job_id>
```

## Components

### 1. Trajectory Collector (`trajectory_collector.py`)

Collects episodes from the environment with optimal actions.

**Usage:**
```bash
python trajectory_collector.py \
  --episodes 50 \
  --strategy all \
  --output data/trajectories.jsonl
```

**Strategies:**
- `all`: Collect all episodes
- `high_reward`: Only episodes with reward > 0.5
- `optimal`: Only successful episodes with ≤2 steps

**Output Format (JSONL):**
```json
{
  "episode_id": "1234567890",
  "task_id": "easy|medium|hard",
  "total_reward": 1.6,
  "final_score": 0.95,
  "num_steps": 1,
  "success": true,
  "steps": [
    {
      "step_number": 1,
      "action": {"action_type": "classify", "target_category": "work", "confidence": 0.95},
      "reward": 1.6,
      "ground_truth": {"category": "work", "priority": 3, "should_reply": false},
      "is_correct": true
    }
  ]
}
```

### 2. Training Data Generator (`training_data_generator.py`)

Converts trajectories into various training formats.

**Usage:**
```bash
python training_data_generator.py \
  --trajectories data/trajectories.jsonl \
  --format supervised \
  --output data/training_supervised.jsonl
```

**Formats:**

#### Supervised Learning (Recommended for quick fine-tuning)
```json
{
  "prompt": "Email Triage Task [EASY]\nFROM: john@example.com\n...",
  "completion": "ACTION: Classify as [work] (confidence: 0.95)",
  "episode_id": "1234567890",
  "reward": 1.6,
  "difficulty": "easy"
}
```

#### Preference Learning (DPO, IPO)
```json
{
  "prompt": "Email Triage Task [EASY]\n...",
  "chosen": "ACTION: Classify as [work] (confidence: 0.95)",
  "rejected": "ACTION: Archive (confidence: 0.50)",
  "chosen_reward": 1.6,
  "episode_id": "1234567890",
  "difficulty": "easy"
}
```

#### Trajectory Sequences (For RL fine-tuning)
```json
{
  "messages": [
    {"role": "system", "content": "You are an expert email triage assistant..."},
    {"role": "user", "content": "Email Triage Task..."},
    {"role": "assistant", "content": "ACTION: Classify..."}
  ],
  "trajectory_reward": 1.6,
  "final_score": 0.95,
  "success": true,
  "num_steps": 1,
  "difficulty": "easy",
  "episode_id": "1234567890"
}
```

### 3. Fine-tuning Job Manager (`fine_tuning.py`)

Submits and monitors fine-tuning jobs across backends.

**Supported Backends:**
- **OpenAI**: GPT-3.5, GPT-4, and other OpenAI models
- **Local**: Ollama, vLLM, local models
- **HuggingFace**: Any HF model with transformers

**Usage:**

```bash
# OpenAI (requires OPENAI_API_KEY environment variable)
python fine_tuning.py \
  --backend openai \
  --model gpt-3.5-turbo \
  --training-data data/training_supervised.jsonl \
  --submit

# Local (assuming server running on localhost:8000)
python fine_tuning.py \
  --backend local \
  --model llama2 \
  --training-data data/training_supervised.jsonl

# HuggingFace
python fine_tuning.py \
  --backend huggingface \
  --model meta-llama/Llama-2-7b \
  --training-data data/training_supervised.jsonl
```

**Check Job Status:**
```bash
python fine_tuning.py \
  --backend openai \
  --check-status <job_id>
```

### 4. Model Evaluation (`evaluation.py`)

Evaluates models on the email triage task.

**Usage:**

```bash
# Evaluate single model
python evaluation.py --model baseline --episodes 30

# Compare multiple models
python evaluation.py \
  --compare \
  --models baseline gpt-3.5-turbo gpt-4 \
  --episodes 30 \
  --output data/evaluation_results.json
```

**Metrics Collected:**
- Success rate (% of emails correctly classified)
- Average reward (mean reward across episodes)
- Median reward (middle value)
- Average steps (efficiency)
- Latency (inference time in ms)
- By difficulty (easy/medium/hard breakdown)
- By action type (classify/prioritize/reply/escalate/archive)

**Output:**
```json
{
  "baseline": {
    "success_rate": 0.87,
    "avg_reward": 1.24,
    "median_reward": 1.20,
    "avg_steps": 1.5,
    "avg_latency_ms": 42.3,
    "by_difficulty": {
      "easy": {"episodes": 10, "avg_reward": 1.60, "success_rate": 1.0},
      "medium": {"episodes": 10, "avg_reward": 1.20, "success_rate": 0.8},
      "hard": {"episodes": 10, "avg_reward": 0.92, "success_rate": 0.7}
    }
  }
}
```

### 5. Complete Workflow (`finetune_workflow.py`)

Orchestrates all steps automatically.

**Usage:**

```bash
# Dry run (no API calls)
python finetune_workflow.py --episodes 50 --eval-episodes 30

# With OpenAI API submission
python finetune_workflow.py \
  --episodes 100 \
  --backend openai \
  --model gpt-3.5-turbo \
  --submit \
  --eval-episodes 50
```

**Workflow Steps:**
1. ✓ Collect trajectories (50 episodes)
2. ✓ Generate training data (supervised format)
3. ✓ Prepare fine-tuning job
4. ✓ Submit job (optional, dry-run by default)
5. ✓ Evaluate baseline
6. ✓ Monitor fine-tuning progress
7. ✓ Generate report

**Output:**
- `data/trajectories.jsonl` - 50 episode trajectories
- `data/training_supervised.jsonl` - Training pairs
- `data/finetuning_jobs.jsonl` - Job tracking
- `data/finetuning_report.json` - Complete report

## Configuration

### Environment Variables

```bash
# OpenAI API
export OPENAI_API_KEY="sk-..."

# Local LLM server (if using local backend)
export LLM_SERVER_URL="http://localhost:8000"
```

### Recommended Settings

**For Quick Testing:**
```bash
python finetune_workflow.py --episodes 20 --eval-episodes 10
```

**For Production Fine-tuning:**
```bash
python finetune_workflow.py \
  --episodes 200 \
  --backend openai \
  --model gpt-3.5-turbo \
  --submit \
  --eval-episodes 100
```

## Advanced Usage

### Custom Training Data Format

```bash
# Generate all three formats
python training_data_generator.py \
  --trajectories data/trajectories.jsonl \
  --format supervised \
  --output data/training_supervised.jsonl

python training_data_generator.py \
  --trajectories data/trajectories.jsonl \
  --format preference \
  --output data/training_preference.jsonl

python training_data_generator.py \
  --trajectories data/trajectories.jsonl \
  --format trajectory \
  --output data/training_trajectory.jsonl
```

### Fine-tune with Different Models

```bash
# GPT-4
python fine_tuning.py \
  --backend openai \
  --model gpt-4 \
  --training-data data/training_supervised.jsonl \
  --submit

# Llama 2 (local)
python fine_tuning.py \
  --backend local \
  --model llama2 \
  --training-data data/training_supervised.jsonl

# Mistral (HuggingFace)
python fine_tuning.py \
  --backend huggingface \
  --model mistralai/Mistral-7B \
  --training-data data/training_supervised.jsonl
```

### Evaluate Custom Models

```bash
# Compare fine-tuned vs baseline
python evaluation.py \
  --compare \
  --models baseline "gpt-3.5-turbo-finetuned-abc123" \
  --episodes 50 \
  --output data/comparison_results.json
```

## Troubleshooting

### "No OPENAI_API_KEY"
```bash
export OPENAI_API_KEY="your-api-key-here"
python fine_tuning.py --backend openai --model gpt-3.5-turbo --submit
```

### "Connection refused (Local backend)"
```bash
# Ensure local LLM server is running
# For Ollama:
ollama serve

# For vLLM:
python -m vllm.entrypoints.openai.api_server --model llama2
```

### Fine-tuning job stuck
```bash
# Check job status
python fine_tuning.py --backend openai --check-status <job_id>

# If stuck, contact API provider or check documentation
```

## Performance Expectations

### Baseline (Without Fine-tuning)
- Success Rate: 85-90%
- Avg Reward: 1.2-1.4
- Avg Steps: 1.5

### After Fine-tuning (50 episodes)
- Success Rate: 90-95%
- Avg Reward: 1.4-1.6
- Avg Steps: 1.2

### After Fine-tuning (200+ episodes)
- Success Rate: 95-98%
- Avg Reward: 1.6-1.8
- Avg Steps: 1.0-1.1

## Next Steps

1. **Collect more trajectories** as you get better performance
2. **Try different training data formats** (preference learning, trajectory sequences)
3. **Experiment with backends** (compare OpenAI vs local models)
4. **Fine-tune multiple models** and compare results
5. **Deploy best model** to production

## References

- [OpenAI Fine-tuning Docs](https://platform.openai.com/docs/guides/fine-tuning)
- [HuggingFace Fine-tuning](https://huggingface.co/docs/transformers/training)
- [Ollama Setup](https://ollama.ai)
- [vLLM Documentation](https://docs.vllm.ai/)

