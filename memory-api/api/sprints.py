# ABOUTME: Betty AI Sprint Management - Short-burst focused development cycles
# ABOUTME: Tracks LLM costs, sprint velocity, and AI-optimized planning

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import uuid
from pathlib import Path
from enum import Enum

router = APIRouter(prefix="/api/sprints", tags=["sprints"])

# Sprint storage
SPRINTS_DIR = Path.home() / ".betty" / "sprints"
SPRINTS_FILE = SPRINTS_DIR / "sprints.json"
COSTS_FILE = SPRINTS_DIR / "llm_costs.json"

SPRINTS_DIR.mkdir(parents=True, exist_ok=True)

# LLM Cost tracking (per 1K tokens)
LLM_COSTS = {
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
}

class SprintDuration(str, Enum):
    MICRO = "micro"      # 1-2 hours
    MINI = "mini"        # 4 hours
    HALF_DAY = "half"    # 8 hours
    FULL_DAY = "full"    # 24 hours
    
class SprintStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"

class LLMCost(BaseModel):
    task_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[str] = None

class Sprint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    goal: str
    duration: SprintDuration
    status: SprintStatus = SprintStatus.PLANNING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created: datetime = Field(default_factory=datetime.now)
    
    # Sprint capacity
    estimated_hours: float
    actual_hours: float = 0.0
    
    # Tasks
    task_ids: List[str] = []
    completed_task_ids: List[str] = []
    
    # Costs
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    cost_breakdown: Dict[str, float] = {}  # model -> cost
    
    # Metrics
    velocity: float = 0.0  # tasks per hour
    completion_rate: float = 0.0
    cost_per_task: float = 0.0
    tokens_used: int = 0
    
    # AI-specific
    model_preferences: List[str] = ["claude-3-sonnet"]  # Preferred models for this sprint
    parallel_tasks: int = 3  # How many tasks AI can work on simultaneously
    focus_areas: List[str] = []  # e.g., ["backend", "testing", "documentation"]

class SprintPlan(BaseModel):
    sprint_id: str
    task_ids: List[str]
    estimated_hours: float
    estimated_cost: float
    recommendations: List[str]

# Storage functions
def load_sprints() -> Dict[str, Sprint]:
    """Load sprints from file"""
    if SPRINTS_FILE.exists():
        try:
            with open(SPRINTS_FILE, 'r') as f:
                data = json.load(f)
                return {
                    sprint_id: Sprint(**sprint_data)
                    for sprint_id, sprint_data in data.items()
                }
        except Exception as e:
            print(f"Error loading sprints: {e}")
    return {}

def save_sprints(sprints: Dict[str, Sprint]):
    """Save sprints to file"""
    try:
        data = {}
        for sprint_id, sprint in sprints.items():
            sprint_dict = sprint.dict()
            # Convert datetime to ISO format
            for field in ['start_time', 'end_time', 'created']:
                if sprint_dict.get(field):
                    sprint_dict[field] = sprint_dict[field].isoformat()
            data[sprint_id] = sprint_dict
        
        with open(SPRINTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving sprints: {e}")

def load_costs() -> List[LLMCost]:
    """Load LLM costs from file"""
    if COSTS_FILE.exists():
        try:
            with open(COSTS_FILE, 'r') as f:
                data = json.load(f)
                return [LLMCost(**cost) for cost in data]
        except Exception as e:
            print(f"Error loading costs: {e}")
    return []

def save_cost(cost: LLMCost):
    """Append cost to file"""
    costs = load_costs()
    costs.append(cost)
    
    try:
        with open(COSTS_FILE, 'w') as f:
            json.dump([c.dict() for c in costs], f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving cost: {e}")

# API Endpoints
@router.post("/create")
async def create_sprint(
    name: str = Query(..., description="Sprint name"),
    goal: str = Query(..., description="Sprint goal"),
    duration: SprintDuration = Query(SprintDuration.HALF_DAY),
    estimated_hours: float = Query(8.0, description="Estimated hours"),
    focus_areas: Optional[str] = Query(None, description="Comma-separated focus areas")
):
    """Create a new AI sprint"""
    sprints = load_sprints()
    
    # Check for active sprints
    active_sprints = [s for s in sprints.values() if s.status == SprintStatus.ACTIVE]
    if active_sprints:
        return {
            "success": False,
            "message": f"Sprint '{active_sprints[0].name}' is already active. Complete or pause it first."
        }
    
    sprint = Sprint(
        name=name,
        goal=goal,
        duration=duration,
        estimated_hours=estimated_hours,
        focus_areas=focus_areas.split(",") if focus_areas else []
    )
    
    # Set duration-based defaults
    if duration == SprintDuration.MICRO:
        sprint.parallel_tasks = 1
        sprint.estimated_hours = min(2, estimated_hours)
    elif duration == SprintDuration.MINI:
        sprint.parallel_tasks = 2
        sprint.estimated_hours = min(4, estimated_hours)
    elif duration == SprintDuration.HALF_DAY:
        sprint.parallel_tasks = 3
        sprint.estimated_hours = min(8, estimated_hours)
    else:  # FULL_DAY
        sprint.parallel_tasks = 5
        sprint.estimated_hours = min(24, estimated_hours)
    
    sprints[sprint.id] = sprint
    save_sprints(sprints)
    
    return {
        "success": True,
        "message": f"Sprint '{name}' created",
        "sprint": sprint.dict()
    }

@router.post("/start")
async def start_new_sprint(
    title: str = Body(..., description="Sprint title"),
    duration_type: str = Body(..., description="Sprint duration type"),
    tasks: List[str] = Body([], description="Initial tasks for sprint")
):
    """Create and start a new sprint - dashboard compatible endpoint"""
    sprints = load_sprints()
    
    # Check for active sprints
    active_sprints = [s for s in sprints.values() if s.status == SprintStatus.ACTIVE]
    if active_sprints:
        return {
            "success": False,
            "message": f"Sprint '{active_sprints[0].name}' is already active. Complete or pause it first."
        }
    
    # Map duration types
    duration_map = {
        "micro": SprintDuration.MICRO,
        "mini": SprintDuration.MINI,
        "half-day": SprintDuration.HALF_DAY,
        "full-day": SprintDuration.FULL_DAY
    }
    
    duration = duration_map.get(duration_type, SprintDuration.MINI)
    
    # Set duration-based defaults
    hours_map = {
        SprintDuration.MICRO: 2,
        SprintDuration.MINI: 4,
        SprintDuration.HALF_DAY: 8,
        SprintDuration.FULL_DAY: 24
    }
    
    sprint = Sprint(
        name=title,
        goal=f"Complete {len(tasks)} tasks in {duration.value} sprint",
        duration=duration,
        estimated_hours=hours_map[duration],
        task_ids=tasks,
        status=SprintStatus.ACTIVE,
        start_time=datetime.now()
    )
    
    # Set end time
    sprint.end_time = sprint.start_time + timedelta(hours=hours_map[duration])
    
    # Set parallel task defaults
    parallel_map = {
        SprintDuration.MICRO: 1,
        SprintDuration.MINI: 2,
        SprintDuration.HALF_DAY: 3,
        SprintDuration.FULL_DAY: 5
    }
    sprint.parallel_tasks = parallel_map[duration]
    
    sprints[sprint.id] = sprint
    save_sprints(sprints)
    
    return {
        "success": True,
        "message": f"Sprint '{title}' created and started",
        "data": sprint.dict()
    }

@router.post("/{sprint_id}/start")
async def start_sprint(sprint_id: str):
    """Start a sprint"""
    sprints = load_sprints()
    
    if sprint_id not in sprints:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    sprint = sprints[sprint_id]
    
    if sprint.status == SprintStatus.ACTIVE:
        return {"success": False, "message": "Sprint already active"}
    
    sprint.status = SprintStatus.ACTIVE
    sprint.start_time = datetime.now()
    
    # Calculate end time based on duration
    hours = {
        SprintDuration.MICRO: 2,
        SprintDuration.MINI: 4,
        SprintDuration.HALF_DAY: 8,
        SprintDuration.FULL_DAY: 24
    }
    sprint.end_time = sprint.start_time + timedelta(hours=hours[sprint.duration])
    
    save_sprints(sprints)
    
    return {
        "success": True,
        "message": f"Sprint '{sprint.name}' started",
        "sprint": sprint.dict()
    }

@router.post("/{sprint_id}/add-tasks")
async def add_tasks_to_sprint(
    sprint_id: str,
    task_ids: List[str] = Body(..., description="List of task IDs to add")
):
    """Add tasks to a sprint"""
    sprints = load_sprints()
    
    if sprint_id not in sprints:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    sprint = sprints[sprint_id]
    
    # Add unique task IDs
    for task_id in task_ids:
        if task_id not in sprint.task_ids:
            sprint.task_ids.append(task_id)
    
    save_sprints(sprints)
    
    return {
        "success": True,
        "message": f"Added {len(task_ids)} tasks to sprint",
        "sprint": sprint.dict()
    }

@router.post("/track-cost")
async def track_llm_cost(
    task_id: str = Query(...),
    model: str = Query(...),
    input_tokens: int = Query(...),
    output_tokens: int = Query(...),
    context: Optional[str] = Query(None)
):
    """Track LLM API cost for a task"""
    
    # Calculate cost
    model_key = model.lower().replace("_", "-")
    if model_key not in LLM_COSTS:
        model_key = "claude-3-sonnet"  # Default
    
    input_cost = (input_tokens / 1000) * LLM_COSTS[model_key]["input"]
    output_cost = (output_tokens / 1000) * LLM_COSTS[model_key]["output"]
    total_cost = input_cost + output_cost
    
    cost = LLMCost(
        task_id=task_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=total_cost,
        context=context
    )
    
    save_cost(cost)
    
    # Update active sprint if exists
    sprints = load_sprints()
    active_sprints = [s for s in sprints.values() if s.status == SprintStatus.ACTIVE]
    
    if active_sprints and task_id in active_sprints[0].task_ids:
        sprint = active_sprints[0]
        sprint.actual_cost += total_cost
        sprint.tokens_used += input_tokens + output_tokens
        
        # Update cost breakdown
        if model not in sprint.cost_breakdown:
            sprint.cost_breakdown[model] = 0
        sprint.cost_breakdown[model] += total_cost
        
        save_sprints(sprints)
    
    return {
        "success": True,
        "cost": total_cost,
        "breakdown": {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_tokens": input_tokens + output_tokens
        }
    }

@router.get("/active")
async def get_active_sprint():
    """Get the currently active sprint"""
    sprints = load_sprints()
    active = [s for s in sprints.values() if s.status == SprintStatus.ACTIVE]
    
    if not active:
        return {"success": False, "message": "No active sprint"}
    
    sprint = active[0]
    
    # Calculate progress
    if sprint.start_time:
        elapsed = (datetime.now() - sprint.start_time).total_seconds() / 3600
        sprint.actual_hours = elapsed
        
        if sprint.task_ids:
            sprint.completion_rate = len(sprint.completed_task_ids) / len(sprint.task_ids) * 100
            sprint.velocity = len(sprint.completed_task_ids) / max(1, elapsed)
            
            if sprint.actual_cost > 0:
                sprint.cost_per_task = sprint.actual_cost / max(1, len(sprint.completed_task_ids))
    
    return {
        "success": True,
        "sprint": sprint.dict()
    }

@router.post("/{sprint_id}/complete")
async def complete_sprint(sprint_id: str):
    """Mark a sprint as completed"""
    sprints = load_sprints()
    
    if sprint_id not in sprints:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    sprint = sprints[sprint_id]
    sprint.status = SprintStatus.COMPLETED
    sprint.end_time = datetime.now()
    
    # Calculate final metrics
    if sprint.start_time:
        sprint.actual_hours = (sprint.end_time - sprint.start_time).total_seconds() / 3600
        
        if sprint.task_ids:
            sprint.completion_rate = len(sprint.completed_task_ids) / len(sprint.task_ids) * 100
            sprint.velocity = len(sprint.completed_task_ids) / max(1, sprint.actual_hours)
            
            if sprint.actual_cost > 0:
                sprint.cost_per_task = sprint.actual_cost / max(1, len(sprint.completed_task_ids))
    
    save_sprints(sprints)
    
    return {
        "success": True,
        "message": f"Sprint '{sprint.name}' completed",
        "metrics": {
            "duration": f"{sprint.actual_hours:.1f} hours",
            "tasks_completed": len(sprint.completed_task_ids),
            "completion_rate": f"{sprint.completion_rate:.1f}%",
            "total_cost": f"${sprint.actual_cost:.4f}",
            "cost_per_task": f"${sprint.cost_per_task:.4f}",
            "velocity": f"{sprint.velocity:.1f} tasks/hour",
            "tokens_used": sprint.tokens_used
        }
    }

@router.get("/list")
async def list_sprints(
    status: Optional[SprintStatus] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """List all sprints"""
    sprints = load_sprints()
    
    # Filter by status
    if status:
        filtered = [s for s in sprints.values() if s.status == status]
    else:
        filtered = list(sprints.values())
    
    # Sort by creation date
    filtered.sort(key=lambda s: s.created, reverse=True)
    
    return {
        "success": True,
        "count": len(filtered[:limit]),
        "sprints": [s.dict() for s in filtered[:limit]]
    }

@router.get("/costs/summary")
async def get_cost_summary(
    days: int = Query(7, description="Number of days to look back")
):
    """Get cost summary for recent period"""
    costs = load_costs()
    cutoff = datetime.now() - timedelta(days=days)
    
    recent_costs = [c for c in costs if c.timestamp >= cutoff]
    
    # Aggregate by model
    by_model = {}
    for cost in recent_costs:
        if cost.model not in by_model:
            by_model[cost.model] = {"count": 0, "cost": 0, "tokens": 0}
        by_model[cost.model]["count"] += 1
        by_model[cost.model]["cost"] += cost.cost
        by_model[cost.model]["tokens"] += cost.input_tokens + cost.output_tokens
    
    total_cost = sum(c.cost for c in recent_costs)
    total_tokens = sum(c.input_tokens + c.output_tokens for c in recent_costs)
    
    return {
        "success": True,
        "period_days": days,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "total_calls": len(recent_costs),
        "average_cost_per_call": total_cost / max(1, len(recent_costs)),
        "by_model": by_model
    }