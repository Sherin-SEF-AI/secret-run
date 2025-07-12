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
    validation_issues = validator.validate_secrets(
        secrets, 
        required_keys=["API_KEY", "DATABASE_URL"]
    )
    
    if validation_issues['errors']:
        print("   ❌ Validation errors found:")
        for error in validation_issues['errors']:
            print(f"      • {error}")
    else:
        print("   ✅ All secrets passed validation")
    
    if validation_issues['warnings']:
        print("   ⚠️  Validation warnings:")
        for warning in validation_issues['warnings']:
            print(f"      • {warning}")
    
    # Create execution configuration
    print("\n5. Setting up execution...")
    exec_config = ExecutionConfig(
        timeout=30,
        working_dir=Path.cwd(),
        inherit_env=True,
        mask_output=True
    )
    
    # Execute a simple command
    print("\n6. Executing command with secrets...")
    command = ["echo", "Hello from secret-run!"]
    
    try:
        result = await executor.execute(command, secrets, exec_config)
        
        if result.success:
            print("   ✅ Command executed successfully")
            print(f"   Return code: {result.return_code}")
            print(f"   Execution time: {result.execution_time:.2f}s")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print("   ❌ Command failed")
            print(f"   Return code: {result.return_code}")
            if result.error_message:
                print(f"   Error: {result.error_message}")
    
    except Exception as e:
        print(f"   ❌ Execution failed: {e}")
    
    # Show system information
    print("\n7. System information...")
    system_info = platform_manager.get_system_info()
    print(f"   OS: {system_info['system']} {system_info['release']}")
    print(f"   Python: {system_info['python_version'].split()[0]}")
    print(f"   Architecture: {system_info['machine']}")
    
    # Cleanup
    print("\n8. Cleaning up...")
    executor.cleanup()
    security_manager.cleanup()
    print("   ✅ Cleanup completed")
    
    print("\n🎉 Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 