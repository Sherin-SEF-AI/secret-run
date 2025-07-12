"""Run command for executing commands with secrets."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...core.executor import ExecutionConfig
from ...utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(name="run", help="Execute commands with secrets")


@app.command()
def main(
    ctx: typer.Context,
    command: List[str] = typer.Argument(..., help="Command to execute"),
    env: List[str] = typer.Option([], "--env", "-e", help="Environment variable (KEY=VALUE)"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Load secrets from file"),
    stdin: bool = typer.Option(False, "--stdin", help="Read secrets from stdin"),
    format: str = typer.Option("env", "--format", help="Input format (env|json|yaml|ini)"),
    mask_output: bool = typer.Option(True, "--mask-output", help="Mask secrets in output"),
    timeout: int = typer.Option(300, "--timeout", help="Command execution timeout (seconds)"),
    working_dir: Optional[Path] = typer.Option(None, "--working-dir", "-w", help="Working directory"),
    shell: Optional[str] = typer.Option(None, "--shell", help="Shell to use"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output except errors"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed execution logging"),
    audit_log: Optional[Path] = typer.Option(None, "--audit-log", help="Write audit log to file"),
    exclude_env: Optional[str] = typer.Option(None, "--exclude-env", help="Exclude env vars matching pattern"),
    include_env: Optional[str] = typer.Option(None, "--include-env", help="Include only env vars matching pattern"),
    prefix: Optional[str] = typer.Option(None, "--prefix", help="Add prefix to all secret keys"),
    suffix: Optional[str] = typer.Option(None, "--suffix", help="Add suffix to all secret keys"),
    validate: bool = typer.Option(False, "--validate", help="Validate secrets before execution"),
    require_keys: Optional[str] = typer.Option(None, "--require-keys", help="Comma-separated list of required keys"),
    max_memory: Optional[int] = typer.Option(None, "--max-memory", help="Memory limit for child process (MB)"),
    user: Optional[str] = typer.Option(None, "--user", help="Run as different user (Unix only)"),
    group: Optional[str] = typer.Option(None, "--group", help="Run with different group (Unix only)"),
    inherit_env: bool = typer.Option(True, "--inherit-env", help="Inherit parent environment"),
    escape_quotes: bool = typer.Option(False, "--escape-quotes", help="Escape quotes in secret values"),
    base64_decode: Optional[str] = typer.Option(None, "--base64-decode", help="Base64 decode specified keys"),
    json_parse: Optional[str] = typer.Option(None, "--json-parse", help="Parse JSON in specified keys"),
    template_vars: bool = typer.Option(False, "--template-vars", help="Enable template variable substitution"),
):
    """Execute a command with secrets injected as environment variables."""
    
    # Get managers from context
    managers = ctx.obj
    config_manager = managers['config_manager']
    platform_manager = managers['platform_manager']
    security_manager = managers['security_manager']
    secret_manager = managers['secret_manager']
    loader_manager = managers['loader_manager']
    validator = managers['validator']
    executor = managers['executor']
    
    try:
        # Load secrets from various sources
        secrets = {}
        
        # Load from environment variables
        for env_var in env:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                secrets[key] = value
        
        # Load from file
        if file:
            if not file.exists():
                console.print(f"[red]Error: File not found: {file}[/red]")
                raise typer.Exit(1)
            
            file_secrets = loader_manager.load_secrets(str(file))
            secrets.update(file_secrets)
        
        # Load from stdin
        if stdin:
            stdin_secrets = loader_manager.load_secrets("stdin")
            secrets.update(stdin_secrets)
        
        # Apply transformations
        if prefix:
            secret_manager.add_secrets(secrets)
            secret_manager.apply_prefix(prefix)
            secrets = secret_manager.get_secrets()
        
        if suffix:
            secret_manager.add_secrets(secrets)
            secret_manager.apply_suffix(suffix)
            secrets = secret_manager.get_secrets()
        
        if escape_quotes:
            secrets = {k: v.replace('"', '\\"').replace("'", "\\'") for k, v in secrets.items()}
        
        # Apply base64 decoding
        if base64_decode:
            keys_to_decode = [k.strip() for k in base64_decode.split(',')]
            for key in keys_to_decode:
                if key in secrets:
                    try:
                        import base64
                        decoded = base64.b64decode(secrets[key]).decode('utf-8')
                        secrets[key] = decoded
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to base64 decode {key}: {e}[/yellow]")
        
        # Apply JSON parsing
        if json_parse:
            keys_to_parse = [k.strip() for k in json_parse.split(',')]
            for key in keys_to_parse:
                if key in secrets:
                    try:
                        import json
                        parsed = json.loads(secrets[key])
                        if isinstance(parsed, dict):
                            secrets[key] = json.dumps(parsed)
                        else:
                            secrets[key] = str(parsed)
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to parse JSON for {key}: {e}[/yellow]")
        
        # Template variable substitution
        if template_vars:
            import re
            for key, value in secrets.items():
                # Replace ${VAR} with actual secret values
                def substitute(match):
                    var_name = match.group(1)
                    return secrets.get(var_name, match.group(0))
                
                secrets[key] = re.sub(r'\$\{([^}]+)\}', substitute, value)
        
        # Validate secrets if requested
        if validate:
            required_keys_list = []
            if require_keys:
                required_keys_list = [k.strip() for k in require_keys.split(',')]
            
            validation_issues = validator.validate_secrets(secrets, required_keys=required_keys_list)
            
            if validation_issues['errors']:
                console.print("[red]Validation errors:[/red]")
                for error in validation_issues['errors']:
                    console.print(f"  • {error}")
                raise typer.Exit(1)
            
            if validation_issues['warnings']:
                console.print("[yellow]Validation warnings:[/yellow]")
                for warning in validation_issues['warnings']:
                    console.print(f"  • {warning}")
        
        # Create execution configuration
        exec_config = ExecutionConfig(
            timeout=timeout,
            working_dir=working_dir,
            shell=shell,
            inherit_env=inherit_env,
            mask_output=mask_output,
            user=user,
            group=group,
            max_memory=max_memory,
        )
        
        # Show what would be executed in dry-run mode
        if dry_run:
            console.print("[bold cyan]Dry run - would execute:[/bold cyan]")
            console.print(f"Command: {' '.join(command)}")
            console.print(f"Working directory: {working_dir or '.'}")
            console.print(f"Shell: {shell or 'auto'}")
            console.print(f"Timeout: {timeout}s")
            console.print(f"Secrets: {len(secrets)} variables")
            
            if secrets:
                table = Table(title="Secrets")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="white")
                
                for key, value in secrets.items():
                    masked_value = "***" if mask_output else value
                    table.add_row(key, masked_value)
                
                console.print(table)
            
            return
        
        # Execute the command
        if not quiet:
            console.print(f"[bold green]Executing command:[/bold green] {' '.join(command)}")
            if secrets:
                console.print(f"[bold green]With {len(secrets)} secrets[/bold green]")
        
        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Executing command...", total=None)
            
            # Execute command
            result = asyncio.run(executor.execute(command, secrets, exec_config))
            
            progress.update(task, completed=True)
        
        # Display results
        if not quiet:
            if result.success:
                console.print(f"[bold green]✅ Command completed successfully[/bold green]")
                console.print(f"Return code: {result.return_code}")
                console.print(f"Execution time: {result.execution_time:.2f}s")
                
                if result.memory_usage:
                    console.print(f"Memory usage: {result.memory_usage:.1f}MB")
            else:
                console.print(f"[bold red]❌ Command failed[/bold red]")
                console.print(f"Return code: {result.return_code}")
                if result.error_message:
                    console.print(f"Error: {result.error_message}")
            
            # Show output
            if result.stdout:
                console.print("\n[bold cyan]Standard Output:[/bold cyan]")
                if mask_output and secrets:
                    # Mask secrets in output
                    masked_output = result.stdout
                    for key, value in secrets.items():
                        masked_output = masked_output.replace(value, f"***{key}***")
                    console.print(masked_output)
                else:
                    console.print(result.stdout)
            
            if result.stderr:
                console.print("\n[bold red]Standard Error:[/bold red]")
                if mask_output and secrets:
                    # Mask secrets in error output
                    masked_error = result.stderr
                    for key, value in secrets.items():
                        masked_error = masked_error.replace(value, f"***{key}***")
                    console.print(masked_error)
                else:
                    console.print(result.stderr)
        
        # Exit with command's return code
        if not result.success:
            raise typer.Exit(result.return_code)
    
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) 