"""Secret Run - Secure command execution with temporary secret injection."""

__version__ = "0.1.0"
__author__ = "sherin joseph roy"
__email__ = "sherin.joseph2217@gmail.com"

from .core.executor import SecretExecutor
from .core.secrets import SecretManager
from .core.loaders import SecretLoader
from .core.validators import SecretValidator
from .core.security import SecurityManager
from .core.rotation import SecretRotator, RotationPolicy, SecretMetadata
from .core.cloud_integrations import (
    CloudIntegrationManager,
    AWSIntegration,
    GCPIntegration,
    AzureIntegration,
    VaultIntegration
)

__all__ = [
    "SecretExecutor",
    "SecretManager", 
    "SecretLoader",
    "SecretValidator",
    "SecurityManager",
    "SecretRotator",
    "RotationPolicy", 
    "SecretMetadata",
    "CloudIntegrationManager",
    "AWSIntegration",
    "GCPIntegration",
    "AzureIntegration",
    "VaultIntegration",
] 