# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Secret Metadata Management**: Automatic registration and validation of secret metadata
- **Demo Scripts**: Two comprehensive demo scripts for different use cases
  - `demo_showcase.sh`: Single-key demo with configurable variables
  - `multi_key_demo.sh`: Multi-key batch demo for advanced workflows
- **Robust Error Handling**: Improved error handling for metadata registration
- **Variable-Based Configuration**: Easy switching between different secret keys and policies
- **Batch Processing**: Support for processing multiple secrets with different policies
- **Automatic Metadata Creation**: Scripts automatically handle metadata registration
- **Policy Pattern Matching**: Enhanced policy creation with pattern-based matching

### Fixed
- **"No metadata found for secret" Error**: Resolved by implementing proper metadata registration
- **Secret Generation Failures**: Fixed issues with secret generation when metadata was missing
- **Policy Creation Conflicts**: Improved handling of existing policies in demo scripts
- **Script Execution Flow**: Fixed script termination issues caused by pyperclip warnings
- **Metadata Validation**: Fixed validation errors with null hash values in metadata

### Changed
- **Documentation**: Comprehensive updates to README with troubleshooting and examples
- **Demo Workflow**: Streamlined demo process with automatic metadata handling
- **Error Messages**: Improved error messages and troubleshooting guidance
- **Configuration**: Enhanced configuration examples and metadata structure documentation

### Security
- **Metadata Integrity**: Ensured proper hash generation for secret metadata
- **Validation**: Added validation for secret metadata structure and required fields

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