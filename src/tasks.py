"""
Task definitions for Code Test Generation environment
"""
from typing import Dict, Any, List


class Task:
    """Task definition class"""

    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        difficulty: str,
        code_snippet: str,
        function_name: str,
        edge_cases: List[str],
        expected_tests: int,
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.code_snippet = code_snippet
        self.function_name = function_name
        self.edge_cases = edge_cases
        self.expected_tests = expected_tests

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty,
            "code_snippet": self.code_snippet,
            "function_name": self.function_name,
            "edge_cases": self.edge_cases,
            "expected_tests": self.expected_tests,
        }


# Task definitions
EASY_TASK = Task(
    task_id="easy",
    name="Simple Function Testing",
    description="Generate tests for a simple utility function",
    difficulty="easy",
    code_snippet='''def add(a, b):
    """Add two numbers."""
    return a + b
''',
    function_name="add",
    edge_cases=["positive numbers", "negative numbers", "zero"],
    expected_tests=4,
)

MEDIUM_TASK = Task(
    task_id="medium",
    name="Edge Case Coverage",
    description="Generate tests covering edge cases and error conditions",
    difficulty="medium",
    code_snippet='''def validate_email(email):
    """Validate email format."""
    if not isinstance(email, str):
        return False
    if "@" not in email or "." not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if "." not in domain or domain.startswith("."):
        return False
    return True
''',
    function_name="validate_email",
    edge_cases=[
        "valid email",
        "no @",
        "no domain",
        "multiple @",
        "empty string",
        "non-string input",
    ],
    expected_tests=8,
)

HARD_TASK = Task(
    task_id="hard",
    name="Complex System Testing",
    description="Generate comprehensive tests for complex state management",
    difficulty="hard",
    code_snippet='''class CacheWithTTL:
    """Cache with time-to-live expiration."""
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}
    
    def set(self, key, value):
        """Store key-value with timestamp."""
        import time
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def get(self, key):
        """Retrieve value if not expired."""
        import time
        if key not in self.cache:
            return None
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        return self.cache[key]
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.timestamps.clear()
''',
    function_name="CacheWithTTL",
    edge_cases=[
        "set and get",
        "ttl expiration",
        "missing key",
        "clear cache",
        "multiple keys",
    ],
    expected_tests=12,
)

TASKS_DATABASE = {
    "easy": EASY_TASK.to_dict(),
    "medium": MEDIUM_TASK.to_dict(),
    "hard": HARD_TASK.to_dict(),
}


def get_task_by_id(task_id: str) -> Dict[str, Any]:
    """Get task by ID"""
    if task_id not in TASKS_DATABASE:
        raise ValueError(f"Unknown task ID: {task_id}")
    return TASKS_DATABASE[task_id]


def list_all_tasks() -> List[str]:
    """List all available task IDs"""
    return list(TASKS_DATABASE.keys())


def get_difficulty_level(task_id: str) -> str:
    """Get difficulty level for a task"""
    task = get_task_by_id(task_id)
    return task["difficulty"]


def get_expected_test_count(task_id: str) -> int:
    """Get expected number of tests for a task"""
    task = get_task_by_id(task_id)
    return task["expected_tests"]
