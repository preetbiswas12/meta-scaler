#!/usr/bin/env python3
"""
Comprehensive validator pre-submission checklist.
Tests everything the Meta/Scaler validator expects.
"""

import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional
import yaml

class ValidatorChecklist:
    """Pre-submission validator readiness checklist."""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def log_pass(self, test_name: str, details: str = ""):
        """Log a passing check."""
        print(f"  ✓ {test_name}")
        if details:
            print(f"    {details}")
        self.checks_passed.append(test_name)
    
    def log_fail(self, test_name: str, details: str = ""):
        """Log a failing check."""
        print(f"  ✗ {test_name}")
        if details:
            print(f"    {details}")
        self.checks_failed.append(test_name)
    
    def log_warn(self, test_name: str, details: str = ""):
        """Log a warning."""
        print(f"  ⚠ {test_name}")
        if details:
            print(f"    {details}")
        self.warnings.append(test_name)
    
    def test_pythonpath(self) -> bool:
        """Check PYTHONPATH and package structure."""
        print("\n[1/6] PYTHONPATH & Package Structure")
        print("=" * 70)
        
        all_pass = True
        
        # Check __init__.py files
        init_files = [
            Path("src/__init__.py"),
        ]
        
        for init_file in init_files:
            if init_file.exists():
                self.log_pass(f"{init_file} exists")
            else:
                self.log_fail(f"{init_file} missing - This breaks import!")
                all_pass = False
        
        return all_pass
    
    def test_openenv_yaml(self) -> bool:
        """Validate openenv.yaml structure and required fields."""
        print("\n[2/6] openenv.yaml Validation")
        print("=" * 70)
        
        yaml_path = Path("openenv.yaml")
        if not yaml_path.exists():
            self.log_fail("openenv.yaml not found", "Must be in root directory")
            return False
        
        self.log_pass("openenv.yaml exists in root")
        
        try:
            with open(yaml_path) as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.log_fail("openenv.yaml parse error", str(e))
            return False
        
        self.log_pass("openenv.yaml is valid YAML")
        
        # Check required top-level fields
        required_fields = ["spec_version", "name", "description", "environment", "tasks"]
        for field in required_fields:
            if field in config:
                self.log_pass(f"Top-level field '{field}' present")
            else:
                self.log_fail(f"Top-level field '{field}' MISSING")
                return False
        
        # Check tasks array
        if not isinstance(config.get("tasks"), list):
            self.log_fail("'tasks' is not a list")
            return False
        
        if len(config["tasks"]) == 0:
            self.log_fail("'tasks' array is empty")
            return False
        
        self.log_pass(f"Tasks array present with {len(config['tasks'])} tasks")
        
        # Validate each task
        task_ids = []
        for i, task in enumerate(config["tasks"]):
            task_id = task.get("id")
            task_name = task.get("name")
            task_desc = task.get("description")
            task_diff = task.get("difficulty")
            task_grader = task.get("grader")
            
            if not all([task_id, task_name, task_desc, task_diff, task_grader]):
                self.log_fail(f"Task {i} missing required fields", 
                            f"Has: id={bool(task_id)}, name={bool(task_name)}, "
                            f"desc={bool(task_desc)}, difficulty={bool(task_diff)}, "
                            f"grader={bool(task_grader)}")
                return False
            
            task_ids.append(task_id)
            self.log_pass(f"Task '{task_id}' has all required fields")
            
            if task_diff not in ["easy", "medium", "hard"]:
                self.log_fail(f"Task '{task_id}' difficulty invalid", 
                            f"Expected easy/medium/hard, got '{task_diff}'")
                return False
        
        self.log_pass(f"All {len(task_ids)} tasks have valid difficulty levels")
        
        return True
    
    def test_grader_paths(self) -> bool:
        """Test if grader paths are discoverable and callable."""
        print("\n[3/6] Grader Path Discovery & Callability")
        print("=" * 70)
        
        # Load openenv.yaml to get grader paths
        with open("openenv.yaml") as f:
            config = yaml.safe_load(f)
        
        all_pass = True
        
        for task in config["tasks"]:
            task_id = task["id"]
            grader_path = task["grader"]
            
            # Parse grader path
            if ":" not in grader_path:
                self.log_fail(f"Task '{task_id}' grader path format invalid", 
                            f"Expected 'module:function', got '{grader_path}'")
                all_pass = False
                continue
            
            module_path, func_name = grader_path.rsplit(":", 1)
            
            # Try to import
            try:
                module = importlib.import_module(module_path)
                self.log_pass(f"Module '{module_path}' imported successfully")
            except ImportError as e:
                self.log_fail(f"Cannot import '{module_path}'", str(e))
                all_pass = False
                continue
            
            # Check if function exists
            if not hasattr(module, func_name):
                self.log_fail(f"Function '{func_name}' not in module '{module_path}'")
                all_pass = False
                continue
            
            grader_func = getattr(module, func_name)
            
            # Check if callable
            if not callable(grader_func):
                self.log_fail(f"'{func_name}' is not callable")
                all_pass = False
                continue
            
            self.log_pass(f"Task '{task_id}' grader '{func_name}' is callable")
            
            # Check function signature
            import inspect
            sig = inspect.signature(grader_func)
            params = list(sig.parameters.keys())
            
            # Should have required params and **kwargs
            if "kwargs" not in str(sig):
                self.log_warn(f"Task '{task_id}' grader signature missing **kwargs", 
                            f"Has params: {params}")
        
        return all_pass
    
    def test_environment_initialization(self) -> bool:
        """Test environment initialization with all task IDs."""
        print("\n[4/6] Environment Initialization")
        print("=" * 70)
        
        from src.environment import EmailTriageEnv
        
        task_ids = [
            "basic_email_classification",
            "phishing_threat_detection",
            "critical_escalation_handling",
        ]
        
        all_pass = True
        
        for task_id in task_ids:
            try:
                env = EmailTriageEnv()
                state = env.reset(task_id)
                
                # Verify required state fields
                required_state_fields = [
                    "task_id", "difficulty", "episode_id", "step", 
                    "max_steps", "done", "score", "reward"
                ]
                
                missing = [f for f in required_state_fields if f not in state]
                if missing:
                    self.log_fail(f"Task '{task_id}' state missing fields", 
                                f"Missing: {missing}")
                    all_pass = False
                    continue
                
                # Verify state values are correct
                if state["task_id"] != task_id:
                    self.log_fail(f"Task '{task_id}' task_id mismatch", 
                                f"Expected '{task_id}', got '{state['task_id']}'")
                    all_pass = False
                    continue
                
                if state["difficulty"] not in ["easy", "medium", "hard"]:
                    self.log_fail(f"Task '{task_id}' invalid difficulty", 
                                f"Got '{state['difficulty']}'")
                    all_pass = False
                    continue
                
                self.log_pass(f"Task '{task_id}' initializes correctly → "
                            f"difficulty: {state['difficulty']}, "
                            f"max_steps: {state['max_steps']}")
                
            except Exception as e:
                self.log_fail(f"Task '{task_id}' initialization failed", str(e))
                all_pass = False
        
        return all_pass
    
    def test_reward_bounds(self) -> bool:
        """Test that graders produce valid normalized rewards."""
        print("\n[5/6] Reward Bounds Validation")
        print("=" * 70)
        
        from src.graders_normalized import (
            grade_basic_classification,
            grade_phishing_detection,
            grade_escalation_handling,
        )
        
        graders = [
            ("basic_classification", grade_basic_classification),
            ("phishing_detection", grade_phishing_detection),
            ("escalation_handling", grade_escalation_handling),
        ]
        
        all_pass = True
        
        # Mock objects for testing
        action = type('Action', (), {
            'action_type': 'classify', 
            'confidence': 0.85
        })()
        email = {'email_id': 'test_001', 'subject': 'Test Email'}
        ground_truth = {'category': 'test', 'priority': 1, 'ambiguity': 'low'}
        
        for grader_name, grader_func in graders:
            try:
                reward, info = grader_func(
                    action=action,
                    email=email,
                    ground_truth=ground_truth,
                    step_number=1,
                )
                
                # Validate reward is in (0, 1) exclusive
                if not (0 < reward < 1):
                    self.log_fail(f"'{grader_name}' reward out of bounds", 
                                f"Reward={reward:.10f}, must be in (0, 1)")
                    all_pass = False
                    continue
                
                # Validate info is dict
                if not isinstance(info, dict):
                    self.log_fail(f"'{grader_name}' info not a dict", 
                                f"Got {type(info)}")
                    all_pass = False
                    continue
                
                self.log_pass(f"'{grader_name}' grader produces valid reward", 
                            f"Reward={reward:.6f} (0 < r < 1) ✓")
                
            except Exception as e:
                self.log_fail(f"'{grader_name}' grader call failed", str(e))
                all_pass = False
        
        return all_pass
    
    def test_docker_readiness(self) -> bool:
        """Check Docker configuration."""
        print("\n[6/6] Docker Configuration")
        print("=" * 70)
        
        all_pass = True
        
        # Check Dockerfile exists
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            self.log_fail("Dockerfile not found")
            return False
        
        self.log_pass("Dockerfile exists")
        
        # Check for problematic COPY commands in Dockerfile
        with open(dockerfile) as f:
            content = f.read()
        
        # Should not try to copy deleted config/ directory
        if "COPY config/" in content:
            self.log_fail("Dockerfile still tries to COPY config/ (deleted)", 
                        "Remove: COPY config/ config/")
            all_pass = False
        else:
            self.log_pass("Dockerfile doesn't reference deleted config/ directory")
        
        # Check docker-compose exists
        docker_compose = Path("docker-compose.yml")
        if not docker_compose.exists():
            self.log_fail("docker-compose.yml not found")
            return False
        
        self.log_pass("docker-compose.yml exists")
        
        # Check for environment variables
        with open(docker_compose) as f:
            compose_content = f.read()
        
        if "API_KEY" in compose_content and "API_BASE_URL" in compose_content:
            self.log_pass("docker-compose sets API_KEY and API_BASE_URL")
        else:
            self.log_warn("docker-compose may not properly set API credentials")
        
        # Check for volume mount
        if "volumes:" in compose_content and ".:/app" in compose_content:
            self.log_pass("docker-compose mounts root directory as /app volume")
        else:
            self.log_warn("docker-compose volume configuration unclear")
        
        return all_pass
    
    def run_all_checks(self) -> int:
        """Run all checklist items."""
        print("\n" + "=" * 70)
        print("VALIDATOR PRE-SUBMISSION CHECKLIST")
        print("=" * 70)
        
        checks = [
            self.test_pythonpath,
            self.test_openenv_yaml,
            self.test_grader_paths,
            self.test_environment_initialization,
            self.test_reward_bounds,
            self.test_docker_readiness,
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                print(f"\n[ERROR] Check failed with exception: {e}")
                import traceback
                traceback.print_exc()
                results.append(False)
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        passed = len(self.checks_passed)
        failed = len(self.checks_failed)
        warnings = len(self.warnings)
        
        print(f"\n✓ Passed:  {passed}")
        print(f"✗ Failed:  {failed}")
        print(f"⚠ Warnings: {warnings}")
        
        if failed == 0 and warnings == 0:
            print("\n" + "=" * 70)
            print("🎉 ALL CHECKS PASSED!")
            print("Your submission is ready for the validator.")
            print("=" * 70)
            return 0
        elif failed == 0:
            print("\n" + "=" * 70)
            print("✓ Ready to submit (warnings are not blocking)")
            print("=" * 70)
            return 0
        else:
            print("\n" + "=" * 70)
            print("❌ FAILED - Fix issues above before submitting")
            print("=" * 70)
            return 1

if __name__ == "__main__":
    checklist = ValidatorChecklist()
    exit_code = checklist.run_all_checks()
    sys.exit(exit_code)
