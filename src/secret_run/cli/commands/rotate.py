"""Rotate command for secret rotation and lifecycle management."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.rotation import SecretRotator
from ...utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(name="rotate", help="Secret rotation and lifecycle management")


@app.command()
def status(
    ctx: typer.Context,
    days: int = typer.Option(30, "--days", "-d", help="Days to look ahead for expiring secrets"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, csv"),
    export: Optional[Path] = typer.Option(None, "--export", help="Export report to file"),
):
    """Show secret rotation status and expiring secrets."""
    
    rotator = SecretRotator()
    report = rotator.get_rotation_report()
    
    if format == "json":
        import json
        output = json.dumps(report, indent=2, default=str)
        if export:
            export.write_text(output)
        else:
            console.print(output)
        return
    
    # Display summary
    console.print(Panel(
        f"[bold cyan]Secret Rotation Status[/bold cyan]\n"
        f"Total Secrets: {report['total_secrets']}\n"
        f"Expired: {report['expired_secrets']}\n"
        f"Expiring Soon (7 days): {report['expiring_soon']}\n"
        f"Expiring This Month: {report['expiring_month']}",
        title="Summary"
    ))
    
    # Show expired secrets
    if report['expired_details']:
        console.print("\n[bold red]Expired Secrets[/bold red]")
        table = Table()
        table.add_column("Key", style="cyan")
        table.add_column("Policy", style="yellow")
        table.add_column("Last Rotated", style="green")
        table.add_column("Rotation Count", style="blue")
        
        for secret in report['expired_details']:
            table.add_row(
                secret['key'],
                secret['policy'] or "None",
                str(secret['last_rotated']) if secret['last_rotated'] else "Never",
                str(secret['rotation_count'])
            )
        console.print(table)
    
    # Show expiring soon secrets
    if report['expiring_soon_details']:
        console.print("\n[bold yellow]Expiring Soon (Next 7 Days)[/bold yellow]")
        table = Table()
        table.add_column("Key", style="cyan")
        table.add_column("Policy", style="yellow")
        table.add_column("Expires", style="red")
        table.add_column("Days Left", style="blue")
        
        for secret in report['expiring_soon_details']:
            if secret['expires_at']:
                from datetime import datetime
                expires = datetime.fromisoformat(secret['expires_at'])
                days_left = (expires - datetime.now()).days
                table.add_row(
                    secret['key'],
                    secret['policy'] or "None",
                    expires.strftime("%Y-%m-%d"),
                    str(days_left)
                )
        console.print(table)


@app.command()
def generate(
    ctx: typer.Context,
    key: str = typer.Option(..., "--key", "-k", help="Secret key to generate"),
    method: str = typer.Option("random", "--method", "-m", help="Generation method: random, incremental, hash"),
    length: Optional[int] = typer.Option(None, "--length", "-l", help="Secret length"),
    policy: Optional[str] = typer.Option(None, "--policy", "-p", help="Rotation policy to apply"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Tags for the secret"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for generated secret"),
):
    """Generate a new secret value."""
    
    rotator = SecretRotator()
    
    try:
        # Generate the secret
        secret_value = rotator.generate_rotated_secret(key, method)
        
        # Add to metadata
        rotator.add_secret(key, secret_value, policy, tags)
        
        # Display result
        console.print(Panel(
            f"[bold green]Generated Secret[/bold green]\n"
            f"Key: {key}\n"
            f"Method: {method}\n"
            f"Length: {len(secret_value)}\n"
            f"Policy: {policy or 'None'}\n"
            f"Tags: {', '.join(tags) if tags else 'None'}",
            title="Success"
        ))
        
        # Show the secret (masked in production)
        console.print(f"\n[bold]Secret Value:[/bold] {'*' * len(secret_value)}")
        
        # Save to file if requested
        if output:
            output.write_text(secret_value)
            console.print(f"\n[green]Secret saved to: {output}[/green]")
        
        # Copy to clipboard if available
        try:
            import pyperclip
            pyperclip.copy(secret_value)
            console.print("[green]Secret copied to clipboard[/green]")
        except ImportError:
            console.print("[yellow]Install pyperclip to enable clipboard copy[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error generating secret: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def rotate(
    ctx: typer.Context,
    key: str = typer.Option(..., "--key", "-k", help="Secret key to rotate"),
    method: str = typer.Option("random", "--method", "-m", help="Rotation method: random, incremental, hash"),
    new_value: Optional[str] = typer.Option(None, "--value", "-v", help="New secret value (if not generating)"),
    force: bool = typer.Option(False, "--force", help="Force rotation even if not expired"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be rotated without doing it"),
):
    """Rotate a specific secret."""
    
    rotator = SecretRotator()
    
    if key not in rotator.metadata:
        console.print(f"[red]Error: No metadata found for secret '{key}'[/red]")
        raise typer.Exit(1)
    
    meta = rotator.metadata[key]
    
    if not force and meta.expires_at:
        from datetime import datetime
        expires = datetime.fromisoformat(meta.expires_at)
        if expires > datetime.now():
            console.print(f"[yellow]Warning: Secret '{key}' is not expired yet (expires: {expires.strftime('%Y-%m-%d')})[/yellow]")
            if not typer.confirm("Continue anyway?"):
                raise typer.Exit(0)
    
    if dry_run:
        console.print(f"[bold cyan]Dry Run - Would rotate secret '{key}'[/bold cyan]")
        console.print(f"Current rotation count: {meta.rotation_count}")
        console.print(f"Method: {method}")
        if new_value:
            console.print(f"New value: {'*' * len(new_value)}")
        else:
            console.print("New value: [would be generated]")
        return
    
    try:
        if new_value:
            success = rotator.rotate_secret(key, new_value)
        else:
            generated_value = rotator.generate_rotated_secret(key, method)
            success = rotator.rotate_secret(key, generated_value)
        
        if success:
            console.print(f"[green]Successfully rotated secret '{key}'[/green]")
            updated_meta = rotator.metadata[key]
            console.print(f"New rotation count: {updated_meta.rotation_count}")
            if updated_meta.expires_at:
                console.print(f"New expiry: {updated_meta.expires_at}")
        else:
            console.print(f"[red]Failed to rotate secret '{key}'[/red]")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Error rotating secret: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def auto_rotate(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be rotated without doing it"),
    max_secrets: Optional[int] = typer.Option(None, "--max", help="Maximum number of secrets to rotate"),
):
    """Automatically rotate expired secrets that have auto-rotate enabled."""
    
    rotator = SecretRotator()
    
    if dry_run:
        expired = rotator.get_expired_secrets()
        auto_rotate_candidates = [
            meta for meta in expired
            if meta.policy and meta.policy in rotator.policies
            and rotator.policies[meta.policy].auto_rotate
        ]
        
        if not auto_rotate_candidates:
            console.print("[yellow]No expired secrets with auto-rotate enabled[/yellow]")
            return
        
        console.print(f"[bold cyan]Dry Run - Would auto-rotate {len(auto_rotate_candidates)} secrets[/bold cyan]")
        
        table = Table()
        table.add_column("Key", style="cyan")
        table.add_column("Policy", style="yellow")
        table.add_column("Expired", style="red")
        
        for meta in auto_rotate_candidates[:max_secrets] if max_secrets else auto_rotate_candidates:
            table.add_row(
                meta.key,
                meta.policy,
                meta.expires_at.strftime("%Y-%m-%d") if meta.expires_at else "Unknown"
            )
        console.print(table)
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Auto-rotating expired secrets...", total=None)
        
        try:
            rotated = asyncio.run(rotator.auto_rotate_expired())
            
            if max_secrets:
                rotated = rotated[:max_secrets]
            
            progress.update(task, description=f"Auto-rotated {len(rotated)} secrets")
            
            if rotated:
                console.print(f"\n[green]Successfully auto-rotated {len(rotated)} secrets:[/green]")
                for key in rotated:
                    console.print(f"  • {key}")
            else:
                console.print("\n[yellow]No secrets were auto-rotated[/yellow]")
        
        except Exception as e:
            console.print(f"\n[red]Error during auto-rotation: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def policy(
    ctx: typer.Context,
    action: str = typer.Option(..., "--action", help="Action: list, create, update, delete"),
    name: Optional[str] = typer.Option(None, "--name", help="Policy name"),
    pattern: Optional[str] = typer.Option(None, "--pattern", help="Secret pattern regex"),
    interval: Optional[int] = typer.Option(None, "--interval", help="Rotation interval in days"),
    auto_rotate: Optional[bool] = typer.Option(None, "--auto-rotate", help="Enable auto-rotation"),
    method: Optional[str] = typer.Option(None, "--method", help="Rotation method"),
    min_length: Optional[int] = typer.Option(None, "--min-length", help="Minimum secret length"),
):
    """Manage rotation policies."""
    
    rotator = SecretRotator()
    
    if action == "list":
        console.print("[bold cyan]Rotation Policies[/bold cyan]")
        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Pattern", style="yellow")
        table.add_column("Interval", style="green")
        table.add_column("Auto-Rotate", style="blue")
        table.add_column("Method", style="magenta")
        
        for name, policy in rotator.policies.items():
            table.add_row(
                name,
                policy.secret_pattern,
                f"{policy.rotation_interval} days",
                "Yes" if policy.auto_rotate else "No",
                policy.rotation_method
            )
        console.print(table)
    
    elif action == "create":
        if not all([name, pattern, interval]):
            console.print("[red]Error: name, pattern, and interval are required for creating policies[/red]")
            raise typer.Exit(1)
        
        from ...core.rotation import RotationPolicy
        
        policy = RotationPolicy(
            name=name,
            secret_pattern=pattern,
            rotation_interval=interval,
            auto_rotate=auto_rotate or False,
            rotation_method=method or "random",
            min_length=min_length or 16
        )
        
        rotator.policies[name] = policy
        console.print(f"[green]Created policy '{name}'[/green]")
    
    elif action == "update":
        if not name or name not in rotator.policies:
            console.print(f"[red]Error: Policy '{name}' not found[/red]")
            raise typer.Exit(1)
        
        policy = rotator.policies[name]
        
        if pattern:
            policy.secret_pattern = pattern
        if interval:
            policy.rotation_interval = interval
        if auto_rotate is not None:
            policy.auto_rotate = auto_rotate
        if method:
            policy.rotation_method = method
        if min_length:
            policy.min_length = min_length
        
        console.print(f"[green]Updated policy '{name}'[/green]")
    
    elif action == "delete":
        if not name or name not in rotator.policies:
            console.print(f"[red]Error: Policy '{name}' not found[/red]")
            raise typer.Exit(1)
        
        del rotator.policies[name]
        console.print(f"[green]Deleted policy '{name}'[/green]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1) 