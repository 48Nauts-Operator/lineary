# ABOUTME: Betty Agent Usage Tracking - Monitor sub-agent costs and performance
# ABOUTME: Tracks individual AI agents usage patterns and LLM costs

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import uuid
from pathlib import Path
from enum import Enum

router = APIRouter(prefix="/api/agent-tracking", tags=["agent-tracking"])

# Agent storage
TRACKING_DIR = Path.home() / ".betty" / "agent-tracking"
AGENTS_FILE = TRACKING_DIR / "agents.json"
SESSIONS_FILE = TRACKING_DIR / "sessions.json"

TRACKING_DIR.mkdir(parents=True, exist_ok=True)

# Sub-agent types and their typical models
SUB_AGENTS = {
    "llm-systems-architect": {"model": "claude-3-opus", "specialty": "AI/LLM systems, RAG, vector databases", "color": "#8B5CF6"},
    "security-auditor": {"model": "claude-3-sonnet", "specialty": "Security reviews, vulnerability assessment", "color": "#EF4444"},
    "frontend-developer": {"model": "claude-3-sonnet", "specialty": "React, UI/UX, responsive design", "color": "#3B82F6"},
    "backend-architect": {"model": "claude-3-sonnet", "specialty": "APIs, databases, scalability", "color": "#10B981"},
    "test-automation-architect": {"model": "claude-3-sonnet", "specialty": "Testing strategies, CI/CD", "color": "#F59E0B"},
    "debug-specialist": {"model": "claude-3-haiku", "specialty": "Error diagnosis, troubleshooting", "color": "#EC4899"},
    "code-reviewer": {"model": "claude-3-haiku", "specialty": "Code quality, best practices", "color": "#6366F1"},
    "data-engineer": {"model": "claude-3-sonnet", "specialty": "ETL, data pipelines, analytics", "color": "#14B8A6"},
    "devops-automator": {"model": "claude-3-sonnet", "specialty": "Docker, Kubernetes, deployment", "color": "#84CC16"},
    "rapid-prototyper": {"model": "claude-3-sonnet", "specialty": "MVPs, proof-of-concepts", "color": "#A855F7"},
    "trend-researcher": {"model": "claude-3-haiku", "specialty": "Market analysis, trending topics", "color": "#F97316"},
    "sprint-prioritizer": {"model": "claude-3-haiku", "specialty": "Task planning, sprint management", "color": "#0EA5E9"},
    "prompt-optimizer": {"model": "claude-3-sonnet", "specialty": "Prompt engineering, LLM optimization", "color": "#D946EF"},
    "sql-pro": {"model": "claude-3-sonnet", "specialty": "Complex queries, database optimization", "color": "#059669"},
    "general-purpose": {"model": "claude-3-haiku", "specialty": "General tasks, research", "color": "#737373"}
}

# LLM pricing (per 1K tokens)
LLM_PRICING = {
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
}

class AgentUsage(BaseModel):
    agent_type: str
    agent_name: str
    total_sessions: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    total_time_minutes: float = 0.0
    success_rate: float = 100.0
    last_used: Optional[datetime] = None
    tasks_completed: int = 0
    average_cost_per_task: float = 0.0
    
class AgentSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str
    task_id: str
    task_description: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    model_used: str = ""
    success: bool = True
    sprint_id: Optional[str] = None

def load_agent_usage() -> Dict[str, AgentUsage]:
    """Load agent usage data"""
    if AGENTS_FILE.exists():
        try:
            with open(AGENTS_FILE, 'r') as f:
                data = json.load(f)
                agents = {}
                for agent_type, usage_data in data.items():
                    if 'last_used' in usage_data and usage_data['last_used']:
                        usage_data['last_used'] = datetime.fromisoformat(usage_data['last_used'])
                    agents[agent_type] = AgentUsage(**usage_data)
                return agents
        except Exception as e:
            print(f"Error loading agent usage: {e}")
    
    # Initialize with all known agent types
    agents = {}
    for agent_type, config in SUB_AGENTS.items():
        agents[agent_type] = AgentUsage(
            agent_type=agent_type,
            agent_name=agent_type.replace("-", " ").title()
        )
    return agents

def save_agent_usage(agents: Dict[str, AgentUsage]):
    """Save agent usage data"""
    try:
        data = {}
        for agent_type, usage in agents.items():
            usage_dict = usage.dict()
            if usage_dict.get('last_used'):
                usage_dict['last_used'] = usage_dict['last_used'].isoformat()
            data[agent_type] = usage_dict
        
        with open(AGENTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving agent usage: {e}")

def load_sessions() -> List[AgentSession]:
    """Load agent sessions"""
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, 'r') as f:
                data = json.load(f)
                sessions = []
                for session_data in data:
                    for field in ['start_time', 'end_time']:
                        if session_data.get(field):
                            session_data[field] = datetime.fromisoformat(session_data[field])
                    sessions.append(AgentSession(**session_data))
                return sessions
        except Exception as e:
            print(f"Error loading sessions: {e}")
    return []

def save_sessions(sessions: List[AgentSession]):
    """Save sessions"""
    try:
        data = []
        for session in sessions[-500:]:  # Keep last 500 sessions
            session_dict = session.dict()
            for field in ['start_time', 'end_time']:
                if session_dict.get(field):
                    session_dict[field] = session_dict[field].isoformat()
            data.append(session_dict)
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving sessions: {e}")

@router.post("/track")
async def track_agent_usage(
    agent_type: str = Query(..., description="Type of agent used"),
    task_id: str = Query(..., description="Task ID"),
    task_description: str = Query(..., description="What the agent did"),
    input_tokens: int = Query(..., description="Input tokens used"),
    output_tokens: int = Query(..., description="Output tokens generated"),
    duration_minutes: float = Query(..., description="How long it took"),
    success: bool = Query(True, description="Whether task succeeded"),
    sprint_id: Optional[str] = Query(None, description="Sprint ID if applicable")
):
    """Track usage of a sub-agent"""
    
    # Load current usage
    agents = load_agent_usage()
    sessions = load_sessions()
    
    # Get agent config
    agent_config = SUB_AGENTS.get(agent_type, SUB_AGENTS["general-purpose"])
    model = agent_config["model"]
    
    # Calculate cost
    pricing = LLM_PRICING.get(model, LLM_PRICING["claude-3-haiku"])
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    total_cost = input_cost + output_cost
    
    # Create session record
    session = AgentSession(
        agent_type=agent_type,
        task_id=task_id,
        task_description=task_description,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_cost=total_cost,
        model_used=model,
        success=success,
        sprint_id=sprint_id,
        end_time=datetime.now()
    )
    sessions.append(session)
    
    # Update agent usage
    if agent_type not in agents:
        agents[agent_type] = AgentUsage(
            agent_type=agent_type,
            agent_name=agent_type.replace("-", " ").title()
        )
    
    usage = agents[agent_type]
    usage.total_sessions += 1
    usage.total_cost += total_cost
    usage.total_tokens += input_tokens + output_tokens
    usage.total_time_minutes += duration_minutes
    usage.last_used = datetime.now()
    
    if success:
        usage.tasks_completed += 1
    
    # Recalculate metrics
    if usage.total_sessions > 0:
        successful = len([s for s in sessions if s.agent_type == agent_type and s.success])
        usage.success_rate = (successful / usage.total_sessions) * 100
        
    if usage.tasks_completed > 0:
        usage.average_cost_per_task = usage.total_cost / usage.tasks_completed
    
    # Save data
    save_agent_usage(agents)
    save_sessions(sessions)
    
    # Also track in sprints if applicable
    if sprint_id:
        from .sprints import load_sprints, save_sprints
        sprints = load_sprints()
        if sprint_id in sprints:
            sprint = sprints[sprint_id]
            sprint.actual_cost += total_cost
            sprint.tokens_used += input_tokens + output_tokens
            if model not in sprint.cost_breakdown:
                sprint.cost_breakdown[model] = 0
            sprint.cost_breakdown[model] += total_cost
            save_sprints(sprints)
    
    return {
        "success": True,
        "session_id": session.session_id,
        "agent": agent_type,
        "cost": total_cost,
        "tokens": input_tokens + output_tokens
    }

@router.get("/usage")
async def get_agent_usage(
    days: int = Query(7, description="Days to look back"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type")
):
    """Get agent usage statistics"""
    agents = load_agent_usage()
    sessions = load_sessions()
    
    cutoff = datetime.now() - timedelta(days=days)
    recent_sessions = [s for s in sessions if s.start_time >= cutoff]
    
    if agent_type:
        recent_sessions = [s for s in recent_sessions if s.agent_type == agent_type]
        filtered_agents = {agent_type: agents.get(agent_type)} if agent_type in agents else {}
    else:
        filtered_agents = agents
    
    # Calculate period stats
    period_stats = {
        "total_cost": sum(s.total_cost for s in recent_sessions),
        "total_tokens": sum(s.input_tokens + s.output_tokens for s in recent_sessions),
        "total_sessions": len(recent_sessions),
        "successful_sessions": len([s for s in recent_sessions if s.success]),
        "unique_agents_used": len(set(s.agent_type for s in recent_sessions))
    }
    
    # Agent breakdown
    agent_breakdown = []
    for agent_type, usage in filtered_agents.items():
        agent_sessions = [s for s in recent_sessions if s.agent_type == agent_type]
        if agent_sessions or usage.total_sessions > 0:
            agent_breakdown.append({
                "agent_type": agent_type,
                "agent_name": usage.agent_name,
                "color": SUB_AGENTS.get(agent_type, {}).get("color", "#737373"),
                "specialty": SUB_AGENTS.get(agent_type, {}).get("specialty", ""),
                "period_cost": sum(s.total_cost for s in agent_sessions),
                "period_sessions": len(agent_sessions),
                "total_cost": usage.total_cost,
                "total_sessions": usage.total_sessions,
                "success_rate": usage.success_rate,
                "average_cost_per_task": usage.average_cost_per_task,
                "last_used": usage.last_used.isoformat() if usage.last_used else None
            })
    
    # Sort by period cost
    agent_breakdown.sort(key=lambda x: x["period_cost"], reverse=True)
    
    return {
        "success": True,
        "period_days": days,
        "period_stats": period_stats,
        "agents": agent_breakdown,
        "top_agents": agent_breakdown[:5] if len(agent_breakdown) > 5 else agent_breakdown
    }

@router.get("/cost-breakdown")
async def get_cost_breakdown(
    group_by: str = Query("agent", description="Group by: agent, model, or day")
):
    """Get detailed cost breakdown"""
    sessions = load_sessions()
    
    breakdown = {}
    
    if group_by == "agent":
        for session in sessions:
            if session.agent_type not in breakdown:
                breakdown[session.agent_type] = {
                    "name": session.agent_type.replace("-", " ").title(),
                    "cost": 0,
                    "sessions": 0,
                    "tokens": 0
                }
            breakdown[session.agent_type]["cost"] += session.total_cost
            breakdown[session.agent_type]["sessions"] += 1
            breakdown[session.agent_type]["tokens"] += session.input_tokens + session.output_tokens
    
    elif group_by == "model":
        for session in sessions:
            model = session.model_used or "unknown"
            if model not in breakdown:
                breakdown[model] = {
                    "cost": 0,
                    "sessions": 0,
                    "tokens": 0
                }
            breakdown[model]["cost"] += session.total_cost
            breakdown[model]["sessions"] += 1
            breakdown[model]["tokens"] += session.input_tokens + session.output_tokens
    
    elif group_by == "day":
        for session in sessions:
            day = session.start_time.date().isoformat()
            if day not in breakdown:
                breakdown[day] = {
                    "cost": 0,
                    "sessions": 0,
                    "agents": set()
                }
            breakdown[day]["cost"] += session.total_cost
            breakdown[day]["sessions"] += 1
            breakdown[day]["agents"].add(session.agent_type)
        
        # Convert sets to counts
        for day in breakdown:
            breakdown[day]["unique_agents"] = len(breakdown[day]["agents"])
            del breakdown[day]["agents"]
    
    return {
        "success": True,
        "group_by": group_by,
        "breakdown": breakdown
    }