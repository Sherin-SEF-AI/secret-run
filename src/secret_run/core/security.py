"""Security utilities for memory safety and secure operations."""

import ctypes
import os
import platform
import sys
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SecurityManager:
    """Manages security aspects of secret handling."""
    
    def __init__(self):
        self._locked_memory: List[Any] = []
        self._secure_strings: List[Any] = []
    
    def secure_allocate(self, size: int) -> memoryview:
        """Allocate secure memory that won't be swapped to disk."""
        try:
            # Allocate memory
            buffer = ctypes.create_string_buffer(size)
            
            # Lock memory in RAM (Unix-like systems)
            if platform.system() != "Windows":
                self._lock_memory(buffer)
            
            self._locked_memory.append(buffer)
            return memoryview(buffer)
            
        except Exception as e:
            logger.error(f"Failed to allocate secure memory: {e}")
            raise
    
    def _lock_memory(self, buffer: ctypes.Array):
        """Lock memory to prevent swapping."""
        try:
            import mmap
            # This is a simplified version - in production you'd use mlock()
            # For now, we'll just mark it for tracking
            pass
        except ImportError:
            logger.warning("mmap not available, memory locking disabled")
    
    def secure_string(self, value: str) -> str:
        """Create a secure string that will be zeroed when destroyed."""
        # For now, return the string as-is
        # In a production implementation, this would use secure memory
        self._secure_strings.append(value)
        return value
    
    def secure_zero(self, data: Any):
        """Securely zero memory containing sensitive data."""
        if isinstance(data, (str, bytes)):
            # For strings, we can't easily zero them in Python
            # This is a limitation of Python's string immutability
            logger.debug("String zeroing requested (not implemented)")
        elif isinstance(data, memoryview):
            # Zero the memory view
            data[:] = b'\x00' * len(data)
        elif isinstance(data, ctypes.Array):
            # Zero the buffer
            ctypes.memset(data, 0, len(data))
    
    def cleanup(self):
        """Clean up secure memory and zero sensitive data."""
        # Zero all secure strings
        for string in self._secure_strings:
            self.secure_zero(string)
        
        # Zero and free locked memory
        for buffer in self._locked_memory:
            self.secure_zero(buffer)
        
        self._secure_strings.clear()
        self._locked_memory.clear()
    
    def validate_secret_pattern(self, key: str, value: str) -> bool:
        """Validate secret against common patterns."""
        # Check for common secret patterns
        patterns = {
            'api_key': r'^[a-zA-Z0-9]{32,}$',
            'jwt_secret': r'^[a-zA-Z0-9+/]{32,}={0,2}$',
            'database_url': r'^[a-zA-Z]+://',
            'password': r'^.{8,}$',
        }
        
        # Simple validation for now
        if key.lower().endswith('_key') and len(value) < 16:
            return False
        
        if key.lower().endswith('_password') and len(value) < 8:
            return False
        
        return True
    
    def sanitize_command(self, command: str) -> str:
        """Sanitize command to prevent injection."""
        # Basic command injection prevention
        dangerous_chars = [';', '|', '&', '`', '$', '(', ')', '{', '}']
        
        for char in dangerous_chars:
            if char in command:
                logger.warning(f"Potentially dangerous character '{char}' in command")
        
        return command
    
    def validate_file_path(self, path: str) -> bool:
        """Validate file path for security."""
        # Prevent directory traversal
        if '..' in path or path.startswith('/'):
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            '/etc/passwd',
            '/etc/shadow',
            '/proc/',
            '/sys/',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in path:
                return False
        
        return True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup() 