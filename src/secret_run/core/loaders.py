"""Secret loaders for various input sources."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from dotenv import dotenv_values

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SecretLoader:
    """Base class for secret loaders."""
    
    def load(self, source: str) -> Dict[str, str]:
        """Load secrets from source."""
        raise NotImplementedError
    
    def can_load(self, source: str) -> bool:
        """Check if this loader can handle the source."""
        raise NotImplementedError


class EnvFileLoader(SecretLoader):
    """Load secrets from .env files."""
    
    def can_load(self, source: str) -> bool:
        """Check if source is a .env file."""
        return source.endswith('.env') or 'env' in source.lower()
    
    def load(self, source: str) -> Dict[str, str]:
        """Load secrets from .env file."""
        try:
            env_path = Path(source)
            if not env_path.exists():
                raise FileNotFoundError(f"Environment file not found: {source}")
            
            # Load using python-dotenv
            env_vars = dotenv_values(env_path)
            
            # Filter out None values
            secrets = {k: v for k, v in env_vars.items() if v is not None}
            
            logger.debug(f"Loaded {len(secrets)} secrets from {source}")
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to load .env file {source}: {e}")
            raise


class JsonLoader(SecretLoader):
    """Load secrets from JSON files."""
    
    def can_load(self, source: str) -> bool:
        """Check if source is a JSON file."""
        return source.endswith('.json') or source.startswith('json:')
    
    def load(self, source: str) -> Dict[str, str]:
        """Load secrets from JSON file."""
        try:
            if source.startswith('json:'):
                # Parse JSON string directly
                data = json.loads(source[5:])
            else:
                # Load from file
                json_path = Path(source)
                if not json_path.exists():
                    raise FileNotFoundError(f"JSON file not found: {source}")
                
                with open(json_path, 'r') as f:
                    data = json.load(f)
            
            # Convert to string values
            secrets = {}
            self._flatten_dict(data, secrets)
            
            logger.debug(f"Loaded {len(secrets)} secrets from {source}")
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to load JSON file {source}: {e}")
            raise
    
    def _flatten_dict(self, data: Any, result: Dict[str, str], prefix: str = ""):
        """Flatten nested dictionary."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}{key}" if prefix else key
                self._flatten_dict(value, result, f"{new_key}_")
        elif isinstance(data, (list, tuple)):
            for i, value in enumerate(data):
                new_key = f"{prefix}{i}" if prefix else str(i)
                self._flatten_dict(value, result, f"{new_key}_")
        else:
            result[prefix.rstrip('_')] = str(data)


class YamlLoader(SecretLoader):
    """Load secrets from YAML files."""
    
    def can_load(self, source: str) -> bool:
        """Check if source is a YAML file."""
        return source.endswith(('.yml', '.yaml')) or source.startswith('yaml:')
    
    def load(self, source: str) -> Dict[str, str]:
        """Load secrets from YAML file."""
        try:
            if source.startswith('yaml:'):
                # Parse YAML string directly
                data = yaml.safe_load(source[6:])
            else:
                # Load from file
                yaml_path = Path(source)
                if not yaml_path.exists():
                    raise FileNotFoundError(f"YAML file not found: {source}")
                
                with open(yaml_path, 'r') as f:
                    data = yaml.safe_load(f)
            
            # Convert to string values
            secrets = {}
            self._flatten_dict(data, secrets)
            
            logger.debug(f"Loaded {len(secrets)} secrets from {source}")
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to load YAML file {source}: {e}")
            raise
    
    def _flatten_dict(self, data: Any, result: Dict[str, str], prefix: str = ""):
        """Flatten nested dictionary."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}{key}" if prefix else key
                self._flatten_dict(value, result, f"{new_key}_")
        elif isinstance(data, (list, tuple)):
            for i, value in enumerate(data):
                new_key = f"{prefix}{i}" if prefix else str(i)
                self._flatten_dict(value, result, f"{new_key}_")
        else:
            result[prefix.rstrip('_')] = str(data)


class StdinLoader(SecretLoader):
    """Load secrets from stdin."""
    
    def can_load(self, source: str) -> bool:
        """Check if source is stdin."""
        return source.lower() in ['stdin', '-', 'pipe']
    
    def load(self, source: str) -> Dict[str, str]:
        """Load secrets from stdin."""
        try:
            # Read from stdin
            content = sys.stdin.read().strip()
            if not content:
                return {}
            
            # Try to parse as different formats
            secrets = {}
            
            # Try JSON first
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    secrets.update(data)
                    logger.debug(f"Loaded {len(secrets)} secrets from stdin (JSON)")
                    return secrets
            except json.JSONDecodeError:
                pass
            
            # Try YAML
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    secrets.update(data)
                    logger.debug(f"Loaded {len(secrets)} secrets from stdin (YAML)")
                    return secrets
            except yaml.YAMLError:
                pass
            
            # Try key=value format
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    secrets[key.strip()] = value.strip()
            
            logger.debug(f"Loaded {len(secrets)} secrets from stdin (key=value)")
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to load secrets from stdin: {e}")
            raise


class EnvironmentLoader(SecretLoader):
    """Load secrets from environment variables."""
    
    def can_load(self, source: str) -> bool:
        """Check if source is environment."""
        return source.lower() in ['env', 'environment', 'os']
    
    def load(self, source: str) -> Dict[str, str]:
        """Load secrets from environment variables."""
        try:
            # Get all environment variables
            secrets = dict(os.environ)
            
            logger.debug(f"Loaded {len(secrets)} environment variables")
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to load environment variables: {e}")
            raise


class LoaderManager:
    """Manages multiple secret loaders."""
    
    def __init__(self):
        self.loaders: List[SecretLoader] = [
            EnvFileLoader(),
            JsonLoader(),
            YamlLoader(),
            StdinLoader(),
            EnvironmentLoader(),
        ]
    
    def load_secrets(self, source: str) -> Dict[str, str]:
        """Load secrets from source using appropriate loader."""
        for loader in self.loaders:
            if loader.can_load(source):
                return loader.load(source)
        
        raise ValueError(f"No loader found for source: {source}")
    
    def load_multiple_sources(self, sources: List[str]) -> Dict[str, str]:
        """Load secrets from multiple sources."""
        all_secrets = {}
        
        for source in sources:
            try:
                secrets = self.load_secrets(source)
                all_secrets.update(secrets)
                logger.debug(f"Loaded {len(secrets)} secrets from {source}")
            except Exception as e:
                logger.error(f"Failed to load from {source}: {e}")
                raise
        
        return all_secrets
    
    def add_loader(self, loader: SecretLoader) -> None:
        """Add a custom loader."""
        self.loaders.append(loader)
        logger.debug(f"Added custom loader: {loader.__class__.__name__}")
    
    def get_available_loaders(self) -> List[str]:
        """Get list of available loader types."""
        return [loader.__class__.__name__ for loader in self.loaders] 