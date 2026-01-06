"""
Configuration for testing generated code
"""

# Test scenarios to run on generated projects
TEST_SCENARIOS = {
    "basic_import": {
        "description": "Test if all modules can be imported",
        "required": True
    },
    "json_handling": {
        "description": "Test JSON parsing with invalid input",
        "test_input": '{"invalid": json}',
        "required": True
    },
    "api_mocking": {
        "description": "Test with mocked API responses",
        "required": False
    },
    "error_handling": {
        "description": "Test error handling paths",
        "required": True
    }
}

# Common runtime errors to check for
RUNTIME_ERROR_PATTERNS = [
    {
        "pattern": r"json\.loads?\([^)]+\)",
        "check": "JSONDecodeError handling",
        "fix": "Add try-except with json.JSONDecodeError"
    },
    {
        "pattern": r"\w+\[['\"][\w]+['\"]\]",
        "check": "KeyError handling",
        "fix": "Use .get() method or validate key exists"
    },
    {
        "pattern": r"requests\.(get|post|put|delete)",
        "check": "RequestException handling",
        "fix": "Add try-except with requests.exceptions.RequestException"
    },
    {
        "pattern": r"open\([^)]+\)",
        "check": "File error handling",
        "fix": "Use 'with open()' context manager"
    },
    {
        "pattern": r"int\(|float\(|str\(",
        "check": "Type conversion error handling",
        "fix": "Add try-except with ValueError"
    }
]

# Validation rules
VALIDATION_RULES = {
    "must_have_error_handling": True,
    "must_use_type_hints": False,  # Optional but recommended
    "must_have_docstrings": False,  # Optional
    "max_function_length": 50,  # Lines
    "require_logging": False  # Optional
}

# Mock data for testing
MOCK_RESPONSES = {
    "llm_response": {
        "content": "Test response from mocked LLM",
        "role": "assistant"
    },
    "api_response": {
        "status": "success",
        "data": {"result": "test"}
    },
    "database_response": {
        "rows": [{"id": 1, "name": "test"}]
    }
}