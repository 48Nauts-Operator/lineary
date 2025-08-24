# ABOUTME: Admin API endpoints for Betty system management and pretool validation
# ABOUTME: Provides secure command execution with guardian validation

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import subprocess
import json
import asyncio
import logging
from datetime import datetime
import os
import re
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

class ToolType(str, Enum):
    BASH = "Bash"
    WRITE = "Write"
    EDIT = "Edit"
    READ = "Read"
    LS = "LS"
    GREP = "Grep"

class CommandValidationRequest(BaseModel):
    command: str = Field(..., description="Command to validate")
    tool: ToolType = Field(..., description="Tool type for execution")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Additional parameters")

class CommandExecutionRequest(BaseModel):
    command: str = Field(..., description="Command to execute")
    tool: ToolType = Field(..., description="Tool type for execution")
    validation_token: str = Field(..., description="Validation token from pretool check")

class ValidationResult(BaseModel):
    status: str  # approved, blocked, warning
    reason: Optional[str] = None
    recommendations: Optional[List[str]] = None
    validation_token: Optional[str] = None
    expires_at: Optional[datetime] = None

class ExecutionResult(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime

# In-memory store for validation tokens (in production, use Redis)
validation_tokens = {}

def generate_validation_token(command: str, tool: str) -> str:
    """Generate a unique validation token for approved commands"""
    import hashlib
    import time
    token_data = f"{command}:{tool}:{time.time()}"
    return hashlib.sha256(token_data.encode()).hexdigest()

def check_guardian_rules(command: str, tool: str) -> ValidationResult:
    """Check command against Guardian rules"""
    
    # Define dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf\s+/',  # Destructive rm commands
        r'dd\s+if=.*of=/dev/',  # Dangerous dd operations
        r'mkfs\.',  # Filesystem formatting
        r'>\s*/dev/[^n]',  # Overwriting devices
        r'chmod\s+777',  # Overly permissive permissions
        r'curl.*\|.*sh',  # Piping curl to shell
        r'wget.*\|.*sh',  # Piping wget to shell
    ]
    
    # Define warning patterns
    warning_patterns = [
        r'sudo',  # Elevated privileges
        r'npm\s+install.*-g',  # Global npm installs
        r'pip\s+install.*--user',  # User pip installs
        r'docker\s+rm',  # Container removal
        r'git\s+push.*--force',  # Force push
    ]
    
    # Check for blocked patterns
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return ValidationResult(
                status="blocked",
                reason=f"Command matches dangerous pattern: {pattern}",
                recommendations=["Review the command for safety", "Consider using a safer alternative"]
            )
    
    # Check for warning patterns
    for pattern in warning_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            token = generate_validation_token(command, tool)
            validation_tokens[token] = {
                "command": command,
                "tool": tool,
                "expires_at": datetime.now().timestamp() + 300  # 5 minute expiry
            }
            return ValidationResult(
                status="warning",
                reason=f"Command requires caution: {pattern}",
                recommendations=["Ensure you understand the implications", "Proceed with caution"],
                validation_token=token,
                expires_at=datetime.fromtimestamp(validation_tokens[token]["expires_at"])
            )
    
    # Command is approved
    token = generate_validation_token(command, tool)
    validation_tokens[token] = {
        "command": command,
        "tool": tool,
        "expires_at": datetime.now().timestamp() + 300  # 5 minute expiry
    }
    
    return ValidationResult(
        status="approved",
        reason="Command passed all safety checks",
        validation_token=token,
        expires_at=datetime.fromtimestamp(validation_tokens[token]["expires_at"])
    )

@router.post("/validate-command", response_model=ValidationResult)
async def validate_command(request: CommandValidationRequest):
    """Validate a command against Guardian rules before execution"""
    try:
        logger.info(f"Validating command: {request.command} with tool: {request.tool}")
        
        # Perform Guardian validation
        result = check_guardian_rules(request.command, request.tool)
        
        # Log validation result
        logger.info(f"Validation result: {result.status} for command: {request.command}")
        
        return result
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )

@router.post("/execute-command", response_model=ExecutionResult)
async def execute_command(request: CommandExecutionRequest):
    """Execute a pre-validated command"""
    try:
        # Verify validation token
        if request.validation_token not in validation_tokens:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired validation token"
            )
        
        token_data = validation_tokens[request.validation_token]
        
        # Check token expiry
        if datetime.now().timestamp() > token_data["expires_at"]:
            del validation_tokens[request.validation_token]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Validation token has expired"
            )
        
        # Verify command matches token
        if token_data["command"] != request.command or token_data["tool"] != request.tool:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Command does not match validation token"
            )
        
        # Remove used token
        del validation_tokens[request.validation_token]
        
        start_time = datetime.now()
        
        # Execute based on tool type
        if request.tool == ToolType.BASH:
            # Execute bash command with timeout
            try:
                result = subprocess.run(
                    request.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 second timeout
                    cwd="/home/jarvis/projects/Betty"  # Set working directory
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return ExecutionResult(
                    success=result.returncode == 0,
                    output=result.stdout if result.stdout else result.stderr,
                    error=result.stderr if result.returncode != 0 else None,
                    execution_time=execution_time,
                    timestamp=datetime.now()
                )
                
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    success=False,
                    error="Command execution timed out after 30 seconds",
                    execution_time=30.0,
                    timestamp=datetime.now()
                )
                
        elif request.tool == ToolType.READ:
            # Simulate file read
            try:
                # Extract file path from command
                file_path = request.command.strip()
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read(5000)  # Read first 5000 chars
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    return ExecutionResult(
                        success=True,
                        output=content,
                        execution_time=execution_time,
                        timestamp=datetime.now()
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        error=f"File not found: {file_path}",
                        execution_time=0.0,
                        timestamp=datetime.now()
                    )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error=str(e),
                    execution_time=0.0,
                    timestamp=datetime.now()
                )
                
        elif request.tool == ToolType.LS:
            # List directory contents
            try:
                path = request.command.strip() or "."
                if os.path.exists(path):
                    items = os.listdir(path)
                    output = "\n".join(items[:100])  # Limit to 100 items
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    return ExecutionResult(
                        success=True,
                        output=output,
                        execution_time=execution_time,
                        timestamp=datetime.now()
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        error=f"Directory not found: {path}",
                        execution_time=0.0,
                        timestamp=datetime.now()
                    )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error=str(e),
                    execution_time=0.0,
                    timestamp=datetime.now()
                )
        
        else:
            # Other tools not implemented yet
            return ExecutionResult(
                success=False,
                error=f"Tool {request.tool} execution not implemented",
                execution_time=0.0,
                timestamp=datetime.now()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )

@router.get("/command-history")
async def get_command_history(limit: int = 50):
    """Get recent command execution history"""
    # In a real implementation, this would query from database
    return {
        "success": True,
        "history": [],  # Would be populated from database
        "total": 0
    }

@router.delete("/clear-tokens")
async def clear_expired_tokens():
    """Clear expired validation tokens"""
    current_time = datetime.now().timestamp()
    expired = []
    
    for token, data in list(validation_tokens.items()):
        if current_time > data["expires_at"]:
            expired.append(token)
            del validation_tokens[token]
    
    return {
        "success": True,
        "cleared": len(expired),
        "remaining": len(validation_tokens)
    }