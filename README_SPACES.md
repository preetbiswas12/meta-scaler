---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# Email Triage - OpenEnv Environment

Production-ready OpenEnv environment for automated email triage using LLMs. Implements the complete OpenEnv specification with deterministic grading, fine-grained rewards, and OpenAI-compatible API integration.

## Quick Start

```bash
# Health check
curl https://preetbiswas121106-email-triage-env.hf.space/health

# Reset environment (start new episode)
curl -X POST https://preetbiswas121106-email-triage-env.hf.space/reset?task_id=easy

# Execute action
curl -X POST https://preetbiswas121106-email-triage-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_123", "action": {"action_type": "classify", "target_category": "newsletter", "confidence": 0.95}}'
```

## Overview

**Task**: Intelligently triage emails with multi-step reasoning:
- Classify email type
- Set priority level  
- Draft reply (if needed)
- Escalate (if urgent)
- Archive

**Difficulty Levels**:
- **Easy** (3 steps): Newsletter, sales inquiry, transactional
- **Medium** (4 steps): Performance issues, financial escalation, ambiguous requests
- **Hard** (5 steps): Legal compliance, unconfirmed threats, critical incidents

**Real-World Variants**: 10 messy email scenarios including:
- Ambiguous intent (unclear classification)
- Conflicting signals (urgent but low priority)
- Multi-action chains (classify → investigate → escalate)

## OpenEnv Specification

### Core APIs

```python
# Reset environment
state = env.reset(task_id="easy")  # or "medium", "hard"

# Execute one step
state, reward, done, info = env.step(action)

# Get current state
current_state = env.state()
```

### Reward & Score

- **Reward bounds**: [-0.10, 1.0]
- **Score bounds**: [0.0, 1.0]
- **Out-of-sequence penalty**: -0.10
- **Ambiguity bonus**: +0.05 for conservative approaches on ambiguous emails

### Deterministic Grading

Multi-step workflow rewards:
- Step 1 (Classify): 0.33 weight
- Step 2 (Prioritize): 0.33 weight  
- Step 3 (Reply/Escalate): 0.34 weight
- Confidence multiplier: 0.05–1.0 based on confidence [0.0–1.0]

## Baseline Performance

| Task | Easy | Medium | Hard |
|------|------|--------|------|
| Baseline Score | 0.72 | 0.80 | 0.86 |
| Steps Required | 3 | 4 | 5 |
| Variants | 3 | 4 | 3 |

## Environment Variables

```bash
API_BASE_URL=https://api.openai.com/v1        # LLM API endpoint
MODEL_NAME=gpt-3.5-turbo                       # Model identifier
HF_TOKEN=hf_xxxxx                              # Hugging Face token
```

## API Reference

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0"
}
```

### POST /reset
Initialize new environment episode.

**Query Parameters:**
- `task_id`: "easy" | "medium" | "hard"

**Response:**
```json
{
  "task_id": "easy",
  "episode_id": "uuid",
  "step": 0,
  "max_steps": 3,
  "current_email": {...},
  "score": 0.0,
  "done": false,
  "reward": 0.0,
  "ground_truth": {...}
}
```

### POST /step
Execute one action in the environment.

**Body:**
```json
{
  "session_id": "uuid",
  "action": {
    "action_type": "classify",
    "target_category": "newsletter",
    "confidence": 0.95
  }
}
```

**Response:**
```json
{
  "state": {...},
  "reward": 0.33,
  "done": false,
  "info": {
    "quality": "perfect",
    "is_correct": true,
    "confidence": 0.95
  }
}
```

### GET /state
Get current environment state.

**Query Parameters:**
- `session_id`: Episode session ID

**Response:** Current state object

### GET /sessions
List all active sessions.

**Response:**
```json
{
  "sessions": ["uuid1", "uuid2", ...],
  "count": 2
}
```

### DELETE /sessions/{session_id}
Delete session.

## Evaluation Criteria

### Phase 1: Automated Validation
- ✅ HF Space deploys
- ✅ OpenEnv spec compliance (YAML, schemas, endpoints)
- ✅ Dockerfile builds
- ✅ Baseline reproduces
- ✅ 3+ tasks with graders

### Phase 2: Agentic Evaluation
- Baseline agent re-run
- Standard LLM agent (Nemotron 3 Super) evaluation
- Score variance check

### Phase 3: Human Review
- Real-world utility assessment
- Creativity evaluation
- Security/exploit checks

## Disqualification Criteria

- ❌ Environment does not deploy or respond
- ❌ Plagiarized/trivial modifications
- ❌ Graders always return same score
- ❌ No baseline inference script

## Configuration

See `config/openenv.yaml` for full specification:
- Environment class: `src.environment:EmailTriageEnv`
- Task definitions: easy, medium, hard
- Resource requirements: 2 vCPU, 8GB RAM
- Runtime limit: 20 minutes

## Testing

```bash
# Unit tests
pytest -v

# Integration tests
python main.py

# Validator checks (local)
python validator.py

# Validator checks (with deployed space)
export HF_SPACE_URL=https://preetbiswas121106-email-triage-env.hf.space
python validator.py
```

## Submission Checklist

- [x] Environment specification (openenv.yaml)
- [x] Pydantic models (EmailSchema, ActionSchema, StateSchema)
- [x] Core APIs (reset, step, state)
- [x] Deterministic graders
- [x] Flask HTTP API (app.py)
- [x] Docker containerization
- [x] Inference script (inference.py)
- [x] Baseline testing (main.py)
- [x] Validator script
- [x] 40/40 tests passing
- [x] HF Space deployed

---

**For full documentation, see**: [Project README](./README.md)

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
