"""Platform-specific utilities."""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .logging import get_logger

logger = get_logger(__name__)


class PlatformManager:
    """Manages platform-specific functionality."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_macos = self.system == "darwin"
        self.is_linux = self.system == "linux"
        
        # Platform-specific paths
        self.home_dir = Path.home()
        self.config_dir = self._get_config_dir()
        self.cache_dir = self._get_cache_dir()
        self.data_dir = self._get_data_dir()
    
    def _get_config_dir(self) -> Path:
        """Get platform-specific config directory."""
        if self.is_windows:
            return Path(os.environ.get('APPDATA', '')) / "secret-run"
        elif self.is_macos:
            return self.home_dir / "Library" / "Application Support" / "secret-run"
        else:
            return self.home_dir / ".config" / "secret-run"
    
    def _get_cache_dir(self) -> Path:
        """Get platform-specific cache directory."""
        if self.is_windows:
            return Path(os.environ.get('LOCALAPPDATA', '')) / "secret-run" / "cache"
        elif self.is_macos:
            return self.home_dir / "Library" / "Caches" / "secret-run"
        else:
            return self.home_dir / ".cache" / "secret-run"
    
    def _get_data_dir(self) -> Path:
        """Get platform-specific data directory."""
        if self.is_windows:
            return Path(os.environ.get('LOCALAPPDATA', '')) / "secret-run" / "data"
        elif self.is_macos:
            return self.home_dir / "Library" / "Application Support" / "secret-run"
        else:
            return self.home_dir / ".local" / "share" / "secret-run"
    
    def get_default_shell(self) -> str:
        """Get the default shell for the platform."""
        if self.is_windows:
            return "cmd.exe"
        else:
            # Try to get the user's default shell
            shell = os.environ.get('SHELL', '')
            if shell and Path(shell).exists():
                return shell
            
            # Fallback shells
            for shell in ['bash', 'zsh', 'fish', 'sh']:
                if self._shell_exists(shell):
                    return shell
            
            return 'sh'
    
    def _shell_exists(self, shell: str) -> bool:
        """Check if a shell exists on the system."""
        try:
            if self.is_windows:
                result = subprocess.run(
                    ['where', shell], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
            else:
                result = subprocess.run(
                    ['which', shell], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get all environment variables."""
        return dict(os.environ)
    
    def set_environment_variable(self, key: str, value: str) -> None:
        """Set an environment variable."""
        os.environ[key] = value
    
    def unset_environment_variable(self, key: str) -> None:
        """Unset an environment variable."""
        if key in os.environ:
            del os.environ[key]
    
    def get_user_info(self) -> Dict[str, str]:
        """Get current user information."""
        info = {
            'username': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            'home': str(self.home_dir),
            'uid': str(os.getuid()) if hasattr(os, 'getuid') else 'unknown',
            'gid': str(os.getgid()) if hasattr(os, 'getgid') else 'unknown',
        }
        
        if not self.is_windows:
            try:
                import pwd
                user_info = pwd.getpwuid(os.getuid())
                info.update({
                    'username': user_info.pw_name,
                    'gecos': user_info.pw_gecos,
                    'shell': user_info.pw_shell,
                })
            except ImportError:
                pass
        
        return info
    
    def get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': sys.version,
            'python_implementation': platform.python_implementation(),
        }
    
    def create_temp_file(self, prefix: str = "secret-run", suffix: str = ".tmp") -> Path:
        """Create a temporary file."""
        import tempfile
        temp_dir = self.cache_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        fd, path = tempfile.mkstemp(
            prefix=prefix,
            suffix=suffix,
            dir=temp_dir
        )
        os.close(fd)
        return Path(path)
    
    def secure_delete_file(self, path: Path) -> bool:
        """Securely delete a file by overwriting it first."""
        try:
            if not path.exists():
                return True
            
            # Get file size
            size = path.stat().st_size
            
            # Overwrite with zeros
            with open(path, 'wb') as f:
                f.write(b'\x00' * size)
                f.flush()
                os.fsync(f.fileno())
            
            # Overwrite with ones
            with open(path, 'wb') as f:
                f.write(b'\xff' * size)
                f.flush()
                os.fsync(f.fileno())
            
            # Overwrite with random data
            import secrets
            with open(path, 'wb') as f:
                f.write(secrets.token_bytes(size))
                f.flush()
                os.fsync(f.fileno())
            
            # Delete the file
            path.unlink()
            return True
            
        except Exception as e:
            logger.error(f"Failed to securely delete {path}: {e}")
            return False
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get information about a process."""
        try:
            import psutil
            process = psutil.Process(pid)
            
            return {
                'pid': process.pid,
                'name': process.name(),
                'cmdline': process.cmdline(),
                'status': process.status(),
                'create_time': process.create_time(),
                'memory_info': process.memory_info()._asdict(),
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'username': process.username(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, ImportError):
            return None
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kill a process."""
        try:
            import psutil
            process = psutil.Process(pid)
            
            if force:
                process.kill()
            else:
                process.terminate()
            
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, ImportError):
            return False
    
    def get_available_memory(self) -> int:
        """Get available memory in bytes."""
        try:
            import psutil
            return psutil.virtual_memory().available
        except ImportError:
            # Fallback for systems without psutil
            if self.is_linux:
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if line.startswith('MemAvailable:'):
                                return int(line.split()[1]) * 1024
                except FileNotFoundError:
                    pass
            return 0
    
    def get_disk_usage(self, path: Path) -> Dict[str, Union[int, float]]:
        """Get disk usage for a path."""
        try:
            import psutil
            usage = psutil.disk_usage(str(path))
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
            }
        except ImportError:
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0,
            }
    
    def is_terminal_interactive(self) -> bool:
        """Check if the terminal is interactive."""
        return sys.stdin.isatty() and sys.stdout.isatty()
    
    def supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        if not self.is_terminal_interactive():
            return False
        
        # Check for color support
        if 'NO_COLOR' in os.environ:
            return False
        
        if 'FORCE_COLOR' in os.environ:
            return True
        
        # Platform-specific checks
        if self.is_windows:
            # Windows 10+ supports ANSI colors
            return int(platform.release()) >= 10
        else:
            # Unix-like systems typically support colors
            return True
    
    def get_terminal_size(self) -> tuple[int, int]:
        """Get terminal size (columns, rows)."""
        try:
            import shutil
            return shutil.get_terminal_size()
        except (ImportError, OSError):
            # Fallback values
            return (80, 24)
    
    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        directories = [
            self.config_dir,
            self.cache_dir,
            self.data_dir,
            self.cache_dir / "temp",
            self.config_dir / "profiles",
            self.config_dir / "templates",
            self.config_dir / "logs",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up old temporary files."""
        import time
        temp_dir = self.cache_dir / "temp"
        if not temp_dir.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for temp_file in temp_dir.glob("*"):
            if temp_file.is_file():
                file_age = current_time - temp_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        temp_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {temp_file}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} temporary files")
        return deleted_count 