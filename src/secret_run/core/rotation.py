"""Advanced secret rotation and management capabilities."""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
from pydantic import BaseModel, Field

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RotationPolicy(BaseModel):
    """Defines how secrets should be rotated."""
    
    name: str = Field(..., description="Policy name")
    secret_pattern: str = Field(..., description="Regex pattern to match secrets")
    rotation_interval: int = Field(..., description="Rotation interval in days")
    warning_days: int = Field(default=7, description="Days before expiry to warn")
    auto_rotate: bool = Field(default=False, description="Automatically rotate secrets")
    rotation_method: str = Field(default="random", description="Rotation method: random, incremental, hash")
    min_length: int = Field(default=16, description="Minimum secret length")
    complexity_requirements: Dict[str, bool] = Field(
        default_factory=lambda: {
            "uppercase": True,
            "lowercase": True,
            "digits": True,
            "special": True
        }
    )


class SecretMetadata(BaseModel):
    """Metadata for secret tracking and rotation."""
    
    key: str = Field(..., description="Secret key")
    created_at: datetime = Field(default_factory=datetime.now)
    last_rotated: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    rotation_count: int = Field(default=0)
    hash: str = Field(..., description="Hash of the secret value")
    policy: Optional[str] = Field(default=None, description="Associated rotation policy")
    tags: List[str] = Field(default_factory=list)
    usage_count: int = Field(default=0)
    last_used: Optional[datetime] = Field(default=None)


class SecretRotator:
    """Handles secret rotation and lifecycle management."""
    
    def __init__(self, metadata_file: Optional[Path] = None):
        self.metadata_file = metadata_file or Path.home() / ".config" / "secret-run" / "secret-metadata.json"
        self.metadata: Dict[str, SecretMetadata] = {}
        self.policies: Dict[str, RotationPolicy] = {}
        self._load_metadata()
        self._setup_default_policies()
    
    def _load_metadata(self) -> None:
        """Load secret metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for key, meta_data in data.items():
                        self.metadata[key] = SecretMetadata(**meta_data)
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save secret metadata to file."""
        try:
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, 'w') as f:
                json.dump(
                    {k: v.model_dump() for k, v in self.metadata.items()},
                    f, indent=2, default=str
                )
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _setup_default_policies(self) -> None:
        """Setup default rotation policies."""
        self.policies.update({
            "api_keys": RotationPolicy(
                name="api_keys",
                secret_pattern=r"^.*_API_KEY$",
                rotation_interval=90,
                warning_days=14,
                auto_rotate=True,
                min_length=32
            ),
            "passwords": RotationPolicy(
                name="passwords",
                secret_pattern=r"^.*_PASSWORD$",
                rotation_interval=30,
                warning_days=7,
                auto_rotate=False,
                min_length=16,
                complexity_requirements={
                    "uppercase": True,
                    "lowercase": True,
                    "digits": True,
                    "special": True
                }
            ),
            "tokens": RotationPolicy(
                name="tokens",
                secret_pattern=r"^.*_TOKEN$",
                rotation_interval=60,
                warning_days=10,
                auto_rotate=True,
                min_length=24
            )
        })
    
    def add_secret(self, key: str, value: str, policy: Optional[str] = None, tags: Optional[List[str]] = None) -> None:
        """Add a secret with metadata tracking."""
        secret_hash = hashlib.sha256(value.encode()).hexdigest()
        
        # Determine policy based on key pattern
        if not policy:
            for pol_name, pol in self.policies.items():
                if pol.secret_pattern and any(key.upper().endswith(suffix) for suffix in pol.secret_pattern.split('|')):
                    policy = pol_name
                    break
        
        # Create or update metadata
        if key in self.metadata:
            meta = self.metadata[key]
            meta.last_rotated = datetime.now()
            meta.rotation_count += 1
            meta.hash = secret_hash
            if policy:
                meta.policy = policy
            if tags:
                meta.tags.extend(tags)
        else:
            meta = SecretMetadata(
                key=key,
                hash=secret_hash,
                policy=policy,
                tags=tags or []
            )
            self.metadata[key] = meta
        
        # Set expiry if policy exists
        if policy and policy in self.policies:
            pol = self.policies[policy]
            meta.expires_at = datetime.now() + timedelta(days=pol.rotation_interval)
        
        self._save_metadata()
        logger.info(f"Added secret '{key}' with policy '{policy}'")
    
    def get_expiring_secrets(self, days: int = 30) -> List[SecretMetadata]:
        """Get secrets that will expire within the specified days."""
        cutoff = datetime.now() + timedelta(days=days)
        return [
            meta for meta in self.metadata.values()
            if meta.expires_at and meta.expires_at <= cutoff
        ]
    
    def get_expired_secrets(self) -> List[SecretMetadata]:
        """Get secrets that have already expired."""
        now = datetime.now()
        return [
            meta for meta in self.metadata.values()
            if meta.expires_at and meta.expires_at <= now
        ]
    
    def generate_rotated_secret(self, key: str, method: str = "random") -> str:
        """Generate a new secret value for rotation."""
        import secrets
        import string
        
        if key not in self.metadata:
            raise ValueError(f"No metadata found for secret '{key}'")
        
        meta = self.metadata[key]
        policy = self.policies.get(meta.policy) if meta.policy else None
        
        if method == "random":
            return self._generate_random_secret(policy)
        elif method == "incremental":
            return self._generate_incremental_secret(key, meta, policy)
        elif method == "hash":
            return self._generate_hash_based_secret(key, meta, policy)
        else:
            raise ValueError(f"Unknown rotation method: {method}")
    
    def _generate_random_secret(self, policy: Optional[RotationPolicy]) -> str:
        """Generate a random secret based on policy requirements."""
        import secrets
        import string
        
        min_length = policy.min_length if policy else 16
        complexity = policy.complexity_requirements if policy else {}
        
        # Build character set based on complexity requirements
        chars = ""
        if complexity.get("lowercase", True):
            chars += string.ascii_lowercase
        if complexity.get("uppercase", True):
            chars += string.ascii_uppercase
        if complexity.get("digits", True):
            chars += string.digits
        if complexity.get("special", True):
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        # Generate secret ensuring minimum length
        secret = ''.join(secrets.choice(chars) for _ in range(min_length))
        
        # Ensure complexity requirements are met
        if policy and policy.complexity_requirements:
            if complexity.get("uppercase") and not any(c.isupper() for c in secret):
                secret = secrets.choice(string.ascii_uppercase) + secret[1:]
            if complexity.get("lowercase") and not any(c.islower() for c in secret):
                secret = secrets.choice(string.ascii_lowercase) + secret[1:]
            if complexity.get("digits") and not any(c.isdigit() for c in secret):
                secret = secrets.choice(string.digits) + secret[1:]
            if complexity.get("special") and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret):
                secret = secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?") + secret[1:]
        
        return secret
    
    def _generate_incremental_secret(self, key: str, meta: SecretMetadata, policy: Optional[RotationPolicy]) -> str:
        """Generate an incremental secret based on previous value."""
        # This is a simplified version - in practice, you'd want more sophisticated logic
        base = f"{key}_{meta.rotation_count}_{int(time.time())}"
        return hashlib.sha256(base.encode()).hexdigest()[:policy.min_length if policy else 16]
    
    def _generate_hash_based_secret(self, key: str, meta: SecretMetadata, policy: Optional[RotationPolicy]) -> str:
        """Generate a secret based on hashing the key and rotation count."""
        base = f"{key}_{meta.rotation_count}_{int(time.time())}"
        return hashlib.sha256(base.encode()).hexdigest()[:policy.min_length if policy else 16]
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate a secret with a new value."""
        if key not in self.metadata:
            return False
        
        meta = self.metadata[key]
        meta.last_rotated = datetime.now()
        meta.rotation_count += 1
        meta.hash = hashlib.sha256(new_value.encode()).hexdigest()
        
        # Update expiry if policy exists
        if meta.policy and meta.policy in self.policies:
            pol = self.policies[meta.policy]
            meta.expires_at = datetime.now() + timedelta(days=pol.rotation_interval)
        
        self._save_metadata()
        logger.info(f"Rotated secret '{key}' (rotation #{meta.rotation_count})")
        return True
    
    def get_rotation_report(self) -> Dict[str, Any]:
        """Generate a comprehensive rotation report."""
        now = datetime.now()
        expired = self.get_expired_secrets()
        expiring_soon = self.get_expiring_secrets(7)
        expiring_month = self.get_expiring_secrets(30)
        
        return {
            "total_secrets": len(self.metadata),
            "expired_secrets": len(expired),
            "expiring_soon": len(expiring_soon),
            "expiring_month": len(expiring_month),
            "policies": {name: pol.model_dump() for name, pol in self.policies.items()},
            "expired_details": [meta.model_dump() for meta in expired],
            "expiring_soon_details": [meta.model_dump() for meta in expiring_soon],
            "generated_at": now.isoformat()
        }
    
    async def auto_rotate_expired(self) -> List[str]:
        """Automatically rotate expired secrets that have auto-rotate enabled."""
        expired = self.get_expired_secrets()
        rotated = []
        
        for meta in expired:
            if meta.policy and meta.policy in self.policies:
                policy = self.policies[meta.policy]
                if policy.auto_rotate:
                    try:
                        new_value = self.generate_rotated_secret(meta.key, policy.rotation_method)
                        if self.rotate_secret(meta.key, new_value):
                            rotated.append(meta.key)
                    except Exception as e:
                        logger.error(f"Failed to auto-rotate secret '{meta.key}': {e}")
        
        return rotated 