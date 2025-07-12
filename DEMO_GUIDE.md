# 🎬 Secret Run Demo Guide

This guide explains how to use the demo scripts and understand the secret metadata workflow in Secret Run.

## 📋 Overview

Secret Run includes two demo scripts that showcase different use cases:

1. **`demo_showcase.sh`** - Single-key demo with configurable variables
2. **`multi_key_demo.sh`** - Multi-key batch demo for advanced workflows

Both scripts automatically handle secret metadata registration, preventing the common "No metadata found for secret" error.

## 🔑 Secret Metadata Management

### Why Metadata is Required

Before generating or rotating secrets, Secret Run requires metadata to be registered for each secret key. This ensures:

- **Proper lifecycle management** - Track creation, rotation, and expiry dates
- **Policy enforcement** - Associate secrets with rotation policies
- **Audit trails** - Maintain usage statistics and history
- **Security validation** - Ensure proper hash generation and validation

### Metadata Structure

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

## 🎯 Demo Scripts

### Single-Key Demo (`demo_showcase.sh`)

**Purpose**: Demonstrate a single secret with configurable parameters.

**Configuration**:
```bash
# === CONFIGURABLE VARIABLES ===
SECRET_KEY="demo-secret"
SECRET_POLICY="demo-policy"
SECRET_LENGTH=32
```

**Usage**:
```bash
# Use default configuration
./demo_showcase.sh

# Or customize for different secrets
SECRET_KEY="my-api-key" SECRET_POLICY="api-policy" SECRET_LENGTH=40 ./demo_showcase.sh
```

**Features**:
- ✅ Automatic metadata registration
- ✅ Policy creation and management
- ✅ Secret generation with specified length
- ✅ Rotation status checking
- ✅ Cloud integration demonstration
- ✅ Error handling and validation

### Multi-Key Demo (`multi_key_demo.sh`)

**Purpose**: Demonstrate multiple secrets with different policies and lengths.

**Configuration**:
```bash
# === MULTI-KEY DEMO CONFIG ===
SECRETS=(
  "demo-secret:demo-policy:32"
  "prod-api-key:api_keys:40"
  "db-password:passwords:24"
  "service-token:tokens:48"
)
```

**Usage**:
```bash
# Run with default configuration
./multi_key_demo.sh

# Customize the SECRETS array for different combinations
```

**Features**:
- ✅ Batch processing of multiple secrets
- ✅ Different policies for different secret types
- ✅ Variable secret lengths
- ✅ Automatic metadata creation for each secret
- ✅ Robust error handling
- ✅ Progress tracking

## 🚀 Getting Started

### Prerequisites

1. **Install Secret Run**:
   ```bash
   pip install secret-run
   ```

2. **Activate Virtual Environment** (if using source):
   ```bash
   source venv/bin/activate
   ```

3. **Make Scripts Executable**:
   ```bash
   chmod +x demo_showcase.sh multi_key_demo.sh
   ```

### Running the Demos

#### Option 1: Single-Key Demo
```bash
# Basic demo
./demo_showcase.sh

# Custom demo
SECRET_KEY="production-api" SECRET_POLICY="prod-policy" SECRET_LENGTH=64 ./demo_showcase.sh
```

#### Option 2: Multi-Key Demo
```bash
# Run all configured secrets
./multi_key_demo.sh
```

## 🔧 Customization

### Adding New Secrets

#### For Single-Key Demo:
1. Edit the variables at the top of `demo_showcase.sh`
2. Run the script

#### For Multi-Key Demo:
1. Add entries to the `SECRETS` array in `multi_key_demo.sh`
2. Format: `"key:policy:length"`
3. Run the script

### Example Customizations

#### Development Environment
```bash
SECRET_KEY="dev-database" SECRET_POLICY="dev-policy" SECRET_LENGTH=24 ./demo_showcase.sh
```

#### Production Environment
```bash
SECRET_KEY="prod-jwt-secret" SECRET_POLICY="prod-policy" SECRET_LENGTH=64 ./demo_showcase.sh
```

#### Batch Processing
```bash
# Edit multi_key_demo.sh SECRETS array:
SECRETS=(
  "dev-api-key:dev-policy:32"
  "staging-db:staging-policy:24"
  "prod-jwt:prod-policy:64"
  "test-token:test-policy:16"
)
```

## 🛠️ Troubleshooting

### Common Issues

#### "No metadata found for secret"
**Cause**: Secret metadata not registered before generation.

**Solution**: Use the demo scripts which handle this automatically, or manually add metadata:

```bash
python3 -c "
import json, datetime, hashlib
from pathlib import Path
f = Path.home() / '.config' / 'secret-run' / 'secret-metadata.json'
m = json.load(open(f))
k = 'your-secret-key'
now = datetime.datetime.now().isoformat()
h = hashlib.sha256(k.encode()).hexdigest()
m[k] = {
    'key': k,
    'created_at': now,
    'last_rotated': None,
    'expires_at': None,
    'rotation_count': 0,
    'hash': h,
    'policy': 'your-policy',
    'tags': [],
    'usage_count': 0,
    'last_used': None
}
json.dump(m, open(f, 'w'), indent=2)
"
```

#### Pyperclip Warning
**Cause**: Clipboard support not available on the system.

**Solution**: Install clipboard support or ignore the warning:
```bash
# Ubuntu/Debian
sudo apt-get install xclip

# macOS
brew install reattach-to-user-namespace

# The warning doesn't affect secret generation
```

#### Policy Creation Fails
**Cause**: Policy already exists or invalid parameters.

**Solution**: Check existing policies:
```bash
secret-run rotate policy --action list
```

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
secret-run --verbose rotate generate --key my-secret --policy my-policy
```

## 📊 Demo Output Examples

### Single-Key Demo Output
```
==============================
 Secret Run CLI Demo Showcase 
==============================

---- 1. Show Help ----
secret-run --help
[Help output]

---- 2. Show Rotate Command Help ----
secret-run rotate --help
[Rotate help output]

---- 3. Show Cloud Command Help ----
secret-run cloud --help
[Cloud help output]

---- 4. Create a Rotation Policy ----
Created policy 'demo-policy'

---- 5. Ensure Metadata for demo-secret Exists ----
Metadata for demo-secret already exists.

---- 6. Generate a New Secret ----
╭──────────────────────────────────────── Success ────────────────────────────────────────╮
│ Generated Secret                                                                        │
│ Key: demo-secret                                                                        │
│ Method: random                                                                          │
│ Length: 16                                                                              │
│ Policy: demo-policy                                                                     │
│ Tags: None                                                                              │
╰─────────────────────────────────────────────────────────────────────────────────────────╯

Secret Value: ****************
```

### Multi-Key Demo Output
```
==============================
Demo for key: demo-secret, policy: demo-policy, length: 32
==============================
---- 1. Create/Ensure Rotation Policy ----
Created policy 'demo-policy'
---- 2. Ensure Metadata for demo-secret Exists ----
Metadata for demo-secret already exists.
---- 3. Generate Secret ----
[Success output]

==============================
Demo for key: prod-api-key, policy: api_keys, length: 40
==============================
[Process repeats for each secret]
```

## 🔄 Advanced Workflows

### CI/CD Integration

Use the demo scripts in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Generate Secrets
  run: |
    chmod +x demo_showcase.sh
    SECRET_KEY="${{ secrets.SECRET_NAME }}" \
    SECRET_POLICY="${{ secrets.POLICY_NAME }}" \
    SECRET_LENGTH=32 \
    ./demo_showcase.sh
```

### Automated Testing

Create test scripts that use the demo infrastructure:

```bash
#!/bin/bash
# test_secrets.sh
for secret in "test-api:test-policy:32" "test-db:test-policy:24"; do
  IFS=":" read -r key policy length <<< "$secret"
  SECRET_KEY="$key" SECRET_POLICY="$policy" SECRET_LENGTH="$length" ./demo_showcase.sh
done
```

### Environment Management

Manage different environments with different configurations:

```bash
# Development
SECRET_KEY="dev-secret" SECRET_POLICY="dev-policy" ./demo_showcase.sh

# Staging
SECRET_KEY="staging-secret" SECRET_POLICY="staging-policy" ./demo_showcase.sh

# Production
SECRET_KEY="prod-secret" SECRET_POLICY="prod-policy" ./demo_showcase.sh
```

## 📚 Additional Resources

- [README.md](README.md) - Main documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [examples/basic_usage.py](examples/basic_usage.py) - Programmatic usage example

## 🤝 Support

If you encounter issues with the demo scripts:

1. Check the troubleshooting section above
2. Review the error messages carefully
3. Ensure all prerequisites are met
4. Try running with verbose logging: `secret-run --verbose`
5. Check the metadata file: `cat ~/.config/secret-run/secret-metadata.json`

---

**Happy secret management! 🔐** 