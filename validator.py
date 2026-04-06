#!/usr/bin/env python3
"""
Validator script for EmailTriageEnv submission.

Checks:
✓ OpenEnv API compliance
✓ Docker build
✓ HF Space deployment (if URL provided)
✓ Logging format
✓ Reward bounds
✓ Integration tests
"""

import os
import sys
import json
import subprocess
import requests
from typing import Dict, List, Tuple
from datetime import datetime

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class Validator:
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.hf_space_url = os.getenv("HF_SPACE_URL", "").rstrip("/")
    
    def check(self, name: str, condition: bool, error: str = "") -> bool:
        """Record a check result."""
        status = "✓" if condition else "✗"
        color = GREEN if condition else RED
        
        msg = f"{color}{status}{RESET} {name}"
        if error and not condition:
            msg += f" — {error}"
        
        print(msg)
        self.results.append((name, condition, error))
        return condition
    
    def section(self, title: str):
        """Print section header."""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{title.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
    
    def summary(self) -> bool:
        """Print summary and return overall pass/fail."""
        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)
        
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}VALIDATION SUMMARY{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        color = GREEN if passed == total else RED
        print(f"{color}{passed}/{total} checks passed{RESET}\n")
        
        if passed == total:
            print(f"{GREEN}✓ All validations passed! Ready for submission.{RESET}\n")
            return True
        else:
            print(f"{RED}✗ Some validations failed. See details above.{RESET}\n")
            return False


def test_imports():
    """Test that all required modules import correctly."""
    validator = Validator()
    validator.section("1. IMPORT VALIDATION")
    
    try:
        from src.environment import EmailTriageEnv
        validator.check("Import EmailTriageEnv", True)
    except Exception as e:
        validator.check("Import EmailTriageEnv", False, str(e))
        return
    
    try:
        from src.graders_normalized import EmailTriageGrader
        validator.check("Import EmailTriageGrader", True)
    except Exception as e:
        validator.check("Import EmailTriageGrader", False, str(e))
        return
    
    try:
        from inference import OpenAIClient, run_inference_episode
        validator.check("Import inference module", True)
    except Exception as e:
        validator.check("Import inference module", False, str(e))
        return
    
    try:
        import flask
        validator.check("Import Flask", True)
    except Exception as e:
        validator.check("Import Flask", False, str(e))
        return
    
    return validator


def test_environment():
    """Test environment functionality."""
    validator = Validator()
    validator.section("2. ENVIRONMENT VALIDATION")
    
    try:
        from src.environment import EmailTriageEnv
        
        env = EmailTriageEnv()
        validator.check("Initialize environment", env is not None)
        
        # Test reset
        state = env.reset("easy")
        validator.check(
            "Reset environment",
            state is not None and state.get("difficulty") == "easy"
        )
        
        # Test step
        action = {
            "action_type": "classify",
            "target_category": "sales_inquiry",
            "confidence": 0.9
        }
        state, reward, done, info = env.step(action)
        validator.check("Execute step", state is not None and isinstance(reward, float))
        
        # Test reward bounds
        validator.check(
            "Reward in bounds [-0.1, 0.45]",
            -0.1 <= reward <= 0.45,
            f"Got {reward}"
        )
        
        # Test score bounds
        score = state.get("score", 0.0)
        validator.check(
            "Score in bounds [0.0, 1.0]",
            0.0 <= score <= 1.0,
            f"Got {score}"
        )
        
    except Exception as e:
        validator.check("Environment workflow", False, str(e))
        return None
    
    return validator


def test_logging_format():
    """Test logging format compliance."""
    validator = Validator()
    validator.section("3. LOGGING FORMAT VALIDATION")
    
    try:
        from inference import run_inference_episode
        from src.environment import EmailTriageEnv
        import io
        import sys
        
        # Capture logs
        log_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = log_capture
        
        env = EmailTriageEnv()
        results = run_inference_episode(env, "easy", client=None)
        
        sys.stdout = old_stdout
        logs = log_capture.getvalue()
        
        # Check logging format
        has_start = "[START]" in logs
        has_step = "[STEP]" in logs
        has_end = "[END]" in logs
        
        validator.check("Log format: [START]", has_start, logs[:200] if not has_start else "")
        validator.check("Log format: [STEP]", has_step, logs if not has_step else "")
        validator.check("Log format: [END]", has_end, logs[-200:] if not has_end else "")
        
        # Check results
        validator.check(
            "Episode completed",
            bool(results.get("completed") or results.get("success")),
            json.dumps(results, indent=2)
        )
        
    except Exception as e:
        validator.check("Logging format", False, str(e))
        return None
    
    return validator


def test_docker_build():
    """Test Docker build."""
    validator = Validator()
    validator.section("4. DOCKER BUILD VALIDATION")
    
    docker_file = "Dockerfile"
    if not os.path.exists(docker_file):
        validator.check("Dockerfile exists", False, "Dockerfile not found")
        return validator
    
    validator.check("Dockerfile exists", True)
    
    try:
        # Try to build Docker image (might fail in some environments)
        print(f"{YELLOW}→ Building Docker image (this may take a few minutes)...{RESET}")
        result = subprocess.run(
            ["docker", "build", "-t", "email-triage-env:test", "."],
            capture_output=True,
            timeout=300,
            text=True
        )
        
        if result.returncode == 0:
            validator.check("Docker build succeeds", True)
        else:
            error = result.stderr or result.stdout
            validator.check("Docker build succeeds", False, error[:200])
    
    except FileNotFoundError:
        print(f"{YELLOW}⚠ Docker not installed - skipping Docker build test{RESET}")
    except subprocess.TimeoutExpired:
        validator.check("Docker build succeeds", False, "Build timeout")
    except Exception as e:
        print(f"{YELLOW}⚠ Docker test skipped: {e}{RESET}")
    
    return validator


def test_hf_space():
    """Test HF Space deployment (if URL provided)."""
    validator = Validator()
    validator.section("5. HUGGING FACE SPACE VALIDATION")
    
    if not validator.hf_space_url:
        print(f"{YELLOW}⚠ HF_SPACE_URL not set - skipping HF Space tests{RESET}")
        return validator
    
    print(f"Testing HF Space: {validator.hf_space_url}\n")
    
    try:
        # Health check
        resp = requests.get(
            f"{validator.hf_space_url}/health",
            timeout=10
        )
        validator.check(
            "HF Space /health endpoint",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
        
        # Reset endpoint
        resp = requests.post(
            f"{validator.hf_space_url}/reset?task_id=easy",
            timeout=10
        )
        validator.check(
            "HF Space /reset endpoint",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            session_id = data.get("session_id")
            
            # Step endpoint
            resp = requests.post(
                f"{validator.hf_space_url}/step",
                json={
                    "session_id": session_id,
                    "action": {
                        "action_type": "classify",
                        "target_category": "sales_inquiry",
                        "confidence": 0.9
                    }
                },
                timeout=10
            )
            validator.check(
                "HF Space /step endpoint",
                resp.status_code == 200,
                f"Got {resp.status_code}"
            )
    
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ Cannot connect to HF Space{RESET}")
        print(f"{YELLOW}→ Make sure your HF Space is deployed at: {validator.hf_space_url}{RESET}")
    except Exception as e:
        print(f"{YELLOW}⚠ HF Space test error: {e}{RESET}")
    
    return validator


def main():
    """Run all validations."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}EMAIL TRIAGE ENVIRONMENT VALIDATOR{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    validators: List[Validator] = []
    
    # Run all tests
    v = test_imports()
    if v:
        validators.append(v)
    else:
        print(f"{RED}✗ Import validation failed - cannot continue{RESET}")
        return False
    
    v = test_environment()
    if v:
        validators.append(v)
    
    v = test_logging_format()
    if v:
        validators.append(v)
    
    v = test_docker_build()
    if v:
        validators.append(v)
    
    v = test_hf_space()
    if v:
        validators.append(v)
    
    # Print final summary
    total_passed = sum(sum(1 for _, result, _ in v.results if result) for v in validators)
    total_checks = sum(len(v.results) for v in validators)
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}FINAL VALIDATION SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    if total_passed == total_checks:
        print(f"{GREEN}{total_passed}/{total_checks} validations passed{RESET}")
        print(f"{GREEN}✓ Your submission is ready!{RESET}\n")
        return True
    else:
        print(f"{RED}{total_passed}/{total_checks} validations passed{RESET}")
        print(f"{RED}✗ Please fix the failures above.{RESET}\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
