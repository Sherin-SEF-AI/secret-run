# 🚀 Secret Run

**Secure command execution with temporary secret injection**

Secret Run is a production-ready command-line tool that executes commands with temporary secret injection, ensuring secrets never touch the filesystem. This tool addresses the critical security need of running applications with sensitive environment variables without persistent storage risks.

## ✨ Features

- **🔒 Memory-Safe Secret Handling**: Secrets are kept in memory and explicitly cleaned up
- **🛡️ Process Isolation**: Commands run in isolated process trees
- **📁 Multiple Input Sources**: Load secrets from files, environment, stdin, and more
- **🔧 Secret Transformations**: Base64 decode, JSON parse, template substitution
- **✅ Validation**: Built-in secret validation and pattern checking
- **📊 Audit Logging**: Comprehensive audit trails for security compliance
- **🌐 Cross-Platform**: Works on Linux, macOS, and Windows
- **⚡ High Performance**: Minimal overhead with async execution
- **🎨 Beautiful UI**: Rich terminal interface with progress indicators
- **🔄 Secret Rotation**: Advanced secret lifecycle management with policies
- **☁️ Cloud Integrations**: Native support for AWS, GCP, Azure, and HashiCorp Vault
- **🤖 Auto-Rotation**: Automated secret rotation based on policies
- **📋 Policy Management**: Flexible rotation policies with pattern matching
- **🏥 Health Monitoring**: Secret expiry tracking and health checks
- **🔄 Multi-Cloud Sync**: Synchronize secrets across multiple cloud providers
- **🔑 Metadata Management**: Automatic secret metadata registration and validation

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install secret-run

# Or install with all integrations
pip install secret-run[all]

# Or install from source
git clone https://github.com/yourusername/secret-run.git
cd secret-run
pip install -e .
```

### Basic Usage

```bash
# Run a command with secrets from environment variables
secret-run run "python app.py" --env API_KEY=sk_live_123 --env DATABASE_URL=postgresql://user:pass@localhost/db

# Load secrets from a .env file
secret-run run "docker-compose up" --file .env.production

# Load secrets from JSON
secret-run run "node server.js" --file config.json --format json

# Read secrets from stdin
echo '{"API_KEY": "secret123"}' | secret-run run "python script.py" --stdin

# Validate secrets before execution
secret-run run "python app.py" --file .env --validate --require-keys API_KEY,DATABASE_URL
```

## 🔑 Secret Metadata Management

**Important**: Before generating or rotating secrets, you must register secret metadata. This ensures proper lifecycle management and policy enforcement.

### Automatic Metadata Registration

The demo scripts automatically handle metadata registration. For manual usage:

```bash
# Metadata is stored in ~/.config/secret-run/secret-metadata.json
# Each secret requires: key, policy, hash, and metadata fields
```

### Demo Scripts

Two demo scripts are provided for different use cases:

#### Single-Key Demo (`demo_showcase.sh`)
```bash
# Configure variables at the top of the script
SECRET_KEY="my-secret"
SECRET_POLICY="my-policy"
SECRET_LENGTH=32

# Run the demo
./demo_showcase.sh
```

#### Multi-Key Demo (`multi_key_demo.sh`)
```bash
# Demonstrates multiple secrets with different policies
# Configurable in the SECRETS array: "key:policy:length"
./multi_key_demo.sh
```

## 📋 Command Reference

### Core Commands

```bash
# Execute commands with secrets
secret-run run COMMAND [ARGS...] [OPTIONS]

# Validate secrets and configurations
secret-run validate [OPTIONS]

# Manage configuration
secret-run config [COMMAND] [OPTIONS]

# Audit and monitoring
secret-run audit [COMMAND] [OPTIONS]

# Secret rotation and lifecycle management
secret-run rotate [COMMAND] [OPTIONS]

# Cloud integrations management
secret-run cloud [COMMAND] [OPTIONS]

# System information and health
secret-run doctor [OPTIONS]
secret-run info [OPTIONS]
secret-run version [OPTIONS]
```

### Advanced Commands

#### Secret Rotation
```bash
# Check rotation status
secret-run rotate status --days 30

# Generate new secret (requires metadata registration)
secret-run rotate generate --key API_KEY --method random --policy api_keys

# Rotate specific secret
secret-run rotate rotate --key DATABASE_PASSWORD --method random

# Auto-rotate expired secrets
secret-run rotate auto-rotate --dry-run

# Manage rotation policies
secret-run rotate policy --action list
secret-run rotate policy --action create --name custom --pattern "^CUSTOM_.*" --interval 60
```

#### Cloud Integrations
```bash
# List cloud integrations
secret-run cloud list

# Add AWS integration
secret-run cloud add-aws --name prod --region us-east-1 --profile default

# Add GCP integration
secret-run cloud add-gcp --name prod --project my-project

# Add Azure integration
secret-run cloud add-azure --name prod --vault-url https://my-vault.vault.azure.net/

# Add HashiCorp Vault integration
secret-run cloud add-vault --name prod --address https://vault.company.com

# Get secret from cloud
secret-run cloud get --secret my-secret --format json

# Put secret to cloud
secret-run cloud put --secret my-secret --value "secret-value"

# Test cloud connectivity
secret-run cloud test --integration prod
```

### Run Command Options

```bash
secret-run run COMMAND [ARGS...]
  --env KEY=VALUE              # Direct secret specification (repeatable)
  --file PATH                  # Load from file (.env, .json, .yaml)
  --stdin                      # Read secrets from stdin
  --format FORMAT              # Input format: env|json|yaml|ini
  --mask-output               # Mask secrets in command output
  --timeout SECONDS           # Command execution timeout (default: 300)
  --working-dir PATH          # Change working directory
  --shell SHELL               # Specify shell (bash, zsh, fish, cmd, powershell)
  --dry-run                   # Show what would be executed without running
  --quiet                     # Suppress output except errors
  --verbose                   # Detailed execution logging
  --validate                  # Validate secrets before execution
  --require-keys KEYS         # Comma-separated list of required keys
  --max-memory MB             # Memory limit for child process
  --user USER                 # Run as different user (Unix only)
  --group GROUP               # Run with different group (Unix only)
  --inherit-env / --no-inherit-env  # Inherit parent environment (default: true)
  --escape-quotes             # Escape quotes in secret values
  --base64-decode KEYS        # Base64 decode specified keys
  --json-parse KEYS           # Parse JSON in specified keys
  --template-vars             # Enable template variable substitution
```

## 🔧 Configuration

### Global Configuration

Secret Run uses a YAML configuration file located at:
- **Linux/macOS**: `~/.config/secret-run/config.yaml`
- **Windows**: `%APPDATA%\secret-run\config.yaml`

```yaml
version: "1.0"
default_profile: "default"
security:
  mask_output: true
  audit_logging: true
  memory_limit: 512  # MB
  execution_timeout: 300  # seconds
  require_confirmation: false
  
logging:
  level: "INFO"
  format: "structured"  # structured|human
  file: "~/.config/secret-run/logs/secret-run.log"
  max_size: "10MB"
  max_files: 5
  
sources:
  default_format: "env"
  cache_ttl: 300
  parallel_loading: true
  validation_enabled: true
  
execution:
  default_shell: "auto"  # auto|bash|zsh|fish|cmd|powershell
  inherit_environment: true
  working_directory: "."
  signal_timeout: 10
  
ui:
  color: true
  progress_bars: true
  confirmation_prompts: true
  table_format: "grid"
```

### Secret Metadata Configuration

Secret metadata is stored in `~/.config/secret-run/secret-metadata.json`:

```json
{
  "SECRET_KEY": {
    "key": "SECRET_KEY",
    "created_at": "2025-07-12T20:44:02.123456",
    "last_rotated": "2025-07-12T20:44:02.123456",
    "expires_at": null,
    "rotation_count": 1,
    "hash": "sha256_hash_of_secret_key",
    "policy": "policy_name",
    "tags": [],
    "usage_count": 0,
    "last_used": null
  }
}
```

### Profile Configuration

Create environment-specific profiles:

```yaml
# ~/.config/secret-run/profiles/production.yaml
name: "production"
description: "Production environment secrets"
sources:
  - name: "vault"
    type: "hashicorp-vault"
    config:
      address: "https://vault.company.com"
      auth_method: "aws"
      path: "secret/production"
      
  - name: "env-file"
    type: "file"
    config:
      path: ".env.production"
      format: "env"
      watch: false
      
security:
  require_confirmation: true
  audit_all_operations: true
  allowed_commands:
    - "python"
    - "node"
    - "docker"
    - "kubectl"
    
validation:
  schema: "schemas/production.yaml"
  required_keys:
    - "DATABASE_URL"
    - "API_KEY"
    - "JWT_SECRET"
  patterns:
    API_KEY: "^sk_live_[a-zA-Z0-9]{32}$"
    DATABASE_URL: "^postgresql://"
```

## 🔒 Security Features

### Memory Safety
- **Secure Memory Allocation**: Uses `mlock()` to prevent secrets from swapping to disk
- **Explicit Memory Zeroing**: Overwrites memory containing secrets before deallocation
- **Process Isolation**: Runs commands in isolated process trees
- **Signal Handling**: Graceful cleanup on SIGTERM/SIGINT

### Input Validation
- **Secret Pattern Recognition**: Detects and validates common secret formats
- **Input Sanitization**: Prevents command injection through secret values
- **Environment Variable Validation**: Ensures valid variable names and values
- **File Path Validation**: Secure handling of file paths and permissions

### Audit & Logging
- **Structured Audit Logs**: JSON-formatted audit trails with timestamps
- **Configurable Log Levels**: Debug, info, warning, error with filtering
- **Secret Masking**: Automatic masking of sensitive values in logs
- **Tamper Detection**: Log integrity verification

## 🚀 Advanced Features

### Secret Rotation Workflow

1. **Create Policy**: Define rotation rules and patterns
2. **Register Metadata**: Add secret metadata to enable rotation
3. **Generate/Rotate**: Create or update secrets with policies
4. **Monitor**: Track expiry and rotation status

### Multi-Cloud Secret Management

- **AWS Secrets Manager**: Native integration with IAM roles
- **Google Cloud Secret Manager**: Project-based secret management
- **Azure Key Vault**: Enterprise-grade secret storage
- **HashiCorp Vault**: Self-hosted secret management

### Health Monitoring

```bash
# Check secret health
secret-run rotate status --days 7

# Monitor expiring secrets
secret-run rotate status --format json

# Auto-rotate expired secrets
secret-run rotate auto-rotate --dry-run
```

## 🛠️ Troubleshooting

### Common Issues

#### "No metadata found for secret"
**Solution**: Register secret metadata before generation:
```bash
# Use the demo scripts which handle this automatically
./demo_showcase.sh
./multi_key_demo.sh
```

#### Pyperclip clipboard warning
**Solution**: Install clipboard support or ignore the warning:
```bash
# Ubuntu/Debian
sudo apt-get install xclip

# macOS
brew install reattach-to-user-namespace

# The warning doesn't affect secret generation
```

#### Policy creation fails
**Solution**: Check if policy already exists:
```bash
secret-run rotate policy --action list
```

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
secret-run --verbose rotate generate --key my-secret --policy my-policy
```

## 📚 Examples

### Basic Secret Management
```bash
# Create a policy
secret-run rotate policy --action create --name api-keys --pattern "^.*_API_KEY$" --interval 90

# Generate a secret (with metadata registration)
./demo_showcase.sh

# Rotate the secret
secret-run rotate rotate --key demo-secret --method random --force
```

### Multi-Environment Setup
```bash
# Development
SECRET_KEY="dev-api-key" SECRET_POLICY="dev-policy" ./demo_showcase.sh

# Production
SECRET_KEY="prod-api-key" SECRET_POLICY="prod-policy" ./demo_showcase.sh

# Batch processing
./multi_key_demo.sh
```

### Cloud Integration
```bash
# Add cloud provider
secret-run cloud add-aws --name prod --region us-east-1

# Sync secrets
secret-run cloud put --secret my-secret --value "secret-value"
secret-run cloud get --secret my-secret
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/yourusername/secret-run.git
cd secret-run
pip install -e .[dev]
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](https://secret-run.readthedocs.io/)
- [Issue Tracker](https://github.com/yourusername/secret-run/issues)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)

---

**Made with ❤️ for secure DevOps** 