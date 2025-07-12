# Contributing to Secret Run

Thank you for your interest in contributing to Secret Run! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/yourusername/secret-run.git`
3. **Create** a virtual environment: `python -m venv venv`
4. **Activate** the environment: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
5. **Install** dependencies: `pip install -e ".[dev,all]"`
6. **Install** pre-commit hooks: `pre-commit install`
7. **Create** a feature branch: `git checkout -b feature/amazing-feature`
8. **Make** your changes
9. **Test** your changes: `pytest`
10. **Commit** your changes: `git commit -m 'Add amazing feature'`
11. **Push** to your branch: `git push origin feature/amazing-feature`
12. **Open** a Pull Request

## 📋 Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- A code editor (VS Code, PyCharm, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/secret-run.git
cd secret-run

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=secret_run --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m security
pytest -m performance

# Run tests in parallel
pytest -n auto
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Security checks
bandit -r src/
safety check
```

## 🏗️ Project Structure

```
secret-run/
├── src/secret_run/           # Main source code
│   ├── cli/                  # Command-line interface
│   ├── core/                 # Core functionality
│   ├── integrations/         # External integrations
│   └── utils/                # Utility modules
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── security/             # Security tests
│   └── performance/          # Performance tests
├── examples/                 # Usage examples
├── docs/                     # Documentation
└── templates/                # Configuration templates
```

## 📝 Code Style

We follow these coding standards:

- **Black**: Code formatting (88 character line length)
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **Docstrings**: Google style docstrings
- **Type Hints**: Full type annotations required

### Example Code Style

```python
"""Example module demonstrating code style."""

from typing import Dict, List, Optional

from secret_run.core.secrets import SecretManager
from secret_run.utils.logging import get_logger

logger = get_logger(__name__)


class ExampleClass:
    """Example class demonstrating proper code style.
    
    This class shows how to write clean, well-documented code
    that follows our project's style guidelines.
    
    Args:
        name: The name of the example.
        config: Optional configuration dictionary.
    
    Attributes:
        name: The name of the example.
        config: The configuration dictionary.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, str]] = None) -> None:
        """Initialize the example class.
        
        Args:
            name: The name of the example.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.config = config or {}
        logger.debug(f"Initialized ExampleClass with name: {name}")
    
    def process_data(self, data: List[str]) -> Dict[str, int]:
        """Process a list of strings and return character counts.
        
        Args:
            data: List of strings to process.
            
        Returns:
            Dictionary mapping strings to their character counts.
            
        Raises:
            ValueError: If data is empty.
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        result = {item: len(item) for item in data}
        logger.info(f"Processed {len(data)} items")
        return result
```

## 🧪 Testing Guidelines

### Test Categories

- **Unit Tests** (`@pytest.mark.unit`): Test individual functions and classes
- **Integration Tests** (`@pytest.mark.integration`): Test component interactions
- **Security Tests** (`@pytest.mark.security`): Test security features
- **Performance Tests** (`@pytest.mark.performance`): Test performance characteristics

### Test Structure

```python
"""Tests for example module."""

import pytest
from unittest.mock import Mock, patch

from secret_run.core.example import ExampleClass


class TestExampleClass:
    """Test ExampleClass functionality."""
    
    def test_init(self):
        """Test class initialization."""
        example = ExampleClass("test")
        assert example.name == "test"
        assert example.config == {}
    
    def test_process_data(self):
        """Test data processing."""
        example = ExampleClass("test")
        data = ["hello", "world"]
        result = example.process_data(data)
        
        assert result["hello"] == 5
        assert result["world"] == 5
    
    def test_process_data_empty(self):
        """Test processing empty data raises error."""
        example = ExampleClass("test")
        
        with pytest.raises(ValueError, match="Data cannot be empty"):
            example.process_data([])
    
    @patch('secret_run.utils.logging.get_logger')
    def test_logging(self, mock_logger):
        """Test logging functionality."""
        mock_log = Mock()
        mock_logger.return_value = mock_log
        
        example = ExampleClass("test")
        example.process_data(["test"])
        
        mock_log.info.assert_called_once()
```

### Test Coverage

We aim for:
- **Line Coverage**: ≥95%
- **Branch Coverage**: ≥90%
- **Function Coverage**: 100%

## 🔒 Security Guidelines

### Security Considerations

- **Input Validation**: Always validate and sanitize inputs
- **Secret Handling**: Never log or expose secrets
- **Memory Safety**: Use secure memory allocation and cleanup
- **Process Isolation**: Ensure proper process boundaries
- **File Permissions**: Validate file paths and permissions

### Security Testing

```python
"""Security tests for example module."""

import pytest
from secret_run.core.security import SecurityManager


class TestSecurityFeatures:
    """Test security features."""
    
    def test_command_sanitization(self):
        """Test command sanitization."""
        security = SecurityManager()
        
        # Test safe command
        safe_cmd = "python script.py"
        assert security.sanitize_command(safe_cmd) == safe_cmd
        
        # Test dangerous command (should log warning)
        dangerous_cmd = "python script.py; rm -rf /"
        result = security.sanitize_command(dangerous_cmd)
        # Should log warning but not modify command
    
    def test_file_path_validation(self):
        """Test file path validation."""
        security = SecurityManager()
        
        # Valid paths
        assert security.validate_file_path("config.yaml") is True
        assert security.validate_file_path("./config.yaml") is True
        
        # Invalid paths
        assert security.validate_file_path("../config.yaml") is False
        assert security.validate_file_path("/etc/passwd") is False
```

## 📚 Documentation

### Docstring Guidelines

- Use Google style docstrings
- Include type hints
- Document all public functions and classes
- Provide usage examples for complex functions

### Documentation Structure

```
docs/
├── api/              # API documentation
├── guides/           # User guides
├── examples/         # Code examples
└── contributing/     # Contributing documentation
```

## 🚀 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Code coverage meets requirements
- [ ] Documentation is updated
- [ ] Changelog is updated
- [ ] Version is bumped
- [ ] Release notes are written

### Creating a Release

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Create and push tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will automatically:
# - Run tests
# - Build package
# - Publish to PyPI
# - Create GitHub release
```

## 🤝 Pull Request Guidelines

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests are added/updated
- [ ] Documentation is updated
- [ ] Changelog entry is added
- [ ] All CI checks pass

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Manual testing completed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changelog entry added
```

## 🆘 Getting Help

### Communication Channels

- **Issues**: [GitHub Issues](https://github.com/yourusername/secret-run/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/secret-run/discussions)
- **Security**: [Security Policy](SECURITY.md)

### Before Asking for Help

1. Check existing issues and discussions
2. Read the documentation
3. Try the examples
4. Run the test suite
5. Check the troubleshooting guide

## 🙏 Acknowledgments

Thank you for contributing to Secret Run! Your contributions help make this tool better for everyone in the security and DevOps communities.

---

**Happy coding! 🚀** 