# Fine-tuning Quick Reference

## 🚀 Quick Start (5 minutes)

```bash
# 1. Collect trajectories (30 episodes)
python trajectory_collector.py --episodes 30

# 2. Generate training data
python training_data_generator.py --trajectories data/trajectories.jsonl --format supervised

# 3. Evaluate baseline
python evaluation.py --episodes 20
```

**Output:**
- `data/trajectories.jsonl` - 30 episode trajectories
- `data/training_supervised.jsonl` - 30 training pairs
- Baseline metrics: 100% success rate, avg reward 1.6

## 📊 Three Training Data Formats

| Format | Use Case | When |
|--------|----------|------|
| **Supervised** | Standard fine-tuning | Quick & simple |
| **Preference** | Direct preference optimization (DPO) | Better alignment |
| **Trajectory** | Multi-step episode learning | Complex tasks |

```bash
# Generate all three
python training_data_generator.py --format supervised
python training_data_generator.py --format preference
python training_data_generator.py --format trajectory
```

## 🔧 Three Backends

| Backend | Setup | Command |
|---------|-------|---------|
| **OpenAI** | `export OPENAI_API_KEY=sk-...` | `--backend openai --model gpt-3.5-turbo` |
| **Local** | Run Ollama/vLLM | `--backend local --model llama2` |
| **HuggingFace** | Install transformers | `--backend huggingface --model meta-llama/Llama-2-7b` |

## 💡 Common Use Cases

### Case 1: Try OpenAI's GPT-3.5
```bash
export OPENAI_API_KEY="sk-..."
python fine_tuning.py \
  --backend openai \
  --model gpt-3.5-turbo \
  --training-data data/training_supervised.jsonl \
  --submit
```

### Case 2: Fine-tune Locally (Ollama)
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Fine-tune
python fine_tuning.py \
  --backend local \
  --model llama2 \
  --training-data data/training_supervised.jsonl
```

### Case 3: Complete Workflow
```bash
python finetune_workflow.py \
  --episodes 100 \
  --backend openai \
  --model gpt-3.5-turbo \
  --submit \
  --eval-episodes 50
```

### Case 4: Compare Multiple Models
```bash
python evaluation.py \
  --compare \
  --models baseline gpt-3.5-turbo gpt-4 \
  --episodes 30
```

## 📈 Evaluation Metrics

```bash
python evaluation.py --episodes 20
```

Returns:
- ✅ Success rate (% of emails correctly handled)
- 📊 Average reward (mean score)
- 📉 Median reward (middle value)
- ⏱️ Average steps (efficiency)
- 🚀 Latency (inference speed in ms)
- 🎯 By difficulty (easy/medium/hard)
- 🎬 By action type (classify/prioritize/reply/escalate/archive)

## 🔍 Monitoring Fine-tuning

```bash
# Check job status
python fine_tuning.py \
  --backend openai \
  --check-status <job_id>
```

## 📁 File Structure

```
project/
├── trajectory_collector.py          # Collect episodes
├── training_data_generator.py       # Format training data
├── fine_tuning.py                   # Submit fine-tuning jobs
├── evaluation.py                    # Evaluate models
├── finetune_workflow.py             # End-to-end orchestration
├── FINETUNING_GUIDE.md              # Detailed guide
├── FINETUNING_COMPLETE.md           # Summary
└── data/
    ├── trajectories.jsonl           # Episode data
    ├── training_supervised.jsonl    # Supervised pairs
    ├── training_preference.jsonl    # Preference pairs
    └── training_trajectory.jsonl    # Trajectory sequences
```

## ⚡ One-Liners

```bash
# Collect 100 episodes
python trajectory_collector.py --episodes 100

# Generate all training formats
for fmt in supervised preference trajectory; do python training_data_generator.py --format $fmt; done

# Evaluate baseline (30 episodes)
python evaluation.py --episodes 30

# Submit to OpenAI (requires API key)
python fine_tuning.py --backend openai --submit

# Full workflow (dry run)
python finetune_workflow.py --episodes 50

# Compare 3 models
python evaluation.py --compare --models baseline model_a model_b --episodes 30
```

## 🎯 Performance Targets

### Baseline (Optimal Policy)
- Success: 100% ✓
- Reward: 1.6 ✓
- Steps: 1.0 ✓

### After Fine-tuning (50 episodes)
- Success: 90-95%
- Reward: 1.4-1.6
- Steps: 1.2-1.5

### After Fine-tuning (200+ episodes)
- Success: 95-98%
- Reward: 1.6-1.8
- Steps: 1.0-1.1

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `OPENAI_API_KEY not found` | `export OPENAI_API_KEY="sk-..."` |
| Connection refused (local) | Start Ollama: `ollama serve` |
| Out of memory | Use smaller model or batch size |
| `No trainingfile found` | Run `trajectory_collector.py` first |

## 📚 More Information

- Full guide: `FINETUNING_GUIDE.md`
- Summary: `FINETUNING_COMPLETE.md`
- Architecture: See individual `.py` files

## 🎬 Next Steps

1. ✅ Generate training data
   ```bash
   python trajectory_collector.py --episodes 100
   python training_data_generator.py --format supervised
   ```

2. ✅ Evaluate baseline
   ```bash
   python evaluation.py --episodes 30
   ```

3. ✅ Fine-tune model
   ```bash
   export OPENAI_API_KEY="your-key"
   python fine_tuning.py --backend openai --submit
   ```

4. ✅ Compare results
   ```bash
   python evaluation.py --compare --models baseline finetuned
   ```

5. ✅ Deploy winner
   - Use best model in production
   - Monitor performance
   - Collect new data for retraining

---

**Everything is ready! Start with:**
```bash
python trajectory_collector.py --episodes 50
python training_data_generator.py --format supervised
python evaluation.py --episodes 20
```
