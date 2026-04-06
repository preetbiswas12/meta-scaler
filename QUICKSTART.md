# Quick Start Guide

## Installation

```bash
# Clone or extract repository
cd openenv_test_generation

# Install dependencies
pip install -r requirements.txt
```

## Run Locally

### Windows
```batch
run_local.bat test              # Run tests
run_local.bat demo              # Run interactive demo  
run_local.bat inference         # Run all tasks
run_local.bat easy              # Run easy task only
```

### Linux/macOS
```bash
chmod +x run_local.sh
./run_local.sh test             # Run tests
./run_local.sh demo             # Run interactive demo
./run_local.sh inference        # Run all tasks
```

## Use in Code

```python
from src.environment import CodeTestGenerationEnv

# Create environment
env = CodeTestGenerationEnv()

# Start episode
state = env.reset("easy")

# Generate tests (e.g., from LLM)
generated_tests = """
def test_add():
    assert add(2, 3) == 5
"""

# Step in environment
state, reward, done, info = env.step(generated_tests)

# Check results
print(f"Score: {state['score']}")
print(f"Reward: {reward}")
```

## Run with API

### OpenAI
```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-3.5-turbo"
export OPENAI_API_KEY="sk-..."
python inference.py --task all --use-api
```

### Hugging Face
```bash
export API_BASE_URL="https://api-inference.huggingface.co/models/<model-id>/v1"
export MODEL_NAME="model-id"
export HF_TOKEN="hf_..."
python inference.py --task all --use-api
```

## Docker

```bash
# Build
docker build -t openenv-test-generation .

# Run
docker run -e API_BASE_URL="..." -e MODEL_NAME="..." openenv-test-generation

# With docker-compose
docker-compose up
```

## Output Format

All output follows structured logging:
```
[START] episode_id=<id> task=<task> timestamp=<time>
[STEP] step=<n> reward=<float> score=<float> ...
[END] episode_id=<id> task=<task> steps=<n> final_score=<float> ...
```

## Tasks

- **easy**: Simple addition function (4 tests)
- **medium**: Email validation with edge cases (8 tests)
- **hard**: Cache with TTL system (12 tests)

## Scoring

- **0.0-1.0**: Final episode score based on test quality
- **-1.0 to 1.0**: Step reward for model feedback

## Next Steps

See [README.md](README.md) for complete documentation.
