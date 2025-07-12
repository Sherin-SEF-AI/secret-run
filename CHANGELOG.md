# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and core functionality
- Command execution engine with secret injection
- Multiple secret source loaders (env, json, yaml, stdin)
- Secret validation and transformation capabilities
- Security manager with memory safety features
- Configuration management system
- Cross-platform utilities
- CLI interface with Typer and Rich
- Comprehensive logging system
- Audit and monitoring capabilities

### Security
- Memory-safe secret handling with explicit cleanup
- Process isolation for command execution
- Input validation and sanitization
- Secret masking in logs and output
- Secure file deletion utilities

## [0.1.0] - 2024-01-01

### Added
- Initial release of secret-run CLI tool
- Core command execution with secret injection
- Support for multiple input formats (env, json, yaml)
- Basic secret validation and transformation
- Configuration management
- Cross-platform support (Linux, macOS, Windows)
- Rich terminal interface
- Comprehensive documentation

### Security
- Memory-safe secret handling
- Process isolation
- Input validation
- Secret masking

## [0.0.1] - 2024-01-01

### Added
- Project initialization
- Basic project structure
- Development environment setup
- Documentation framework 