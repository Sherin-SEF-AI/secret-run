#!/usr/bin/env python3
"""
Basic usage example for secret-run.

This example demonstrates how to use the secret-run library programmatically.
"""

import asyncio
import os
from pathlib import Path

# Add the src directory to the Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_run.core.executor import SecretExecutor, ExecutionConfig
from secret_run.core.secrets import SecretManager
from secret_run.core.loaders import LoaderManager
from secret_run.core.security import SecurityManager
from secret_run.core.validators import SecretValidator
from secret_run.utils.config import ConfigManager
from secret_run.utils.platform import PlatformManager


async def main():
    """Main example function."""
    print("🚀 Secret Run - Basic Usage Example")
    print("=" * 50)
    
    # Initialize managers
    print("\n1. Initializing managers...")
    config_manager = ConfigManager()
    platform_manager = PlatformManager()
    security_manager = SecurityManager()
    secret_manager = SecretManager()
    loader_manager = LoaderManager()
    validator = SecretValidator()
    executor = SecretExecutor(security_manager)
    
    # Load configuration
    print("\n2. Loading configuration...")
    config = config_manager.load_config()
    print(f"   Default profile: {config.get('default_profile', 'default')}")
    print(f"   Log level: {config.get('logging.level', 'INFO')}")
    
    # Add some secrets
    print("\n3. Adding secrets...")
    secrets = {
        "API_KEY": "sk_live_1234567890abcdef1234567890abcdef",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/mydb",
        "JWT_SECRET": "my-super-secret-jwt-key",
        "DEBUG": "false"
    }
    
    secret_manager.add_secrets(secrets, "example")
    print(f"   Added {len(secrets)} secrets")
    
    # Validate secrets
    print("\n4. Validating secrets...")
    validation_results = validator.validate_secrets(secrets)
    if validation_results['errors']:
        print(f"   Validation errors: {validation_results['errors']}")
    else:
        print("   All secrets passed validation")
    
    # Execute a command with secrets
    print("\n5. Executing command with secrets...")
    exec_config = ExecutionConfig(
        timeout=30,
        working_dir=Path.cwd()
    )
    
    try:
        result = await executor.execute(
            command=["echo", "API_KEY is set"],
            secrets=secret_manager.get_secrets(),
            config=exec_config
        )
        print(f"   Command executed successfully")
        print(f"   Exit code: {result.return_code}")
        print(f"   Output: {result.stdout}")
    except Exception as e:
        print(f"   Command execution failed: {e}")
    
    # Demonstrate secret transformations
    print("\n6. Secret transformations...")
    secret_manager.add_secret("BASE64_VALUE", "SGVsbG8gV29ybGQ=", "example")
    secret_manager.transform_secret("BASE64_VALUE", "base64_decode")
    decoded_value = secret_manager.get_secret("BASE64_VALUE")
    print(f"   Base64 decoded: {decoded_value}")
    
    # Show platform information
    print("\n7. Platform information...")
    platform_info = platform_manager.get_system_info()
    print(f"   OS: {platform_info['system']}")
    print(f"   Architecture: {platform_info['machine']}")
    print(f"   Python version: {platform_info['python_version'].split()[0]}")
    
    print("\n✅ Basic usage example completed!")
    print("\n📝 Note: For advanced features like secret rotation and cloud integrations,")
    print("   use the demo scripts:")
    print("   - ./demo_showcase.sh (single-key demo)")
    print("   - ./multi_key_demo.sh (multi-key demo)")
    print("\n🔑 Important: Secret metadata must be registered before rotation operations.")


if __name__ == "__main__":
    asyncio.run(main()) 