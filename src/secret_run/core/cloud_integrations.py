"""Advanced cloud integrations for secret management."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ..utils.logging import get_logger

logger = get_logger(__name__)


class CloudConfig(BaseModel):
    """Base configuration for cloud integrations."""
    
    name: str = Field(..., description="Integration name")
    provider: str = Field(..., description="Cloud provider")
    enabled: bool = Field(default=True, description="Whether integration is enabled")
    credentials_path: Optional[str] = Field(default=None, description="Path to credentials file")
    region: Optional[str] = Field(default=None, description="Cloud region")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


class AWSIntegration(CloudConfig):
    """AWS Secrets Manager integration."""
    
    provider: str = "aws"
    profile: Optional[str] = Field(default=None, description="AWS profile to use")
    role_arn: Optional[str] = Field(default=None, description="IAM role ARN for cross-account access")
    kms_key_id: Optional[str] = Field(default=None, description="KMS key ID for encryption")
    secret_prefix: str = Field(default="/secret-run/", description="Prefix for secret names")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._client = None
        self._session = None
    
    async def get_client(self):
        """Get AWS Secrets Manager client."""
        try:
            import boto3
            from botocore.config import Config
            
            if self._client is None:
                config = Config(
                    region_name=self.region,
                    retries={'max_attempts': self.retry_attempts},
                    connect_timeout=self.timeout,
                    read_timeout=self.timeout
                )
                
                session_kwargs = {}
                if self.profile:
                    session_kwargs['profile_name'] = self.profile
                if self.credentials_path:
                    session_kwargs['profile_name'] = 'custom'
                    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = self.credentials_path
                
                self._session = boto3.Session(**session_kwargs)
                
                if self.role_arn:
                    # Assume role for cross-account access
                    sts_client = self._session.client('sts', config=config)
                    assumed_role = sts_client.assume_role(
                        RoleArn=self.role_arn,
                        RoleSessionName='secret-run-session'
                    )
                    credentials = assumed_role['Credentials']
                    
                    self._client = boto3.client(
                        'secretsmanager',
                        aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken'],
                        config=config
                    )
                else:
                    self._client = self._session.client('secretsmanager', config=config)
            
            return self._client
        except ImportError:
            raise ImportError("boto3 is required for AWS integration. Install with: pip install boto3")
    
    async def get_secret(self, secret_name: str) -> Dict[str, str]:
        """Get secret from AWS Secrets Manager."""
        client = await self.get_client()
        full_name = f"{self.secret_prefix}{secret_name}"
        
        try:
            response = client.get_secret_value(SecretId=full_name)
            secret_string = response['SecretString']
            
            # Try to parse as JSON first, fallback to single value
            try:
                return json.loads(secret_string)
            except json.JSONDecodeError:
                return {secret_name: secret_string}
        
        except client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret '{full_name}' not found in AWS Secrets Manager")
            return {}
        except Exception as e:
            logger.error(f"Failed to get secret '{full_name}' from AWS: {e}")
            return {}
    
    async def put_secret(self, secret_name: str, secret_value: Union[str, Dict[str, str]]) -> bool:
        """Put secret to AWS Secrets Manager."""
        client = await self.get_client()
        full_name = f"{self.secret_prefix}{secret_name}"
        
        try:
            if isinstance(secret_value, dict):
                secret_string = json.dumps(secret_value)
            else:
                secret_string = str(secret_value)
            
            kwargs = {
                'SecretId': full_name,
                'SecretString': secret_string
            }
            
            if self.kms_key_id:
                kwargs['KmsKeyId'] = self.kms_key_id
            
            client.put_secret_value(**kwargs)
            logger.info(f"Successfully stored secret '{full_name}' in AWS Secrets Manager")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store secret '{full_name}' in AWS: {e}")
            return False
    
    async def list_secrets(self, prefix: Optional[str] = None) -> List[str]:
        """List secrets in AWS Secrets Manager."""
        client = await self.get_client()
        search_prefix = prefix or self.secret_prefix
        
        try:
            response = client.list_secrets()
            secrets = []
            
            for secret in response.get('SecretList', []):
                name = secret['Name']
                if name.startswith(search_prefix):
                    # Remove prefix from returned names
                    clean_name = name[len(search_prefix):]
                    secrets.append(clean_name)
            
            return secrets
        
        except Exception as e:
            logger.error(f"Failed to list secrets from AWS: {e}")
            return []


class GCPIntegration(CloudConfig):
    """Google Cloud Secret Manager integration."""
    
    provider: str = "gcp"
    project_id: str = Field(..., description="GCP project ID")
    service_account_key: Optional[str] = Field(default=None, description="Path to service account key file")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._client = None
    
    async def get_client(self):
        """Get GCP Secret Manager client."""
        try:
            from google.cloud import secretmanager
            from google.oauth2 import service_account
            
            if self._client is None:
                if self.service_account_key:
                    credentials = service_account.Credentials.from_service_account_file(
                        self.service_account_key
                    )
                    self._client = secretmanager.SecretManagerServiceClient(credentials=credentials)
                else:
                    # Use default credentials
                    self._client = secretmanager.SecretManagerServiceClient()
            
            return self._client
        except ImportError:
            raise ImportError("google-cloud-secret-manager is required for GCP integration")
    
    async def get_secret(self, secret_name: str) -> Dict[str, str]:
        """Get secret from GCP Secret Manager."""
        client = await self.get_client()
        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        
        try:
            response = client.access_secret_version(request={"name": name})
            secret_data = response.payload.data.decode("UTF-8")
            
            # Try to parse as JSON first, fallback to single value
            try:
                return json.loads(secret_data)
            except json.JSONDecodeError:
                return {secret_name: secret_data}
        
        except Exception as e:
            logger.error(f"Failed to get secret '{secret_name}' from GCP: {e}")
            return {}
    
    async def put_secret(self, secret_name: str, secret_value: Union[str, Dict[str, str]]) -> bool:
        """Put secret to GCP Secret Manager."""
        client = await self.get_client()
        parent = f"projects/{self.project_id}"
        
        try:
            if isinstance(secret_value, dict):
                secret_data = json.dumps(secret_value).encode("UTF-8")
            else:
                secret_data = str(secret_value).encode("UTF-8")
            
            # Create secret if it doesn't exist
            try:
                client.get_secret(request={"name": f"{parent}/secrets/{secret_name}"})
            except Exception:
                client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_name,
                        "secret": {"replication": {"automatic": {}}}
                    }
                )
            
            # Add new version
            client.add_secret_version(
                request={
                    "parent": f"{parent}/secrets/{secret_name}",
                    "payload": {"data": secret_data}
                }
            )
            
            logger.info(f"Successfully stored secret '{secret_name}' in GCP Secret Manager")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store secret '{secret_name}' in GCP: {e}")
            return False


class AzureIntegration(CloudConfig):
    """Azure Key Vault integration."""
    
    provider: str = "azure"
    vault_url: str = Field(..., description="Azure Key Vault URL")
    tenant_id: Optional[str] = Field(default=None, description="Azure tenant ID")
    client_id: Optional[str] = Field(default=None, description="Azure client ID")
    client_secret: Optional[str] = Field(default=None, description="Azure client secret")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._client = None
    
    async def get_client(self):
        """Get Azure Key Vault client."""
        try:
            from azure.identity import DefaultAzureCredential, ClientSecretCredential
            from azure.keyvault.secrets import SecretClient
            
            if self._client is None:
                if all([self.tenant_id, self.client_id, self.client_secret]):
                    credential = ClientSecretCredential(
                        tenant_id=self.tenant_id,
                        client_id=self.client_id,
                        client_secret=self.client_secret
                    )
                else:
                    credential = DefaultAzureCredential()
                
                self._client = SecretClient(
                    vault_url=self.vault_url,
                    credential=credential
                )
            
            return self._client
        except ImportError:
            raise ImportError("azure-keyvault-secrets is required for Azure integration")
    
    async def get_secret(self, secret_name: str) -> Dict[str, str]:
        """Get secret from Azure Key Vault."""
        client = await self.get_client()
        
        try:
            secret = client.get_secret(secret_name)
            secret_value = secret.value
            
            # Try to parse as JSON first, fallback to single value
            try:
                return json.loads(secret_value)
            except json.JSONDecodeError:
                return {secret_name: secret_value}
        
        except Exception as e:
            logger.error(f"Failed to get secret '{secret_name}' from Azure: {e}")
            return {}
    
    async def put_secret(self, secret_name: str, secret_value: Union[str, Dict[str, str]]) -> bool:
        """Put secret to Azure Key Vault."""
        client = await self.get_client()
        
        try:
            if isinstance(secret_value, dict):
                secret_data = json.dumps(secret_value)
            else:
                secret_data = str(secret_value)
            
            client.set_secret(secret_name, secret_data)
            logger.info(f"Successfully stored secret '{secret_name}' in Azure Key Vault")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store secret '{secret_name}' in Azure: {e}")
            return False


class VaultIntegration(CloudConfig):
    """HashiCorp Vault integration."""
    
    provider: str = "vault"
    address: str = Field(..., description="Vault server address")
    token: Optional[str] = Field(default=None, description="Vault token")
    mount_point: str = Field(default="secret", description="Secret mount point")
    auth_method: str = Field(default="token", description="Authentication method")
    role_id: Optional[str] = Field(default=None, description="AppRole role ID")
    secret_id: Optional[str] = Field(default=None, description="AppRole secret ID")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._client = None
    
    async def get_client(self):
        """Get HashiCorp Vault client."""
        try:
            import hvac
            
            if self._client is None:
                self._client = hvac.Client(url=self.address)
                
                if self.auth_method == "token" and self.token:
                    self._client.token = self.token
                elif self.auth_method == "approle" and self.role_id and self.secret_id:
                    self._client.auth.approle.login(
                        role_id=self.role_id,
                        secret_id=self.secret_id
                    )
                else:
                    # Try to use environment variables or other auth methods
                    pass
                
                if not self._client.is_authenticated():
                    raise Exception("Failed to authenticate with Vault")
            
            return self._client
        except ImportError:
            raise ImportError("hvac is required for HashiCorp Vault integration")
    
    async def get_secret(self, secret_name: str) -> Dict[str, str]:
        """Get secret from HashiCorp Vault."""
        client = await self.get_client()
        
        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                mount_point=self.mount_point
            )
            
            secret_data = response['data']['data']
            return secret_data
        
        except Exception as e:
            logger.error(f"Failed to get secret '{secret_name}' from Vault: {e}")
            return {}
    
    async def put_secret(self, secret_name: str, secret_value: Union[str, Dict[str, str]]) -> bool:
        """Put secret to HashiCorp Vault."""
        client = await self.get_client()
        
        try:
            if isinstance(secret_value, str):
                secret_data = {"value": secret_value}
            else:
                secret_data = secret_value
            
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_name,
                secret=secret_data,
                mount_point=self.mount_point
            )
            
            logger.info(f"Successfully stored secret '{secret_name}' in Vault")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store secret '{secret_name}' in Vault: {e}")
            return False


class CloudIntegrationManager:
    """Manages multiple cloud integrations."""
    
    def __init__(self):
        self.integrations: Dict[str, CloudConfig] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
    
    def add_integration(self, integration: CloudConfig) -> None:
        """Add a cloud integration."""
        self.integrations[integration.name] = integration
        logger.info(f"Added {integration.provider} integration: {integration.name}")
    
    def get_integration(self, name: str) -> Optional[CloudConfig]:
        """Get integration by name."""
        return self.integrations.get(name)
    
    def list_integrations(self) -> List[str]:
        """List all integration names."""
        return list(self.integrations.keys())
    
    async def get_secret_from_all(self, secret_name: str) -> Dict[str, str]:
        """Get secret from all enabled integrations."""
        all_secrets = {}
        
        for name, integration in self.integrations.items():
            if not integration.enabled:
                continue
            
            try:
                if isinstance(integration, AWSIntegration):
                    secrets = await integration.get_secret(secret_name)
                elif isinstance(integration, GCPIntegration):
                    secrets = await integration.get_secret(secret_name)
                elif isinstance(integration, AzureIntegration):
                    secrets = await integration.get_secret(secret_name)
                elif isinstance(integration, VaultIntegration):
                    secrets = await integration.get_secret(secret_name)
                else:
                    continue
                
                all_secrets.update(secrets)
                
            except Exception as e:
                logger.error(f"Failed to get secret from {name}: {e}")
        
        return all_secrets
    
    async def put_secret_to_all(self, secret_name: str, secret_value: Union[str, Dict[str, str]]) -> Dict[str, bool]:
        """Put secret to all enabled integrations."""
        results = {}
        
        for name, integration in self.integrations.items():
            if not integration.enabled:
                continue
            
            try:
                if isinstance(integration, AWSIntegration):
                    success = await integration.put_secret(secret_name, secret_value)
                elif isinstance(integration, GCPIntegration):
                    success = await integration.put_secret(secret_name, secret_value)
                elif isinstance(integration, AzureIntegration):
                    success = await integration.put_secret(secret_name, secret_value)
                elif isinstance(integration, VaultIntegration):
                    success = await integration.put_secret(secret_name, secret_value)
                else:
                    success = False
                
                results[name] = success
                
            except Exception as e:
                logger.error(f"Failed to put secret to {name}: {e}")
                results[name] = False
        
        return results
    
    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all integrations."""
        status = {}
        
        for name, integration in self.integrations.items():
            status[name] = {
                "provider": integration.provider,
                "enabled": integration.enabled,
                "region": getattr(integration, 'region', None),
                "timeout": integration.timeout,
                "retry_attempts": integration.retry_attempts
            }
        
        return status 