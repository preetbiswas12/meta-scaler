# Project Structure

```
openenv_test_generation/
│
├── config/                          # Configuration files
│   └── openenv.yaml                # OpenEnv v1.0 specification
│
├── src/                            # Source code
│   ├── __init__.py                 # Package initialization
│   ├── environment.py              # CodeTestGenerationEnv (step/reset/state)
│   ├── graders.py                  # DeterministicGrader for scoring
│   └── tasks.py                    # Task definitions and utilities
│
├── data/                           # Task metadata
│   └── task_metadata.yaml
│
├── inference.py                    # Main inference script
│   ├── OpenAIClient                # OpenAI-compatible API client
│   ├── run_inference_episode()     # Episode runner
│   └── main()                      # CLI entry point
│
├── main.py                         # Alternative entry point
│   ├── Commands: demo, tasks, inference
│   └── Task management utilities
│
├── test_integration.py             # Integration tests (11 tests)
├── validate.py                     # Pre-deployment validation
│
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image for Spaces
├── docker-compose.yml              # Local dev environment
│
├── run_local.sh                    # Linux/macOS quick start
├── run_local.bat                   # Windows quick start
│
├── .env.example                    # Environment template
├── .gitignore                      # Git configuration
│
├── README.md                       # Complete documentation
├── QUICKSTART.md                   # Quick start guide
└── PROJECT_STRUCTURE.md            # This file
```

## File Descriptions

### Core Environment (`src/`)

- **environment.py** (350+ lines)
  - `CodeTestGenerationEnv` class implementing OpenEnv spec
  - `reset(task_id)` - Initialize episode
  - `step(action)` - Execute one step
  - `state()` - Get current state (deterministic)
  - `StateSchema` Pydantic model for type safety
  - Supports 3 tasks: easy, medium, hard

- **graders.py** (400+ lines)
  - `DeterministicGrader` - Deterministic scoring system
  - Scores tests on 5 components (15% weighting):
    1. Syntax validity (15%)
    2. Import correctness (10%)
    3. Test count (25%)
    4. Edge case coverage (30%)
    5. Assertion quality (20%)
  - `GradingMetrics` dataclass for structured scoring
  - Reward function with partial progress signals (-1.0 to 1.0)

- **tasks.py** (130+ lines)
  - Task definitions (Easy, Medium, Hard)
  - Task utilities and helpers
  - TASKS_DATABASE for centralized management

### Inference & Scripts

- **inference.py** (400+ lines)
  - `OpenAIClient` using environment variables:
    - `API_BASE_URL` - API endpoint
    - `MODEL_NAME` - Model identifier
    - `HF_TOKEN` (or `OPENAI_API_KEY`) - API key
  - `run_inference_episode()` - Run complete episode
  - Logging in [START]/[STEP]/[END] format
  - Mock test fallback when API unavailable
  - CLI with `--task`, `--steps`, `--episodes`, `--use-api`

- **main.py** (130+ lines)
  - Alternative entry point with 3 commands:
    - `demo` - Interactive demo
    - `tasks` - Show all tasks
    - `inference` - Run inference pipeline

### Testing & Validation

- **test_integration.py** (280+ lines)
  - 11 comprehensive integration tests
  - 100% pass rate (tests all features)
  - Tests: initialization, reset, step, deterministic grading, episodes

- **validate.py** (220+ lines)
  - 8 pre-deployment validation checks
  - Verifies files, imports, functionality, logging
  - Used before Docker deployment

### Configuration

- **config/openenv.yaml** (50+ lines)
  - OpenEnv v1.0 specification
  - Defines tasks, state schema, deployment requirements
  - CPU: 2 vCPU, Memory: 8GB, Timeout: 20min

- **.env.example**
  - Environment variable template
  - API credentials setup guide

### Container & Deployment

- **Dockerfile** (25+ lines)
  - Python 3.11 slim image
  - Installs dependencies
  - Health checks included
  - Ready for HF Spaces

- **docker-compose.yml** (20+ lines)
  - Local development environment
  - Mounts for live code editing
  - Easy environment variable setup

### Quick Start Scripts

- **run_local.sh** (Linux/macOS)
  - Commands: demo, tasks, test, inference, easy, medium, hard
  - chmod +x required before use

- **run_local.bat** (Windows)
  - Same commands as shell script
  - Direct execution, no chmod needed

## Data Flow

```
User Input (Task ID)
    ↓
environment.reset(task_id)
    ↓
StateSchema (Pydantic model)
    ↓
Agent generates tests
    ↓
environment.step(generated_tests)
    ↓
DeterministicGrader.grade()
    ↓
Score & Reward (-1.0 to 1.0)
    ↓
Output with [START]/[STEP]/[END] logs
```

## Key Features

✓ OpenEnv v1.0 Specification Compliant
✓ Deterministic Grading (reproducible scores)
✓ Pydantic Type Safety (StateSchema)
✓ OpenAI-compatible API Integration
✓ 3 Difficulty Levels (Easy/Medium/Hard)
✓ Structured Logging Format
✓ Mock Test Support (no API needed)
✓ Docker Ready (HF Spaces compatible)
✓ 11 Integration Tests (100% pass)
✓ Pre-deployment Validation
✓ Comprehensive Documentation

## Resource Requirements

- **Runtime**: 5-20 minutes per full run
- **CPU**: 2 vCPU minimum
- **RAM**: 8GB minimum
- **Disk**: 2GB for Docker image
- **Python**: 3.11+

## Testing

```bash
# Run all tests
python test_integration.py

# Validate before deployment
python validate.py

# Run demo
python main.py demo

# Run all tasks
python inference.py --task all --episodes 1
```

## Deployment

```bash
# Docker build
docker build -t openenv-test-generation .

# Docker run with environment
docker run -e API_BASE_URL="https://api.openai.com/v1" \
           -e MODEL_NAME="gpt-3.5-turbo" \
           -e HF_TOKEN="hf_..." \
           openenv-test-generation

# Docker Compose
docker-compose up

# HF Spaces: Upload files, set env vars in secrets, done!
```

---

**Total Lines of Code**: 1500+
**Production Ready**: Yes
**Tested**: Yes (11/11 tests passing)
**Validated**: Yes (8/8 checks passing)
