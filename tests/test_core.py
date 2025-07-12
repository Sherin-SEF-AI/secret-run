"""Tests for core functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from secret_run.core.secrets import SecretManager, Secret
from secret_run.core.loaders import LoaderManager, EnvFileLoader
from secret_run.core.validators import SecretValidator
from secret_run.core.security import SecurityManager


class TestSecretManager:
    """Test SecretManager functionality."""
    
    def test_add_secret(self):
        """Test adding a secret."""
        manager = SecretManager()
        manager.add_secret("API_KEY", "secret123", "test")
        
        assert manager.get_secret("API_KEY") == "secret123"
        assert len(manager.secrets) == 1
    
    def test_add_secrets(self):
        """Test adding multiple secrets."""
        manager = SecretManager()
        secrets = {"API_KEY": "secret123", "DATABASE_URL": "postgresql://"}
        manager.add_secrets(secrets, "test")
        
        assert manager.get_secret("API_KEY") == "secret123"
        assert manager.get_secret("DATABASE_URL") == "postgresql://"
        assert len(manager.secrets) == 2
    
    def test_remove_secret(self):
        """Test removing a secret."""
        manager = SecretManager()
        manager.add_secret("API_KEY", "secret123", "test")
        
        assert manager.remove_secret("API_KEY") is True
        assert manager.get_secret("API_KEY") is None
        assert len(manager.secrets) == 0
    
    def test_clear_secrets(self):
        """Test clearing all secrets."""
        manager = SecretManager()
        manager.add_secrets({"KEY1": "val1", "KEY2": "val2"}, "test")
        
        manager.clear_secrets()
        assert len(manager.secrets) == 0
    
    def test_validate_secrets(self):
        """Test secret validation."""
        manager = SecretManager()
        import pytest
        from pydantic import ValidationError
        # Adding a secret with an empty value should raise ValidationError
        with pytest.raises(ValidationError):
            manager.add_secrets({
                "API_KEY": "secret123",
                "EMPTY_KEY": "",
                "PASSWORD": "weak"
            }, "test")
        # Test missing key logic separately
        manager = SecretManager()
        manager.add_secrets({"API_KEY": "secret123"}, "test")
        issues = manager.validate_secrets(required_keys=["API_KEY", "MISSING_KEY"])
        assert "MISSING_KEY" in issues["missing"]
    
    def test_validator_validate_secrets(self):
        """Test secret validation."""
        validator = SecretValidator()
        secrets = {
            "API_KEY": "secret123",
            "EMPTY_KEY": "",
            "PASSWORD": "weak"
        }
        
        issues = validator.validate_secrets(secrets, required_keys=["API_KEY", "MISSING_KEY"])
        # The new error messages are more descriptive
        assert any("EMPTY_KEY: Secret 'EMPTY_KEY' is too short (min: 1)" in err for err in issues["errors"])
        assert any("PASSWORD: Password 'PASSWORD' must contain" in err for err in issues["errors"])
        assert "MISSING_KEY" not in issues["errors"]  # Now handled as missing, not error
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        validator = SecretValidator()
        
        # Weak password
        issues = validator.validate_secrets({"user_password": "weak"})
        assert any("user_password: Password 'user_password' must contain" in err for err in issues["errors"])
        
        # Strong password
        issues = validator.validate_secrets({"user_password": "StrongPass123!"})
        assert not any("user_password: Password 'user_password' must contain" in err for err in issues["errors"])


class TestSecurityManager:
    """Test SecurityManager functionality."""
    
    def test_secure_allocate(self):
        """Test secure memory allocation."""
        manager = SecurityManager()
        
        # Test allocation
        memory = manager.secure_allocate(1024)
        assert len(memory) == 1024
        
        # Test cleanup
        manager.cleanup()
    
    def test_validate_secret_pattern(self):
        """Test secret pattern validation."""
        manager = SecurityManager()
        
        # Valid API key
        assert manager.validate_secret_pattern("API_KEY", "sk_live_1234567890abcdef1234567890abcdef") is True
        
        # Invalid API key (too short)
        assert manager.validate_secret_pattern("API_KEY", "short") is False
    
    def test_sanitize_command(self):
        """Test command sanitization."""
        manager = SecurityManager()
        
        # Safe command
        safe_cmd = "python script.py"
        assert manager.sanitize_command(safe_cmd) == safe_cmd
        
        # Command with potentially dangerous characters
        dangerous_cmd = "python script.py; rm -rf /"
        result = manager.sanitize_command(dangerous_cmd)
        assert result == dangerous_cmd  # Should log warning but not modify
    
    def test_validate_file_path(self):
        """Test file path validation."""
        manager = SecurityManager()
        
        # Valid path
        assert manager.validate_file_path("config.yaml") is True
        
        # Invalid paths
        assert manager.validate_file_path("../config.yaml") is False
        assert manager.validate_file_path("/etc/passwd") is False


class TestLoaderManager:
    """Test LoaderManager functionality."""
    
    def test_get_available_loaders(self):
        """Test getting available loaders."""
        manager = LoaderManager()
        loaders = manager.get_available_loaders()
        
        assert "EnvFileLoader" in loaders
        assert "JsonLoader" in loaders
        assert "YamlLoader" in loaders
        assert "StdinLoader" in loaders
        assert "EnvironmentLoader" in loaders
    
    def test_env_file_loader(self):
        """Test environment file loader."""
        loader = EnvFileLoader()
        
        # Test can_load method
        assert loader.can_load(".env") is True
        assert loader.can_load("config.env") is True
        assert loader.can_load("config.json") is False
    
    @patch('builtins.open')
    def test_load_nonexistent_file(self, mock_open):
        """Test loading non-existent file."""
        mock_open.side_effect = FileNotFoundError("File not found")
        loader = EnvFileLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.env") 