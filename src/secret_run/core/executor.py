"""Command execution engine with secure secret injection."""

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psutil
from pydantic import BaseModel, Field

from ..utils.logging import get_logger
from .security import SecurityManager

logger = get_logger(__name__)


class ExecutionConfig(BaseModel):
    """Configuration for command execution."""
    
    timeout: int = Field(default=300, ge=1, le=3600, description="Execution timeout in seconds")
    working_dir: Optional[Path] = Field(default=None, description="Working directory")
    shell: Optional[str] = Field(default=None, description="Shell to use")
    inherit_env: bool = Field(default=True, description="Inherit parent environment")
    mask_output: bool = Field(default=True, description="Mask secrets in output")
    user: Optional[str] = Field(default=None, description="User to run as (Unix only)")
    group: Optional[str] = Field(default=None, description="Group to run as (Unix only)")
    max_memory: Optional[int] = Field(default=None, ge=1, description="Memory limit in MB")
    pre_command: Optional[str] = Field(default=None, description="Command to run before main command")
    post_command: Optional[str] = Field(default=None, description="Command to run after main command")
    health_check: Optional[str] = Field(default=None, description="Health check command")
    health_timeout: int = Field(default=30, ge=1, description="Health check timeout")
    restart_on_failure: bool = Field(default=False, description="Restart on failure")
    max_restarts: int = Field(default=3, ge=0, description="Maximum restart attempts")
    signal_handling: str = Field(default="graceful", pattern="^(graceful|immediate)$")


class ExecutionResult(BaseModel):
    """Result of command execution."""
    
    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_usage: Optional[float] = None
    pid: Optional[int] = None
    error_message: Optional[str] = None


class SecretExecutor:
    """Secure command executor with secret injection."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self._active_processes: Dict[int, subprocess.Popen] = {}
        
    async def execute(
        self,
        command: Union[str, List[str]],
        secrets: Dict[str, str],
        config: ExecutionConfig,
    ) -> ExecutionResult:
        """Execute command with injected secrets."""
        
        start_time = time.time()
        process = None
        pid = None
        
        try:
            # Prepare environment with secrets
            env = self._prepare_environment(secrets, config)
            
            # Execute pre-command if specified
            if config.pre_command:
                await self._execute_pre_command(config.pre_command, env, config)
            
            # Execute main command
            process = await self._execute_command(command, env, config)
            pid = process.pid
            self._active_processes[pid] = process
            
            # Monitor execution
            stdout, stderr = await self._monitor_execution(process, config)
            
            # Execute post-command if specified
            if config.post_command:
                await self._execute_post_command(config.post_command, env, config)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Get memory usage if available
            memory_usage = self._get_memory_usage(pid) if pid else None
            
            return ExecutionResult(
                success=process.returncode == 0,
                return_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                memory_usage=memory_usage,
                pid=pid,
            )
            
        except asyncio.TimeoutError:
            if process:
                await self._terminate_process(process, config.signal_handling)
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                execution_time=time.time() - start_time,
                error_message="Command execution timed out",
            )
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                execution_time=time.time() - start_time,
                error_message=str(e),
            )
            
        finally:
            if pid and pid in self._active_processes:
                del self._active_processes[pid]
    
    def _prepare_environment(
        self, 
        secrets: Dict[str, str], 
        config: ExecutionConfig
    ) -> Dict[str, str]:
        """Prepare environment with secrets."""
        
        env = {}
        
        # Inherit parent environment if requested
        if config.inherit_env:
            env.update(os.environ)
        
        # Add secrets to environment
        for key, value in secrets.items():
            # Validate environment variable name
            if not self._is_valid_env_name(key):
                logger.warning(f"Invalid environment variable name: {key}")
                continue
            env[key] = value
        
        return env
    
    def _is_valid_env_name(self, name: str) -> bool:
        """Validate environment variable name."""
        if not name or not name[0].isalpha() and name[0] != '_':
            return False
        return all(c.isalnum() or c == '_' for c in name)
    
    async def _execute_command(
        self,
        command: Union[str, List[str]],
        env: Dict[str, str],
        config: ExecutionConfig,
    ) -> subprocess.Popen:
        """Execute the main command."""
        
        # Determine shell
        shell = config.shell or self._detect_shell()
        
        # Prepare command
        if isinstance(command, str):
            if shell:
                cmd = [shell, "-c", command]
            else:
                cmd = command.split()
        else:
            cmd = command
        
        # Set working directory
        cwd = str(config.working_dir) if config.working_dir else None
        
        # Create process
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=self._get_preexec_fn(config) if os.name != 'nt' else None,
        )
        
        return process
    
    def _detect_shell(self) -> Optional[str]:
        """Detect the default shell."""
        if os.name == 'nt':
            return 'cmd.exe'
        
        shell = os.environ.get('SHELL')
        if shell and Path(shell).exists():
            return shell
        
        # Fallback shells
        for shell in ['bash', 'zsh', 'fish', 'sh']:
            if self._shell_exists(shell):
                return shell
        
        return None
    
    def _shell_exists(self, shell: str) -> bool:
        """Check if shell exists."""
        try:
            result = subprocess.run(
                ['which', shell], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_preexec_fn(self, config: ExecutionConfig):
        """Get preexec function for process setup."""
        def preexec():
            # Set user/group if specified
            if config.user:
                import pwd
                uid = pwd.getpwnam(config.user).pw_uid
                os.setuid(uid)
            
            if config.group:
                import grp
                gid = grp.getgrnam(config.group).gr_gid
                os.setgid(gid)
        
        return preexec
    
    async def _monitor_execution(
        self,
        process: subprocess.Popen,
        config: ExecutionConfig,
    ) -> tuple[str, str]:
        """Monitor command execution with timeout."""
        
        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.to_thread(process.communicate),
                timeout=config.timeout
            )
            return stdout or "", stderr or ""
            
        except asyncio.TimeoutError:
            await self._terminate_process(process, config.signal_handling)
            raise
    
    async def _terminate_process(
        self, 
        process: subprocess.Popen, 
        signal_handling: str
    ):
        """Terminate process gracefully or forcefully."""
        
        if signal_handling == "graceful":
            try:
                process.terminate()
                await asyncio.wait_for(
                    asyncio.to_thread(process.wait),
                    timeout=10
                )
            except asyncio.TimeoutError:
                process.kill()
        else:
            process.kill()
    
    async def _execute_pre_command(
        self,
        command: str,
        env: Dict[str, str],
        config: ExecutionConfig,
    ):
        """Execute pre-command."""
        logger.info("Executing pre-command")
        result = await self.execute(command, {}, config)
        if not result.success:
            raise RuntimeError(f"Pre-command failed: {result.error_message}")
    
    async def _execute_post_command(
        self,
        command: str,
        env: Dict[str, str],
        config: ExecutionConfig,
    ):
        """Execute post-command."""
        logger.info("Executing post-command")
        result = await self.execute(command, {}, config)
        if not result.success:
            logger.warning(f"Post-command failed: {result.error_message}")
    
    def _get_memory_usage(self, pid: int) -> Optional[float]:
        """Get memory usage for process."""
        try:
            process = psutil.Process(pid)
            return process.memory_info().rss / 1024 / 1024  # MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def cleanup(self):
        """Clean up active processes."""
        for pid, process in self._active_processes.items():
            try:
                process.terminate()
                logger.info(f"Terminated process {pid}")
            except Exception as e:
                logger.error(f"Failed to terminate process {pid}: {e}")
        self._active_processes.clear() 