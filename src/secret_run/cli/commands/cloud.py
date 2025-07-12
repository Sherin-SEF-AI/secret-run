"""Cloud integration commands for managing cloud secret providers."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.cloud_integrations import (
    CloudIntegrationManager,
    AWSIntegration,
    GCPIntegration,
    AzureIntegration,
    VaultIntegration
)
from ...utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(name="cloud", help="Cloud integrations management")


@app.command()
def list(
    ctx: typer.Context,
    format: str = typer.Option("table", "--format", help="Output format: table, json"),
):
    """List configured cloud integrations."""
    
    manager = CloudIntegrationManager()
    integrations = manager.list_integrations()
    
    if format == "json":
        import json
        status = manager.get_health_status()
        console.print(json.dumps(status, indent=2))
        return
    
    if not integrations:
        console.print("[yellow]No cloud integrations configured[/yellow]")
        return
    
    console.print("[bold cyan]Cloud Integrations[/bold cyan]")
    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Provider", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Region", style="blue")
    
    status = manager.get_health_status()
    for name in integrations:
        info = status.get(name, {})
        table.add_row(
            name,
            info.get("provider", "Unknown"),
            "Enabled" if info.get("enabled", False) else "Disabled",
            info.get("region", "N/A")
        )
    
    console.print(table)


@app.command()
def add_aws(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Integration name"),
    region: str = typer.Option(..., "--region", help="AWS region"),
    profile: Optional[str] = typer.Option(None, "--profile", help="AWS profile"),
    role_arn: Optional[str] = typer.Option(None, "--role-arn", help="IAM role ARN for cross-account access"),
    kms_key_id: Optional[str] = typer.Option(None, "--kms-key", help="KMS key ID for encryption"),
    secret_prefix: str = typer.Option("/secret-run/", "--prefix", help="Secret name prefix"),
    credentials_path: Optional[Path] = typer.Option(None, "--credentials", help="Path to credentials file"),
):
    """Add AWS Secrets Manager integration."""
    
    try:
        integration = AWSIntegration(
            name=name,
            region=region,
            profile=profile,
            role_arn=role_arn,
            kms_key_id=kms_key_id,
            secret_prefix=secret_prefix,
            credentials_path=str(credentials_path) if credentials_path else None
        )
        
        manager = CloudIntegrationManager()
        manager.add_integration(integration)
        
        console.print(f"[green]Successfully added AWS integration '{name}'[/green]")
        console.print(f"Region: {region}")
        if profile:
            console.print(f"Profile: {profile}")
        if role_arn:
            console.print(f"Role ARN: {role_arn}")
        
    except Exception as e:
        console.print(f"[red]Failed to add AWS integration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_gcp(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Integration name"),
    project_id: str = typer.Option(..., "--project", help="GCP project ID"),
    service_account_key: Optional[Path] = typer.Option(None, "--key-file", help="Service account key file"),
):
    """Add Google Cloud Secret Manager integration."""
    
    try:
        integration = GCPIntegration(
            name=name,
            project_id=project_id,
            service_account_key=str(service_account_key) if service_account_key else None
        )
        
        manager = CloudIntegrationManager()
        manager.add_integration(integration)
        
        console.print(f"[green]Successfully added GCP integration '{name}'[/green]")
        console.print(f"Project ID: {project_id}")
        if service_account_key:
            console.print(f"Service Account Key: {service_account_key}")
        
    except Exception as e:
        console.print(f"[red]Failed to add GCP integration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_azure(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Integration name"),
    vault_url: str = typer.Option(..., "--vault-url", help="Azure Key Vault URL"),
    tenant_id: Optional[str] = typer.Option(None, "--tenant-id", help="Azure tenant ID"),
    client_id: Optional[str] = typer.Option(None, "--client-id", help="Azure client ID"),
    client_secret: Optional[str] = typer.Option(None, "--client-secret", help="Azure client secret"),
):
    """Add Azure Key Vault integration."""
    
    try:
        integration = AzureIntegration(
            name=name,
            vault_url=vault_url,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        manager = CloudIntegrationManager()
        manager.add_integration(integration)
        
        console.print(f"[green]Successfully added Azure integration '{name}'[/green]")
        console.print(f"Vault URL: {vault_url}")
        if tenant_id:
            console.print(f"Tenant ID: {tenant_id}")
        
    except Exception as e:
        console.print(f"[red]Failed to add Azure integration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_vault(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Integration name"),
    address: str = typer.Option(..., "--address", help="Vault server address"),
    token: Optional[str] = typer.Option(None, "--token", help="Vault token"),
    mount_point: str = typer.Option("secret", "--mount-point", help="Secret mount point"),
    auth_method: str = typer.Option("token", "--auth-method", help="Authentication method"),
    role_id: Optional[str] = typer.Option(None, "--role-id", help="AppRole role ID"),
    secret_id: Optional[str] = typer.Option(None, "--secret-id", help="AppRole secret ID"),
):
    """Add HashiCorp Vault integration."""
    
    try:
        integration = VaultIntegration(
            name=name,
            address=address,
            token=token,
            mount_point=mount_point,
            auth_method=auth_method,
            role_id=role_id,
            secret_id=secret_id
        )
        
        manager = CloudIntegrationManager()
        manager.add_integration(integration)
        
        console.print(f"[green]Successfully added Vault integration '{name}'[/green]")
        console.print(f"Address: {address}")
        console.print(f"Mount Point: {mount_point}")
        console.print(f"Auth Method: {auth_method}")
        
    except Exception as e:
        console.print(f"[red]Failed to add Vault integration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def get(
    ctx: typer.Context,
    secret_name: str = typer.Option(..., "--secret", help="Secret name to retrieve"),
    integration: Optional[str] = typer.Option(None, "--integration", help="Specific integration to use"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, env"),
    output: Optional[Path] = typer.Option(None, "--output", help="Output file"),
):
    """Get secret from cloud integration(s)."""
    
    manager = CloudIntegrationManager()
    
    if integration:
        # Get from specific integration
        integration_obj = manager.get_integration(integration)
        if not integration_obj:
            console.print(f"[red]Integration '{integration}' not found[/red]")
            raise typer.Exit(1)
        
        if not integration_obj.enabled:
            console.print(f"[red]Integration '{integration}' is disabled[/red]")
            raise typer.Exit(1)
        
        try:
            if isinstance(integration_obj, AWSIntegration):
                secrets = asyncio.run(integration_obj.get_secret(secret_name))
            elif isinstance(integration_obj, GCPIntegration):
                secrets = asyncio.run(integration_obj.get_secret(secret_name))
            elif isinstance(integration_obj, AzureIntegration):
                secrets = asyncio.run(integration_obj.get_secret(secret_name))
            elif isinstance(integration_obj, VaultIntegration):
                secrets = asyncio.run(integration_obj.get_secret(secret_name))
            else:
                console.print(f"[red]Unsupported integration type: {type(integration_obj)}[/red]")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Failed to get secret from {integration}: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Get from all integrations
        secrets = asyncio.run(manager.get_secret_from_all(secret_name))
    
    if not secrets:
        console.print(f"[yellow]No secrets found with name '{secret_name}'[/yellow]")
        return
    
    if format == "json":
        import json
        output_data = json.dumps(secrets, indent=2)
    elif format == "env":
        output_data = "\n".join([f"{k}={v}" for k, v in secrets.items()])
    else:
        # Table format
        console.print(f"[bold cyan]Secrets for '{secret_name}'[/bold cyan]")
        table = Table()
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in secrets.items():
            masked_value = "*" * len(value) if len(value) > 8 else "*" * 8
            table.add_row(key, masked_value)
        
        console.print(table)
        return
    
    if output:
        output.write_text(output_data)
        console.print(f"[green]Secrets saved to {output}[/green]")
    else:
        console.print(output_data)


@app.command()
def put(
    ctx: typer.Context,
    secret_name: str = typer.Option(..., "--secret", help="Secret name"),
    secret_value: str = typer.Option(..., "--value", help="Secret value"),
    integration: Optional[str] = typer.Option(None, "--integration", help="Specific integration to use"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be stored without doing it"),
):
    """Put secret to cloud integration(s)."""
    
    manager = CloudIntegrationManager()
    
    if dry_run:
        console.print(f"[bold cyan]Dry Run - Would store secret '{secret_name}'[/bold cyan]")
        if integration:
            console.print(f"Integration: {integration}")
        else:
            console.print("Integrations: All enabled")
        console.print(f"Value: {'*' * len(secret_value)}")
        return
    
    if integration:
        # Put to specific integration
        integration_obj = manager.get_integration(integration)
        if not integration_obj:
            console.print(f"[red]Integration '{integration}' not found[/red]")
            raise typer.Exit(1)
        
        if not integration_obj.enabled:
            console.print(f"[red]Integration '{integration}' is disabled[/red]")
            raise typer.Exit(1)
        
        try:
            if isinstance(integration_obj, AWSIntegration):
                success = asyncio.run(integration_obj.put_secret(secret_name, secret_value))
            elif isinstance(integration_obj, GCPIntegration):
                success = asyncio.run(integration_obj.put_secret(secret_name, secret_value))
            elif isinstance(integration_obj, AzureIntegration):
                success = asyncio.run(integration_obj.put_secret(secret_name, secret_value))
            elif isinstance(integration_obj, VaultIntegration):
                success = asyncio.run(integration_obj.put_secret(secret_name, secret_value))
            else:
                console.print(f"[red]Unsupported integration type: {type(integration_obj)}[/red]")
                raise typer.Exit(1)
            
            if success:
                console.print(f"[green]Successfully stored secret '{secret_name}' in {integration}[/green]")
            else:
                console.print(f"[red]Failed to store secret '{secret_name}' in {integration}[/red]")
                raise typer.Exit(1)
        
        except Exception as e:
            console.print(f"[red]Failed to store secret in {integration}: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Put to all integrations
        results = asyncio.run(manager.put_secret_to_all(secret_name, secret_value))
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        console.print(f"[green]Stored secret '{secret_name}' in {success_count}/{total_count} integrations[/green]")
        
        for name, success in results.items():
            status = "✅" if success else "❌"
            console.print(f"  {status} {name}")


@app.command()
def test(
    ctx: typer.Context,
    integration: Optional[str] = typer.Option(None, "--integration", help="Test specific integration"),
):
    """Test cloud integration connectivity."""
    
    manager = CloudIntegrationManager()
    
    if integration:
        # Test specific integration
        integration_obj = manager.get_integration(integration)
        if not integration_obj:
            console.print(f"[red]Integration '{integration}' not found[/red]")
            raise typer.Exit(1)
        
        console.print(f"[bold cyan]Testing integration '{integration}'[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testing connectivity...", total=None)
            
            try:
                # Test connectivity by trying to list secrets or get a test secret
                if isinstance(integration_obj, AWSIntegration):
                    secrets = asyncio.run(integration_obj.list_secrets())
                    progress.update(task, description=f"Found {len(secrets)} secrets")
                elif isinstance(integration_obj, (GCPIntegration, AzureIntegration, VaultIntegration)):
                    # Try to get a test secret
                    test_result = asyncio.run(integration_obj.get_secret("test-connection"))
                    progress.update(task, description="Connection successful")
                else:
                    progress.update(task, description="Unknown integration type")
                
                console.print(f"\n[green]✅ Integration '{integration}' is working correctly[/green]")
            
            except Exception as e:
                console.print(f"\n[red]❌ Integration '{integration}' failed: {e}[/red]")
                raise typer.Exit(1)
    else:
        # Test all integrations
        integrations = manager.list_integrations()
        
        if not integrations:
            console.print("[yellow]No integrations configured[/yellow]")
            return
        
        console.print("[bold cyan]Testing all integrations[/bold cyan]")
        
        results = {}
        for name in integrations:
            integration_obj = manager.get_integration(name)
            if not integration_obj or not integration_obj.enabled:
                results[name] = False
                continue
            
            try:
                if isinstance(integration_obj, AWSIntegration):
                    asyncio.run(integration_obj.list_secrets())
                elif isinstance(integration_obj, (GCPIntegration, AzureIntegration, VaultIntegration)):
                    asyncio.run(integration_obj.get_secret("test-connection"))
                else:
                    results[name] = False
                    continue
                
                results[name] = True
            except Exception:
                results[name] = False
        
        # Display results
        table = Table()
        table.add_column("Integration", style="cyan")
        table.add_column("Status", style="green")
        
        for name, success in results.items():
            status = "✅ Working" if success else "❌ Failed"
            table.add_row(name, status)
        
        console.print(table)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        console.print(f"\n[green]Test completed: {success_count}/{total_count} integrations working[/green]")


@app.command()
def remove(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Integration name to remove"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Remove a cloud integration."""
    
    manager = CloudIntegrationManager()
    
    if name not in manager.integrations:
        console.print(f"[red]Integration '{name}' not found[/red]")
        raise typer.Exit(1)
    
    if not confirm:
        if not typer.confirm(f"Are you sure you want to remove integration '{name}'?"):
            raise typer.Exit(0)
    
    del manager.integrations[name]
    console.print(f"[green]Removed integration '{name}'[/green]") 