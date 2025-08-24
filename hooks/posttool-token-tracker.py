#!/usr/bin/env python3
"""
ABOUTME: Betty PostTool Token Tracker - Captures actual LLM token usage and costs
ABOUTME: Tracks real API token consumption for accurate cost calculation
"""

import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

# Betty API endpoints
BETTY_API = "http://localhost:3034"
AGENT_TRACKING_API = f"{BETTY_API}/api/agent-tracking/track"
SPRINT_COST_API = f"{BETTY_API}/api/sprints/track-cost"

class TokenTracker:
    def __init__(self):
        self.log_file = Path.home() / ".betty" / "token-usage.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def process_hook_input(self):
        """Process PostTool hook input from Claude Code"""
        try:
            # Read hook input from stdin
            hook_input = json.loads(sys.stdin.read())
            
            tool_name = hook_input.get("tool", "unknown")
            tool_result = hook_input.get("result", {})
            metadata = hook_input.get("metadata", {})
            
            # Extract token usage if available
            usage = metadata.get("usage", {})
            if not usage:
                # Try to find usage in result
                if isinstance(tool_result, dict):
                    usage = tool_result.get("usage", {})
            
            if usage:
                self.track_tokens(tool_name, usage, metadata)
            
            # Always continue execution
            return {"action": "continue"}
            
        except Exception as e:
            print(f"Token tracker error: {e}", file=sys.stderr)
            return {"action": "continue"}
    
    def track_tokens(self, tool_name, usage, metadata):
        """Track token usage and send to Betty API"""
        try:
            # Extract token counts
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            
            # Determine agent type from context
            agent_type = self.identify_agent(tool_name, metadata)
            
            # Get current task context
            task_id = metadata.get("task_id", "unknown")
            task_description = metadata.get("task_description", tool_name)
            sprint_id = metadata.get("sprint_id")
            
            # Log to file
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "agent_type": agent_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "task_id": task_id,
                "sprint_id": sprint_id
            }
            
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Send to Betty API
            if input_tokens > 0 or output_tokens > 0:
                self.send_to_betty(
                    agent_type=agent_type,
                    task_id=task_id,
                    task_description=task_description,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    sprint_id=sprint_id
                )
                
        except Exception as e:
            print(f"Failed to track tokens: {e}", file=sys.stderr)
    
    def identify_agent(self, tool_name, metadata):
        """Identify which agent type based on tool and context"""
        # Check explicit agent type
        if "agent_type" in metadata:
            return metadata["agent_type"]
        
        # Map tools to likely agents
        tool_agent_map = {
            "Task": "general-purpose",
            "Write": "code-reviewer",
            "Edit": "code-reviewer",
            "MultiEdit": "code-reviewer",
            "Bash": "devops-automator",
            "Read": "general-purpose",
            "Grep": "debug-specialist",
            "WebSearch": "trend-researcher",
            "WebFetch": "trend-researcher"
        }
        
        # Check for specialized agents from task context
        context = metadata.get("context", "").lower()
        if "security" in context:
            return "security-auditor"
        elif "frontend" in context or "react" in context:
            return "frontend-developer"
        elif "backend" in context or "api" in context:
            return "backend-architect"
        elif "test" in context:
            return "test-automation-architect"
        elif "debug" in context or "error" in context:
            return "debug-specialist"
        elif "sql" in context or "database" in context:
            return "sql-pro"
        elif "prompt" in context:
            return "prompt-optimizer"
        
        return tool_agent_map.get(tool_name, "general-purpose")
    
    def send_to_betty(self, agent_type, task_id, task_description, 
                     input_tokens, output_tokens, sprint_id=None):
        """Send token usage to Betty API"""
        try:
            # Calculate duration (mock for now, could track actual)
            duration_minutes = 1.0  # Will be replaced with actual timing
            
            params = {
                "agent_type": agent_type,
                "task_id": task_id,
                "task_description": task_description[:200],  # Limit length
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_minutes": duration_minutes,
                "success": True
            }
            
            if sprint_id:
                params["sprint_id"] = sprint_id
            
            # Send to agent tracking
            response = requests.post(AGENT_TRACKING_API, params=params, timeout=2)
            
            # Also track sprint costs if in a sprint
            if sprint_id:
                model = self.get_model_for_agent(agent_type)
                cost_params = {
                    "task_id": task_id,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "context": agent_type
                }
                requests.post(SPRINT_COST_API, params=cost_params, timeout=2)
                
        except Exception as e:
            print(f"Failed to send to Betty API: {e}", file=sys.stderr)
    
    def get_model_for_agent(self, agent_type):
        """Get the typical model used by an agent type"""
        agent_models = {
            "llm-systems-architect": "claude-3-opus",
            "security-auditor": "claude-3-sonnet",
            "frontend-developer": "claude-3-sonnet",
            "backend-architect": "claude-3-sonnet",
            "debug-specialist": "claude-3-haiku",
            "code-reviewer": "claude-3-haiku",
            "general-purpose": "claude-3-haiku"
        }
        return agent_models.get(agent_type, "claude-3-haiku")

def main():
    """Hook entry point"""
    tracker = TokenTracker()
    result = tracker.process_hook_input()
    print(json.dumps(result))

if __name__ == "__main__":
    main()