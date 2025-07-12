#!/usr/bin/env python3
"""
Advanced features example for secret-run.

This example demonstrates the advanced features including:
- Secret rotation and lifecycle management
- Cloud integrations
- Advanced secret generation
- Policy management
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_run.core.rotation import SecretRotator, RotationPolicy
from secret_run.core.cloud_integrations import (
    CloudIntegrationManager,
    AWSIntegration,
    GCPIntegration
)
from secret_run.core.secrets import SecretManager
from secret_run.utils.logging import setup_logging


async def main():
    """Main example function demonstrating advanced features."""
    print("🚀 Secret Run - Advanced Features Example")
    print("=" * 60)
    
    # Setup logging
    setup_logging(level="INFO")
    
    # 1. Secret Rotation and Lifecycle Management
    print("\n1. 🔄 Secret Rotation and Lifecycle Management")
    print("-" * 50)
    
    rotator = SecretRotator()
    
    # Add some secrets with different policies
    secrets_data = {
        "API_KEY_PROD": "sk_live_1234567890abcdef1234567890abcdef",
        "DATABASE_PASSWORD": "SuperSecurePass123!",
        "JWT_SECRET": "my-super-secret-jwt-key-for-production",
        "REDIS_PASSWORD": "redis-secure-password-456",
    }
    
    for key, value in secrets_data.items():
        rotator.add_secret(key, value)
    
    print(f"Added {len(secrets_data)} secrets to rotation manager")
    
    # Generate rotation report
    report = rotator.get_rotation_report()
    print(f"Total secrets: {report['total_secrets']}")
    print(f"Expired secrets: {report['expired_secrets']}")
    print(f"Expiring soon: {report['expiring_soon']}")
    
    # Create a custom rotation policy
    custom_policy = RotationPolicy(
        name="custom_api_keys",
        secret_pattern=r"^CUSTOM_.*_KEY$",
        rotation_interval=45,
        warning_days=10,
        auto_rotate=True,
        rotation_method="random",
        min_length=32
    )
    rotator.policies["custom_api_keys"] = custom_policy
    print(f"Created custom policy: {custom_policy.name}")
    
    # Generate a new secret
    rotator.add_secret("NEW_API_KEY", "placeholder", "example")  # Add to metadata first
    new_secret = rotator.generate_rotated_secret("NEW_API_KEY", "random")
    print(f"Generated new secret: {new_secret[:10]}...")
    
    # 2. Cloud Integrations
    print("\n2. ☁️ Cloud Integrations")
    print("-" * 50)
    
    cloud_manager = CloudIntegrationManager()
    
    # Example AWS integration (commented out as it requires credentials)
    """
    aws_integration = AWSIntegration(
        name="production-aws",
        region="us-east-1",
        profile="default",
        secret_prefix="/secret-run/prod/"
    )
    cloud_manager.add_integration(aws_integration)
    print("Added AWS integration")
    """
    
    # Example GCP integration (commented out as it requires credentials)
    """
    gcp_integration = GCPIntegration(
        name="production-gcp",
        project_id="my-gcp-project"
    )
    cloud_manager.add_integration(gcp_integration)
    print("Added GCP integration")
    """
    
    print("Cloud integrations configured (examples commented out)")
    
    # 3. Advanced Secret Management
    print("\n3. 🔐 Advanced Secret Management")
    print("-" * 50)
    
    secret_manager = SecretManager()
    
    # Add secrets with transformations
    secret_manager.add_secret("BASE64_ENCODED", "U2VjcmV0VmFsdWU=", "example")
    secret_manager.add_secret("JSON_CONFIG", '{"api_key": "secret123", "debug": false}', "example")
    
    # Apply transformations
    import base64
    import json
    
    # Base64 decode
    encoded_value = secret_manager.get_secret("BASE64_ENCODED")
    if encoded_value:
        decoded_value = base64.b64decode(encoded_value).decode('utf-8')
        print(f"Base64 decoded: {decoded_value}")
    
    # JSON parse
    json_value = secret_manager.get_secret("JSON_CONFIG")
    if json_value:
        parsed_config = json.loads(json_value)
        print(f"JSON parsed: {parsed_config}")
    
    # 4. Policy Management
    print("\n4. 📋 Policy Management")
    print("-" * 50)
    
    # List all policies
    print("Available rotation policies:")
    for name, policy in rotator.policies.items():
        print(f"  • {name}: {policy.rotation_interval} days, auto-rotate: {policy.auto_rotate}")
    
    # 5. Secret Health Check
    print("\n5. 🏥 Secret Health Check")
    print("-" * 50)
    
    expired = rotator.get_expired_secrets()
    expiring_soon = rotator.get_expiring_secrets(7)
    
    if expired:
        print(f"⚠️  {len(expired)} expired secrets found:")
        for secret in expired:
            print(f"    • {secret.key} (expired: {secret.expires_at})")
    else:
        print("✅ No expired secrets")
    
    if expiring_soon:
        print(f"⚠️  {len(expiring_soon)} secrets expiring soon:")
        for secret in expiring_soon:
            print(f"    • {secret.key} (expires: {secret.expires_at})")
    else:
        print("✅ No secrets expiring soon")
    
    # 6. Advanced Usage Examples
    print("\n6. 💡 Advanced Usage Examples")
    print("-" * 50)
    
    print("CLI Commands you can now use:")
    print("  • secret-run rotate status --days 30")
    print("  • secret-run rotate generate --key NEW_SECRET --method random")
    print("  • secret-run rotate auto-rotate --dry-run")
    print("  • secret-run cloud list")
    print("  • secret-run cloud add-aws --name prod --region us-east-1")
    print("  • secret-run cloud get --secret my-secret --format json")
    
    print("\n🎉 Advanced features demonstration completed!")
    print("\nKey Features Added:")
    print("  ✅ Secret rotation with policies")
    print("  ✅ Cloud integrations (AWS, GCP, Azure, Vault)")
    print("  ✅ Advanced secret generation")
    print("  ✅ Lifecycle management")
    print("  ✅ Health monitoring")
    print("  ✅ Policy management")
    print("  ✅ Multi-cloud secret sync")


if __name__ == "__main__":
    asyncio.run(main()) 