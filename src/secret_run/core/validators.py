"""Secret validation utilities."""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ValidationRule:
    """Base class for validation rules."""
    
    def validate(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Validate a secret value."""
        raise NotImplementedError


class RequiredRule(ValidationRule):
    """Rule to check if a secret is required."""
    
    def __init__(self, required_keys: List[str]):
        self.required_keys = set(required_keys)
    
    def validate(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Check if key is required."""
        if key in self.required_keys and not value.strip():
            return False, f"Required secret '{key}' is empty"
        return True, None


class PatternRule(ValidationRule):
    """Rule to validate against patterns."""
    
    def __init__(self, patterns: Dict[str, str]):
        self.patterns = patterns
    
    def validate(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Validate value against pattern."""
        if key in self.patterns:
            pattern = self.patterns[key]
            if not re.match(pattern, value):
                return False, f"Secret '{key}' does not match pattern '{pattern}'"
        return True, None


class LengthRule(ValidationRule):
    """Rule to validate length constraints."""
    
    def __init__(self, min_length: Optional[int] = None, max_length: Optional[int] = None):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Validate value length."""
        length = len(value)
        
        if self.min_length and length < self.min_length:
            return False, f"Secret '{key}' is too short (min: {self.min_length})"
        
        if self.max_length and length > self.max_length:
            return False, f"Secret '{key}' is too long (max: {self.max_length})"
        
        return True, None


class PasswordStrengthRule(ValidationRule):
    """Rule to validate password strength."""
    
    def __init__(self, min_length: int = 8, require_upper: bool = True, 
                 require_lower: bool = True, require_digit: bool = True, 
                 require_special: bool = True):
        self.min_length = min_length
        self.require_upper = require_upper
        self.require_lower = require_lower
        self.require_digit = require_digit
        self.require_special = require_special
    
    def validate(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Validate password strength."""
        # Only apply to password-like keys
        if not any(key.lower().endswith(suffix) for suffix in ['password', 'pass', 'pwd']):
            return True, None
        
        issues = []
        
        if len(value) < self.min_length:
            issues.append(f"at least {self.min_length} characters")
        
        if self.require_upper and not any(c.isupper() for c in value):
            issues.append("uppercase letter")
        
        if self.require_lower and not any(c.islower() for c in value):
            issues.append("lowercase letter")
        
        if self.require_digit and not any(c.isdigit() for c in value):
            issues.append("digit")
        
        if self.require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in value):
            issues.append("special character")
        
        if issues:
            return False, f"Password '{key}' must contain: {', '.join(issues)}"
        
        return True, None


class DuplicateRule(ValidationRule):
    """Rule to check for duplicate secrets."""
    
    def __init__(self):
        self.seen_values: Set[str] = set()
    
    def validate(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Check for duplicate values."""
        if value in self.seen_values:
            return False, f"Secret '{key}' has duplicate value"
        
        self.seen_values.add(value)
        return True, None


class SecretValidator:
    """Validates secrets against various rules."""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules."""
        self.add_rule(LengthRule(min_length=1))
        self.add_rule(PasswordStrengthRule())
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules.append(rule)
        logger.debug(f"Added validation rule: {rule.__class__.__name__}")
    
    def validate_secrets(self, secrets: Dict[str, str], **kwargs) -> Dict[str, List[str]]:
        """Validate all secrets."""
        issues = {
            'errors': [],
            'warnings': [],
        }
        
        # Add context-specific rules
        if 'required_keys' in kwargs:
            self.add_rule(RequiredRule(kwargs['required_keys']))
        
        if 'patterns' in kwargs:
            self.add_rule(PatternRule(kwargs['patterns']))
        
        if kwargs.get('check_duplicates', False):
            self.add_rule(DuplicateRule())
        
        # Validate each secret
        for key, value in secrets.items():
            for rule in self.rules:
                is_valid, message = rule.validate(key, value)
                if not is_valid:
                    issues['errors'].append(f"{key}: {message}")
        
        return issues
    
    def validate_schema(self, secrets: Dict[str, str], schema: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate secrets against a schema."""
        issues = {
            'errors': [],
            'warnings': [],
        }
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in secrets:
                issues['errors'].append(f"Missing required field: {field}")
        
        # Check field types and constraints
        properties = schema.get('properties', {})
        for field, value in secrets.items():
            if field in properties:
                field_schema = properties[field]
                
                # Check type
                expected_type = field_schema.get('type')
                if expected_type == 'string' and not isinstance(value, str):
                    issues['errors'].append(f"Field '{field}' must be a string")
                
                # Check pattern
                pattern = field_schema.get('pattern')
                if pattern and not re.match(pattern, value):
                    issues['errors'].append(f"Field '{field}' does not match pattern")
                
                # Check min/max length
                min_length = field_schema.get('minLength')
                if min_length and len(value) < min_length:
                    issues['errors'].append(f"Field '{field}' is too short (min: {min_length})")
                
                max_length = field_schema.get('maxLength')
                if max_length and len(value) > max_length:
                    issues['errors'].append(f"Field '{field}' is too long (max: {max_length})")
        
        return issues
    
    def check_secret_patterns(self, secrets: Dict[str, str]) -> Dict[str, List[str]]:
        """Check for common secret patterns."""
        patterns = {
            'api_key': r'^[a-zA-Z0-9]{32,}$',
            'jwt_secret': r'^[a-zA-Z0-9+/]{32,}={0,2}$',
            'database_url': r'^[a-zA-Z]+://',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        }
        
        results = {
            'matches': {},
            'suggestions': [],
        }
        
        for key, value in secrets.items():
            for pattern_name, pattern in patterns.items():
                if re.match(pattern, value):
                    if key not in results['matches']:
                        results['matches'][key] = []
                    results['matches'][key].append(pattern_name)
        
        # Generate suggestions
        for key, value in secrets.items():
            if key.lower().endswith('_key') and len(value) >= 32:
                results['suggestions'].append(f"'{key}' looks like an API key")
            
            if key.lower().endswith('_password') and len(value) < 8:
                results['suggestions'].append(f"'{key}' password might be too weak")
        
        return results
    
    def generate_report(self, validation_results: Dict[str, List[str]]) -> str:
        """Generate a human-readable validation report."""
        report = []
        
        if validation_results['errors']:
            report.append("❌ Validation Errors:")
            for error in validation_results['errors']:
                report.append(f"  • {error}")
        
        if validation_results['warnings']:
            report.append("⚠️  Validation Warnings:")
            for warning in validation_results['warnings']:
                report.append(f"  • {warning}")
        
        if not validation_results['errors'] and not validation_results['warnings']:
            report.append("✅ All secrets passed validation")
        
        return '\n'.join(report) 