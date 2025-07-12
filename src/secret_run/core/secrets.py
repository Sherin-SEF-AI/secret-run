"""Secret management and processing utilities."""

import base64
import json
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ..utils.logging import get_logger

logger = get_logger(__name__)


class Secret(BaseModel):
    """Represents a single secret."""
    
    key: str = Field(..., description="Secret key/name")
    value: str = Field(..., description="Secret value")
    source: str = Field(default="unknown", description="Source of the secret")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def model_post_init(self, __context):
        """Validate secret after initialization."""
        if not self.key or not self.key.strip():
            raise ValueError("Secret key cannot be empty")
        
        if not self.value or not self.value.strip():
            raise ValueError("Secret value cannot be empty")


class SecretManager:
    """Manages secrets with validation and transformation capabilities."""
    
    def __init__(self):
        self.secrets: Dict[str, Secret] = {}
        self.transformations: Dict[str, callable] = {}
        self._setup_default_transformations()
    
    def _setup_default_transformations(self):
        """Setup default secret transformations."""
        self.transformations.update({
            'base64_decode': self._base64_decode,
            'json_parse': self._json_parse,
            'url_encode': self._url_encode,
            'template_substitute': self._template_substitute,
        })
    
    def add_secret(self, key: str, value: str, source: str = "unknown", **metadata) -> None:
        """Add a secret to the manager."""
        secret = Secret(key=key, value=value, source=source, metadata=metadata)
        self.secrets[key] = secret
        logger.debug(f"Added secret '{key}' from source '{source}'")
    
    def add_secrets(self, secrets: Dict[str, str], source: str = "unknown") -> None:
        """Add multiple secrets at once."""
        for key, value in secrets.items():
            self.add_secret(key, value, source)
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value by key."""
        secret = self.secrets.get(key)
        return secret.value if secret else None
    
    def get_secrets(self) -> Dict[str, str]:
        """Get all secrets as a dictionary."""
        return {key: secret.value for key, secret in self.secrets.items()}
    
    def remove_secret(self, key: str) -> bool:
        """Remove a secret by key."""
        if key in self.secrets:
            del self.secrets[key]
            logger.debug(f"Removed secret '{key}'")
            return True
        return False
    
    def clear_secrets(self) -> None:
        """Clear all secrets."""
        self.secrets.clear()
        logger.debug("Cleared all secrets")
    
    def validate_secrets(self, required_keys: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """Validate secrets and return any issues."""
        issues = {
            'missing': [],
            'invalid': [],
            'weak': [],
        }
        
        # Check for required keys
        if required_keys:
            for key in required_keys:
                if key not in self.secrets:
                    issues['missing'].append(key)
        
        # Validate existing secrets
        for key, secret in self.secrets.items():
            # Check for empty values
            if not secret.value.strip():
                issues['invalid'].append(f"{key}: empty value")
            
            # Check for weak passwords
            if self._is_weak_password(key, secret.value):
                issues['weak'].append(f"{key}: weak password")
        
        return issues
    
    def _is_weak_password(self, key: str, value: str) -> bool:
        """Check if a secret is a weak password."""
        if not any(key.lower().endswith(suffix) for suffix in ['password', 'pass', 'pwd']):
            return False
        
        # Check length
        if len(value) < 8:
            return True
        
        # Check complexity
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in value)
        
        return not (has_upper and has_lower and has_digit and has_special)
    
    def transform_secret(self, key: str, transformation: str, **kwargs) -> bool:
        """Apply a transformation to a secret."""
        if key not in self.secrets:
            logger.warning(f"Secret '{key}' not found for transformation")
            return False
        
        if transformation not in self.transformations:
            logger.warning(f"Unknown transformation '{transformation}'")
            return False
        
        try:
            secret = self.secrets[key]
            transformed_value = self.transformations[transformation](secret.value, **kwargs)
            secret.value = transformed_value
            secret.metadata['transformations'] = secret.metadata.get('transformations', [])
            secret.metadata['transformations'].append(transformation)
            logger.debug(f"Applied transformation '{transformation}' to secret '{key}'")
            return True
        except Exception as e:
            logger.error(f"Failed to transform secret '{key}': {e}")
            return False
    
    def _base64_decode(self, value: str, **kwargs) -> str:
        """Base64 decode a value."""
        try:
            decoded = base64.b64decode(value).decode('utf-8')
            return decoded
        except Exception as e:
            raise ValueError(f"Invalid base64 value: {e}")
    
    def _json_parse(self, value: str, **kwargs) -> str:
        """Parse JSON value."""
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                # If it's a dict, return as JSON string
                return json.dumps(parsed)
            return str(parsed)
        except Exception as e:
            raise ValueError(f"Invalid JSON value: {e}")
    
    def _url_encode(self, value: str, **kwargs) -> str:
        """URL encode a value."""
        import urllib.parse
        return urllib.parse.quote(value)
    
    def _template_substitute(self, value: str, **kwargs) -> str:
        """Substitute template variables in a value."""
        # Simple template substitution using ${VAR} syntax
        def substitute(match):
            var_name = match.group(1)
            return self.get_secret(var_name) or match.group(0)
        
        return re.sub(r'\$\{([^}]+)\}', substitute, value)
    
    def apply_prefix(self, prefix: str) -> None:
        """Apply prefix to all secret keys."""
        new_secrets = {}
        for key, secret in self.secrets.items():
            new_key = f"{prefix}{key}"
            secret.key = new_key
            new_secrets[new_key] = secret
        self.secrets = new_secrets
        logger.debug(f"Applied prefix '{prefix}' to all secrets")
    
    def apply_suffix(self, suffix: str) -> None:
        """Apply suffix to all secret keys."""
        new_secrets = {}
        for key, secret in self.secrets.items():
            new_key = f"{key}{suffix}"
            secret.key = new_key
            new_secrets[new_key] = secret
        self.secrets = new_secrets
        logger.debug(f"Applied suffix '{suffix}' to all secrets")
    
    def filter_secrets(self, include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None) -> Dict[str, str]:
        """Filter secrets based on patterns."""
        filtered = {}
        
        for key, secret in self.secrets.items():
            # Check include pattern
            if include_pattern and not re.search(include_pattern, key):
                continue
            
            # Check exclude pattern
            if exclude_pattern and re.search(exclude_pattern, key):
                continue
            
            filtered[key] = secret.value
        
        return filtered
    
    def get_secret_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all secrets."""
        info = {}
        for key, secret in self.secrets.items():
            info[key] = {
                'source': secret.source,
                'length': len(secret.value),
                'metadata': secret.metadata,
                'has_transformations': bool(secret.metadata.get('transformations')),
            }
        return info 