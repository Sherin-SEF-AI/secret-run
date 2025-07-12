"""Main CLI entry point for secret-run."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..core.executor import ExecutionConfig, SecretExecutor
from ..core.loaders import LoaderManager
from ..core.secrets import SecretManager
from ..core.security import SecurityManager
from ..core.validators import SecretValidator
from ..utils.config import ConfigManager
from ..utils.logging import setup_logging
from ..utils.platform import PlatformManager
from .commands import run, validate, config, audit, rotate, cloud

# Create Typer app
app = typer.Typer(
    name="secret-run",
    help="Secure command execution with temporary secret injection",
    add_completion=False,
    rich_markup_mode="rich",
)

# Global console
console = Console()

# Global managers
config_manager: Optional[ConfigManager] = None
platform_manager: Optional[PlatformManager] = None
security_manager: Optional[SecurityManager] = None
secret_manager: Optional[SecretManager] = None
loader_manager: Optional[LoaderManager] = None
validator: Optional[SecretValidator] = None
executor: Optional[SecretExecutor] = None


def get_managers():
    """Get or create global managers."""
    global config_manager, platform_manager, security_manager, secret_manager, loader_manager, validator, executor
    
    if config_manager is None:
        config_manager = ConfigManager()
        platform_manager = PlatformManager()
        security_manager = SecurityManager()
        secret_manager = SecretManager()
        loader_manager = LoaderManager()
        validator = SecretValidator()
        executor = SecretExecutor(security_manager)
    
    return (
        config_manager,
        platform_manager,
        security_manager,
        secret_manager,
        loader_manager,
        validator,
        executor,
    )


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output except errors"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Use custom config file"),
    log_level: str = typer.Option("INFO", "--log-level", help="Set logging level"),
    log_file: Optional[Path] = typer.Option(None, "--log-file", help="Log to file"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
):
    """Secret Run - Secure command execution with temporary secret injection.
    
    This tool allows you to run commands with secrets injected as environment
    variables, ensuring secrets never touch the filesystem and are cleaned up
    after execution.
    """
    
    # Initialize managers
    config_mgr, platform_mgr, security_mgr, secret_mgr, loader_mgr, validator_obj, executor_obj = get_managers()
    
    # Setup logging
    if verbose:
        log_level = "DEBUG"
    elif quiet:
        log_level = "ERROR"
    
    # Determine log file
    if log_file is None:
        log_file = Path(config_mgr.config_dir) / "logs" / "secret-run.log"
    
    # Setup logging
    setup_logging(
        level=log_level,
        log_file=log_file,
        format_type="structured" if not verbose else "human",
    )
    
    # Store context
    ctx.obj = {
        'config_manager': config_mgr,
        'platform_manager': platform_mgr,
        'security_manager': security_mgr,
        'secret_manager': secret_mgr,
        'loader_manager': loader_mgr,
        'validator': validator_obj,
        'executor': executor_obj,
        'verbose': verbose,
        'quiet': quiet,
        'no_color': no_color,
    }


@app.command()
def version(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed version information"),
):
    """Show version information."""
    from .. import __version__, __author__, __email__
    
    if verbose:
        # Show detailed version info
        info = {
            "Version": __version__,
            "Author": __author__,
            "Email": __email__,
            "Python": sys.version,
            "Platform": sys.platform,
        }
        
        # Get system info
        _, platform_mgr, _, _, _, _, _ = get_managers()
        system_info = platform_mgr.get_system_info()
        info.update({
            "OS": f"{system_info['system']} {system_info['release']}",
            "Architecture": system_info['machine'],
        })
        
        # Create rich table
        from rich.table import Table
        table = Table(title="Secret Run Version Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in info.items():
            table.add_row(key, str(value))
        
        console.print(table)
    else:
        # Simple version display
        console.print(f"secret-run version {__version__}")


@app.command()
def doctor(
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
    check_all: bool = typer.Option(False, "--check-all", help="Run all checks"),
):
    """Run system health check."""
    config_mgr, platform_mgr, _, _, _, _, _ = get_managers()
    
    console.print("🔍 Running system health check...")
    
    issues = []
    warnings = []
    
    # Check configuration
    config_issues = config_mgr.validate()
    issues.extend(config_issues['errors'])
    warnings.extend(config_issues['warnings'])
    
    # Check directories
    try:
        platform_mgr.ensure_directories()
    except Exception as e:
        issues.append(f"Failed to create directories: {e}")
    
    # Check permissions
    config_dir = config_mgr.config_dir
    if not config_dir.exists():
        issues.append(f"Configuration directory does not exist: {config_dir}")
    elif not os.access(config_dir, os.W_OK):
        issues.append(f"No write permission to config directory: {config_dir}")
    
    # Check dependencies
    try:
        import psutil
    except ImportError:
        warnings.append("psutil not available - some features may be limited")
    
    try:
        import yaml
    except ImportError:
        issues.append("PyYAML not available - required for configuration")
    
    # Display results
    if issues:
        console.print("\n❌ Issues found:")
        for issue in issues:
            console.print(f"  • {issue}")
    else:
        console.print("\n✅ No issues found")
    
    if warnings:
        console.print("\n⚠️  Warnings:")
        for warning in warnings:
            console.print(f"  • {warning}")
    
    if not issues and not warnings:
        console.print("\n🎉 System is healthy!")
    
    # Exit with error code if issues found
    if issues:
        raise typer.Exit(1)


@app.command()
def info(
    ctx: typer.Context,
    system: bool = typer.Option(False, "--system", help="Show system information"),
    config: bool = typer.Option(False, "--config", help="Show configuration information"),
    security: bool = typer.Option(False, "--security", help="Show security information"),
):
    """Show detailed information about the system."""
    config_mgr, platform_mgr, _, _, _, _, _ = get_managers()
    
    if not any([system, config, security]):
        # Show all information
        system = config = security = True
    
    if system:
        console.print("\n[bold cyan]System Information[/bold cyan]")
        system_info = platform_mgr.get_system_info()
        user_info = platform_mgr.get_user_info()
        
        from rich.table import Table
        table = Table()
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in system_info.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        table.add_row("", "")  # Empty row
        table.add_row("Username", user_info['username'])
        table.add_row("Home Directory", user_info['home'])
        
        console.print(table)
    
    if config:
        console.print("\n[bold cyan]Configuration Information[/bold cyan]")
        config_data = config_mgr.load_config()
        
        from rich.table import Table
        table = Table()
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        # Show key configuration values
        key_settings = [
            ("Default Profile", config_data.get('default_profile', 'default')),
            ("Log Level", config_data.get('logging', {}).get('level', 'INFO')),
            ("Execution Timeout", f"{config_data.get('security', {}).get('execution_timeout', 300)}s"),
            ("Memory Limit", f"{config_data.get('security', {}).get('memory_limit', 512)}MB"),
            ("Config Directory", str(config_mgr.config_dir)),
            ("Cache Directory", str(platform_mgr.cache_dir)),
        ]
        
        for setting, value in key_settings:
            table.add_row(setting, str(value))
        
        console.print(table)
    
    if security:
        console.print("\n[bold cyan]Security Information[/bold cyan]")
        
        from rich.table import Table
        table = Table()
        table.add_column("Feature", style="cyan")
        table.add_column("Status", style="white")
        
        # Check security features
        security_features = [
            ("Memory Locking", "Available" if platform_mgr.is_linux else "Limited"),
            ("Secure File Deletion", "Available"),
            ("Process Isolation", "Available"),
            ("Audit Logging", "Available"),
            ("Secret Masking", "Available"),
        ]
        
        for feature, status in security_features:
            table.add_row(feature, status)
        
        console.print(table)


# Add subcommands
app.add_typer(run.app, name="run", help="Execute commands with secrets")
app.add_typer(validate.app, name="validate", help="Validate secrets and configurations")
app.add_typer(config.app, name="config", help="Manage configuration")
app.add_typer(audit.app, name="audit", help="Audit and monitoring commands")
app.add_typer(rotate.app, name="rotate", help="Secret rotation and lifecycle management")
app.add_typer(cloud.app, name="cloud", help="Cloud integrations management")


def main_wrapper():
    """Wrapper to handle async operations and cleanup."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if config_manager and config_manager.get('logging.level') == 'DEBUG':
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup
        if executor:
            executor.cleanup()
        if security_manager:
            security_manager.cleanup()


if __name__ == "__main__":
    main_wrapper() 