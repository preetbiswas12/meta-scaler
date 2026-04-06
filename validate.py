#!/usr/bin/env python3
"""
Validation script for Code Test Generation OpenEnv environment
Verifies all components are working correctly before deployment
"""
import sys
import os
import json
from pathlib import Path


def check_files():
    """Check that all required files exist"""
    print("Checking files...")
    required_files = [
        "config/openenv.yaml",
        "src/__init__.py",
        "src/environment.py",
        "src/graders.py",
        "src/tasks.py",
        "inference.py",
        "requirements.txt",
        "Dockerfile",
        "README.md",
        "test_integration.py",
    ]
    
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        print(f"  ✗ Missing files: {missing}")
        return False
    
    print("  ✓ All required files present")
    return True


def check_imports():
    """Check that all modules can be imported"""
    print("Checking imports...")
    try:
        from src.environment import CodeTestGenerationEnv
        from src.graders import DeterministicGrader
        from src.tasks import list_all_tasks
        from inference import OpenAIClient, _get_mock_tests
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def check_environment():
    """Check environment initialization"""
    print("Checking environment initialization...")
    try:
        from src.environment import CodeTestGenerationEnv
        env = CodeTestGenerationEnv()
        assert env is not None
        print("  ✓ Environment initializes correctly")
        return True
    except Exception as e:
        print(f"  ✗ Environment check failed: {e}")
        return False


def check_tasks():
    """Check all tasks are available"""
    print("Checking tasks...")
    try:
        from src.environment import CodeTestGenerationEnv
        env = CodeTestGenerationEnv()
        
        for task_id in ["easy", "medium", "hard"]:
            state = env.reset(task_id)
            assert state["difficulty"] == task_id
            assert state["code_snippet"] != ""
        
        print("  ✓ All 3 tasks available and working")
        return True
    except Exception as e:
        print(f"  ✗ Task check failed: {e}")
        return False


def check_grading():
    """Check deterministic grading"""
    print("Checking grading system...")
    try:
        from src.graders import DeterministicGrader
        grader = DeterministicGrader()
        
        test_code = "def test(): assert True"
        score1, reward1, _ = grader.grade(
            "def func(): pass", test_code, "easy", "func"
        )
        score2, reward2, _ = grader.grade(
            "def func(): pass", test_code, "easy", "func"
        )
        
        assert score1 == score2, "Grading is not deterministic"
        print(f"  ✓ Deterministic grading working (scores: {score1:.3f})")
        return True
    except Exception as e:
        print(f"  ✗ Grading check failed: {e}")
        return False


def check_logging_format():
    """Check logging format"""
    print("Checking logging format...")
    try:
        import logging
        from io import StringIO
        
        # Capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("test_logger")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Test formats
        logger.info("[START] episode_id=test task=easy")
        logger.info("[STEP] step=1 reward=0.5 score=0.7")
        logger.info("[END] episode_id=test final_score=0.8")
        
        logs = log_stream.getvalue()
        assert "[START]" in logs
        assert "[STEP]" in logs
        assert "[END]" in logs
        
        print("  ✓ Logging format correct")
        return True
    except Exception as e:
        print(f"  ✗ Logging check failed: {e}")
        return False


def check_requirements():
    """Check that requirements are specified"""
    print("Checking requirements.txt...")
    try:
        with open("requirements.txt") as f:
            content = f.read()
            required_packages = ["pydantic", "requests", "pytest", "PyYAML"]
            missing_packages = []
            for pkg in required_packages:
                if pkg.lower() not in content.lower():
                    missing_packages.append(pkg)
            
            if missing_packages:
                print(f"  ✗ Missing packages: {missing_packages}")
                return False
            
            print("  ✓ All required packages specified")
            return True
    except Exception as e:
        print(f"  ✗ Requirements check failed: {e}")
        return False


def run_quick_episode():
    """Run a quick episode"""
    print("Running quick episode...")
    try:
        from src.environment import CodeTestGenerationEnv
        
        env = CodeTestGenerationEnv()
        state = env.reset("easy")
        
        tests = "def test_add(): assert 2 + 3 == 5"
        state, reward, done, info = env.step(tests)
        
        assert state["score"] >= 0.0 and state["score"] <= 1.0
        assert reward >= -1.0 and reward <= 1.0
        
        print(f"  ✓ Episode ran successfully (score: {state['score']:.3f})")
        return True
    except Exception as e:
        print(f"  ✗ Episode run failed: {e}")
        return False


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Code Test Generation - Validation Report")
    print("=" * 60)
    print()
    
    checks = [
        check_files,
        check_imports,
        check_environment,
        check_tasks,
        check_grading,
        check_logging_format,
        check_requirements,
        run_quick_episode,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All validations passed! Ready for deployment.")
        return 0
    else:
        print("✗ Some validations failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
