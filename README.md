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

# System information and health
secret-run doctor [OPTIONS]
secret-run info [OPTIONS]
secret-run version [OPTIONS]
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

## 🔌 Integrations

### Cloud Services
```bash
# AWS Secrets Manager
secret-run source add-aws production --region us-east-1 --profile default

# Google Cloud Secret Manager
secret-run source add-gcp production --project my-project

# Azure Key Vault
secret-run source add-azure production --vault my-vault --subscription my-sub

# HashiCorp Vault
secret-run source add-vault production --address https://vault.company.com
```

### Password Managers
```bash
# 1Password
secret-run source add-1password work --vault work --account my-team

# Bitwarden
secret-run source add-bitwarden personal --organization my-org

# KeePass
secret-run source add-keepass personal --database passwords.kdbx
```

## 🧪 Examples

### Web Application
```bash
# Run a Django application with database credentials
secret-run run "python manage.py runserver" \
  --file .env.production \
  --validate \
  --require-keys DATABASE_URL,SECRET_KEY,DEBUG \
  --timeout 600
```

### Docker Compose
```bash
# Run Docker Compose with secrets
secret-run run "docker-compose up -d" \
  --file docker.env \
  --working-dir /path/to/docker/project \
  --mask-output
```

### Kubernetes
```bash
# Apply Kubernetes manifests with secrets
secret-run run "kubectl apply -f k8s/" \
  --file k8s-secrets.yaml \
  --format yaml \
  --validate
```

### CI/CD Pipeline
```bash
# In GitHub Actions
- name: Deploy with secrets
  run: |
    secret-run run "npm run deploy" \
      --env NPM_TOKEN=${{ secrets.NPM_TOKEN }} \
      --env AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }} \
      --env AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/secret-run.git
cd secret-run

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=secret_run --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m security
pytest -m performance
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Security checks
bandit -r src/
safety check
```

## 📊 Performance

- **CLI Startup Time**: <200ms
- **Command Execution Overhead**: <50ms
- **Memory Usage**: Handles secrets up to 1MB
- **Environment Variables**: Supports 1000+ variables
- **Reliability**: <0.1% failure rate in normal operations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://secret-run.readthedocs.io](https://secret-run.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/secret-run/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/secret-run/discussions)
- **Security**: [Security Policy](SECURITY.md)

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI
- Beautiful output with [Rich](https://rich.readthedocs.io/)
- Data validation with [Pydantic](https://pydantic-docs.helpmanual.io/)
- Cross-platform support with [platformdirs](https://platformdirs.readthedocs.io/)

## 📈 Roadmap

- [ ] Team collaboration features
- [ ] Advanced secret rotation
- [ ] Kubernetes operator
- [ ] Web UI
- [ ] Mobile app
- [ ] Enterprise features

---

**Made with ❤️ for secure development** 