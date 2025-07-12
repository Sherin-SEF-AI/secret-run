"""Configuration management utilities."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from platformdirs import user_config_dir

from .logging import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, app_name: str = "secret-run"):
        self.app_name = app_name
        self.config_dir = Path(user_config_dir(app_name))
        self.config_file = self.config_dir / "config.yaml"
        self.profiles_dir = self.config_dir / "profiles"
        self.templates_dir = self.config_dir / "templates"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "version": "1.0",
            "default_profile": "default",
            "security": {
                "mask_output": True,
                "audit_logging": True,
                "memory_limit": 512,
                "execution_timeout": 300,
                "require_confirmation": False,
            },
            "logging": {
                "level": "INFO",
                "format": "structured",
                "file": str(self.config_dir / "logs" / "secret-run.log"),
                "max_size": "10MB",
                "max_files": 5,
            },
            "sources": {
                "default_format": "env",
                "cache_ttl": 300,
                "parallel_loading": True,
                "validation_enabled": True,
            },
            "execution": {
                "default_shell": "auto",
                "inherit_environment": True,
                "working_directory": ".",
                "signal_timeout": 10,
            },
            "ui": {
                "color": True,
                "progress_bars": True,
                "confirmation_prompts": True,
                "table_format": "grid",
            },
            "integrations": {
                "password_managers": {},
                "cloud": {},
            },
        }
        
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = yaml.safe_load(f)
                logger.debug(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                self._config = self.default_config.copy()
        else:
            self._config = self.default_config.copy()
            self.save_config()
        
        return self._config
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            logger.debug(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        config = self.load_config()
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)."""
        config = self.load_config()
        keys = key.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        self._config = config
        self.save_config()
        logger.debug(f"Set configuration {key} = {value}")
    
    def unset(self, key: str) -> bool:
        """Remove configuration value by key."""
        config = self.load_config()
        keys = key.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                return False
            current = current[k]
        
        # Remove the key
        if keys[-1] in current:
            del current[keys[-1]]
            self._config = config
            self.save_config()
            logger.debug(f"Unset configuration {key}")
            return True
        
        return False
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = self.default_config.copy()
        self.save_config()
        logger.info("Configuration reset to defaults")
    
    def validate(self) -> Dict[str, list]:
        """Validate configuration."""
        issues = {
            'errors': [],
            'warnings': [],
        }
        
        config = self.load_config()
        
        # Check required fields
        required_fields = ['version', 'default_profile']
        for field in required_fields:
            if field not in config:
                issues['errors'].append(f"Missing required field: {field}")
        
        # Check security settings
        security = config.get('security', {})
        if security.get('memory_limit', 0) <= 0:
            issues['errors'].append("Memory limit must be positive")
        
        if security.get('execution_timeout', 0) <= 0:
            issues['errors'].append("Execution timeout must be positive")
        
        # Check logging settings
        logging_config = config.get('logging', {})
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if logging_config.get('level', 'INFO') not in valid_levels:
            issues['errors'].append(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        
        return issues
    
    def export_config(self, path: Path, format: str = "yaml") -> None:
        """Export configuration to file."""
        config = self.load_config()
        
        try:
            if format.lower() == "json":
                with open(path, 'w') as f:
                    json.dump(config, f, indent=2)
            else:
                with open(path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration exported to {path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise
    
    def import_config(self, path: Path, format: str = "auto") -> None:
        """Import configuration from file."""
        try:
            if format == "auto":
                if path.suffix.lower() == '.json':
                    format = "json"
                else:
                    format = "yaml"
            
            if format.lower() == "json":
                with open(path, 'r') as f:
                    config = json.load(f)
            else:
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
            
            # Validate imported config
            issues = self._validate_imported_config(config)
            if issues['errors']:
                raise ValueError(f"Invalid configuration: {', '.join(issues['errors'])}")
            
            self._config = config
            self.save_config()
            logger.info(f"Configuration imported from {path}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise
    
    def _validate_imported_config(self, config: Dict[str, Any]) -> Dict[str, list]:
        """Validate imported configuration."""
        issues = {
            'errors': [],
            'warnings': [],
        }
        
        if not isinstance(config, dict):
            issues['errors'].append("Configuration must be a dictionary")
            return issues
        
        # Check for required top-level keys
        required_keys = ['version', 'security', 'logging', 'sources', 'execution', 'ui']
        for key in required_keys:
            if key not in config:
                issues['warnings'].append(f"Missing section: {key}")
        
        return issues
    
    def get_profile_path(self, profile_name: str) -> Path:
        """Get path for a profile configuration file."""
        return self.profiles_dir / f"{profile_name}.yaml"
    
    def list_profiles(self) -> list[str]:
        """List available profiles."""
        profiles = []
        for profile_file in self.profiles_dir.glob("*.yaml"):
            profiles.append(profile_file.stem)
        return sorted(profiles)
    
    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Load a profile configuration."""
        profile_path = self.get_profile_path(profile_name)
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
            logger.debug(f"Loaded profile '{profile_name}'")
            return profile
        except Exception as e:
            logger.error(f"Failed to load profile '{profile_name}': {e}")
            return None
    
    def save_profile(self, profile_name: str, profile_config: Dict[str, Any]) -> None:
        """Save a profile configuration."""
        profile_path = self.get_profile_path(profile_name)
        
        try:
            with open(profile_path, 'w') as f:
                yaml.dump(profile_config, f, default_flow_style=False, indent=2)
            logger.debug(f"Saved profile '{profile_name}'")
        except Exception as e:
            logger.error(f"Failed to save profile '{profile_name}': {e}")
            raise
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile configuration."""
        profile_path = self.get_profile_path(profile_name)
        
        if profile_path.exists():
            try:
                profile_path.unlink()
                logger.debug(f"Deleted profile '{profile_name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to delete profile '{profile_name}': {e}")
                return False
        
        return False 