# Email Triage - OpenEnv Environment

Production-ready OpenEnv environment for automated email triage using LLMs. Implements the complete OpenEnv specification with deterministic grading, fine-grained rewards, and OpenAI-compatible API integration.

## Overview

**Task**: Intelligently triage emails with classification, prioritization, reply drafting, escalation, and archival.

**Difficulty Levels**:
- **Easy** (3 emails): Basic emails (sales inquiry, newsletter, transactional)
- **Medium** (4 emails): Phishing, urgent technical threads, HR notices, spam
- **Hard** (3 emails): Subtle spam, critical escalations, strategic discussions

**Grading**: Deterministic rule-based scoring with:
- Classification accuracy (correct category = 1.0 base, wrong = -0.5)
- Priority assignment (exact = 0.8, off-by-1 = 0.3, worse = -0.2*diff)
- Reply quality (0.5-1.0 based on length, professionalism, keyword coverage)
- Escalation judgment (correct = 0.9, correct no reason = 0.6, incorrect = -0.2)
- Efficiency bonus (early correct classification = +0.3)

## OpenEnv Specification Compliance

### Core APIs

```python
# Reset environment and start new episode
state = env.reset(task_id="easy")  # or "medium", "hard"

# Execute one step with email triage action
state, reward, done, info = env.step(action)

# Get current state (deterministic)
current_state = env.state()
```

### State Schema (Pydantic)

```python
class StateSchema(BaseModel):
    task_id: str                    # Unique task identifier
    episode_id: str                 # Episode identifier
    difficulty: str                 # "easy" | "medium" | "hard"
    step: int                       # Current step (0-N)
    max_steps: int                  # Max steps (3, 4, or 5)
    current_email: EmailSchema      # Current email to triage
    actions_taken: List[Dict]       # History of actions with rewards
    score: float                    # Cumulative score
    done: bool                      # Episode completion
    reward: float                   # Latest step reward
    ground_truth: Dict              # Classification, priority, should_reply, etc.
```

### Email Schema

```python
class EmailSchema(BaseModel):
    email_id: str                   # Unique email ID
    sender: str                     # Sender email/name
    subject: str                    # Email subject
    body: str                       # Email body content
    timestamp: str                  # ISO timestamp
    is_spam: bool                   # Spam flag
    urgency_indicators: List[str]   # Urgency keywords (e.g., "URGENT")
```

### Action Schema

```python
class ActionSchema(BaseModel):
    action_type: str                # "classify" | "prioritize" | "reply" | "escalate" | "archive"
    target_category: str            # Category (for classify)
    priority_level: int             # Priority 1-5 (for prioritize)
    reply_draft: str                # Reply text (for reply)
    escalation_reason: str          # Reason for escalation
    confidence: float               # Confidence 0.0-1.0
```

### Configuration (openenv.yaml)

```yaml
version: "1.0"
name: "email_triage"
environment:
  entry_point: "src.environment:EmailTriageEnv"
tasks:
  - id: "easy"    # 3 steps, 3 emails
  - id: "medium"  # 4 steps, 4 emails
  - id: "hard"    # 5 steps, 3 emails
deployment:
  resources:
    cpu: "2"
    memory: "8Gi"
    timeout: 600
```

## Installation

```bash
# Clone or download repository
cd openenv_email_triage

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Local Testing

```bash
# Run single easy task without API
python inference.py --task easy --steps 3

# Run all tasks
python inference.py --task all --episodes 1

# With OpenAI API
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-3.5-turbo"
export OPENAI_API_KEY="sk-..."
python inference.py --task all --use-api --episodes 2
```

### With Custom API (e.g., vLLM, Ollama)

```bash
export API_BASE_URL="http://localhost:8000/v1"
export MODEL_NAME="meta-llama/Llama-2-7b-chat"
export HF_TOKEN="hf_..."
python inference.py --task medium --use-api --steps 5
```

### With Hugging Face Spaces

```bash
# Set environment variables in Spaces secrets:
# - API_BASE_URL: Your inference API endpoint
# - MODEL_NAME: Model identifier
# - HF_TOKEN: Hugging Face token

# Docker will auto-run inference.py
```

### Direct API Usage

```python
from src.environment import CodeTestGenerationEnv
from src.graders import DeterministicGrader

env = CodeTestGenerationEnv()
state = env.reset("medium")

generated_tests = """
def test_email_valid():
    from main import validate_email
    assert validate_email("user@example.com") == True
"""

state, reward, done, info = env.step(generated_tests)
print(f"Score: {state['score']}")
print(f"Reward: {reward}")
print(f"Grading: {info['grading_details']}")
```

## Logging Format

All output follows structured logging format:

```
[START] episode_id=<uuid> task=<task_id> timestamp=<ISO8601>
[STEP] step=<n> reward=<float> score=<float> tests=<int> assertions=<int> edge_cases=<int> done=<bool>
[STEP] ...
[END] episode_id=<uuid> task=<task_id> steps=<n> final_score=<float> total_reward=<float> timestamp=<ISO8601>
```

## Project Structure

```
openenv_test_generation/
├── config/
│   └── openenv.yaml                 # OpenEnv specification
├── src/
│   ├── __init__.py
│   ├── environment.py               # CodeTestGenerationEnv (step/reset/state)
│   └── graders.py                   # DeterministicGrader + metrics
├── data/                            # (Optional) for additional test data
├── inference.py                     # Main inference script
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container for Spaces deployment
└── README.md                        # This file
```

## Grading System

### Score Calculation (0.0-1.0)

1. **Syntax Validation** (15%): Valid Python syntax required
2. **Import Checking** (10%): Only standard library/allowed packages
3. **Test Count** (25%): Penalizes too few/many tests
4. **Edge Case Coverage** (30%): Detects edge case keywords
5. **Assertion Quality** (20%): Assertions per test ratio

### Reward Function (-1.0 to 1.0)

- Base reward: `score * 2.0 - 1.0`
- Bonus: +0.50 for valid test structure, coverage, no duplicates
- Penalty: -0.40 for syntax errors, -0.50 for zero tests

Provides partial progress signals for model feedback.

## Task Descriptions

### Easy: Simple Function Testing

```python
def add(a, b):
    """Add two numbers."""
    return a + b
```

- Expected tests: 4
- Edge cases: positive, negative, zero
- Max steps: 5

### Medium: Edge Case Coverage

```python
def validate_email(email):
    """Validate email format."""
    # Complex logic with multiple conditions
```

- Expected tests: 8
- Edge cases: no @, no domain, multiple @, empty, non-string
- Max steps: 8

### Hard: Complex System Testing

```python
class CacheWithTTL:
    """Cache with time-to-live expiration."""
    # State management, time-dependent behavior
```

- Expected tests: 12
- Edge cases: expiration, concurrent access, type variations
- Max steps: 10

## Resource Requirements

**Minimum**:
- CPU: 2 vCPU
- Memory: 8 GB RAM
- Disk: 2 GB

**Typical Run Time**:
- Single task: ~2-5 minutes
- All tasks (no API): ~15 minutes
- All tasks (with API): ~20 minutes

**Docker Image Size**: ~300 MB

## Environment Variables

```bash
# Required for API inference
API_BASE_URL="https://api.openai.com/v1"           # API endpoint
MODEL_NAME="gpt-3.5-turbo"                         # Model identifier
HF_TOKEN="hf_..."                                  # Hugging Face token (or OPENAI_API_KEY)

# Optional
PYTHONUNBUFFERED=1                                 # Real-time logging
```

## Deployment to Hugging Face Spaces

1. Create new Space on Hugging Face
2. Select "Docker" as runtime
3. Upload repository files
4. Add environment variables in Space Settings:
   - `API_BASE_URL`
   - `MODEL_NAME`
   - `HF_TOKEN`
5. Space automatically builds and runs

Docker container implements health checks and will expose logs.

## Testing

### Local Unit Test

```bash
# Test environment setup
python -c "from src.environment import CodeTestGenerationEnv; env = CodeTestGenerationEnv(); s = env.reset('easy'); print('OK')"

# Test grading
python src/graders.py

# Test inference (mock)
python inference.py --task easy
```

### Integration Test

```bash
# Full episode without API
python inference.py --task all --episodes 1 --steps 3

# Expected output: [START]...[STEP]...[END] logs with scores
```

## Reproducibility

- Deterministic grading (no randomness in scoring)
- Fixed TASK_DATABASE with identical code snippets
- Seeded random operations not used
- Mock tests identical across runs
- All metrics derived from code properties

## Extensibility

### Add Custom Tasks

Edit `src/environment.py` TASK_DATABASE:

```python
TASK_DATABASE = {
    "custom": {
        "code": "def your_function(): pass",
        "function_name": "your_function",
        "description": "...",
        "edge_cases": [...],
        "expected_tests": 4,
    }
}
```

### Customize Grading

Modify `src/graders.py`:
- Change weights in `DeterministicGrader.grade()`
- Add new metrics in `_extract_metrics()`
- Adjust reward calculation in `_calculate_reward()`

## API Compatibility

OpenAI-compatible API client supports:
- OpenAI (GPT-3.5, GPT-4)
- Azure OpenAI
- vLLM
- Ollama
- Hugging Face Inference API
- Any Chat Completion v1 endpoint

## Status & Completion

Within the first run:
- All three tasks initialize
- Deterministic grading produces consistent scores
- Mock tests used if no API provided
- Logs follow [START]/[STEP]/[END] format
- Episode completes with final score

## License

MIT

## Support

For issues or questions about OpenEnv specification:
- OpenEnv Docs: https://github.com/openenv/specification
- This implementation provides full compliance with v1.0 spec

---

**Last Updated**: 2026-04-06  
**OpenEnv Version**: 1.0  
**Python**: 3.11+
