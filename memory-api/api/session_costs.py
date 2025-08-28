"""
ABOUTME: Betty Session Cost API - Manages session cost tracking and predictions
ABOUTME: Provides endpoints for cost estimation, token tracking, and prediction analytics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

router = APIRouter()

# Session cost data model
class SessionCost(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    session_date: str
    files_analyzed: int
    work_completed: List[str]

class CostPrediction(BaseModel):
    estimated_remaining_tokens: int
    estimated_remaining_cost: float
    projected_session_cost: float
    cost_per_task: float
    efficiency_score: float

# File paths
SESSION_COSTS_FILE = Path.home() / ".betty" / "session-costs.jsonl"
TOKEN_USAGE_FILE = Path.home() / ".betty" / "token-usage.jsonl"

def ensure_directories():
    """Ensure required directories exist"""
    SESSION_COSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

def read_session_costs() -> List[SessionCost]:
    """Read all session costs from file"""
    ensure_directories()
    
    if not SESSION_COSTS_FILE.exists():
        return []
    
    costs = []
    try:
        with open(SESSION_COSTS_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    
                    # Handle different field names for backward compatibility
                    if 'files_modified' in data and 'files_analyzed' not in data:
                        data['files_analyzed'] = data['files_modified']
                    
                    # Ensure required fields exist
                    if 'files_analyzed' not in data:
                        data['files_analyzed'] = 0
                    if 'work_completed' not in data:
                        data['work_completed'] = []
                    
                    costs.append(SessionCost(**data))
    except Exception as e:
        print(f"Error reading session costs: {e}")
        return []
    
    return costs

def get_latest_session_cost() -> Optional[SessionCost]:
    """Get the most recent session cost"""
    costs = read_session_costs()
    if not costs:
        return None
    
    # Sort by session_date and return the latest
    costs.sort(key=lambda x: x.session_date, reverse=True)
    return costs[0]

def run_cost_estimator() -> Optional[SessionCost]:
    """Run the session cost estimator script"""
    try:
        script_path = Path(__file__).parent.parent.parent / "hooks" / "estimate-session-cost.py"
        if script_path.exists():
            result = subprocess.run(
                ["python3", str(script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Read the latest cost after running estimator
                return get_latest_session_cost()
    except Exception as e:
        print(f"Error running cost estimator: {e}")
    
    return None

@router.get("/latest")
async def get_latest_session_costs():
    """Get the latest session cost data"""
    try:
        cost = get_latest_session_cost()
        
        if not cost:
            # Try to generate new cost estimate
            cost = run_cost_estimator()
        
        if not cost:
            # Return default/empty cost data
            cost = SessionCost(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                session_date=datetime.now().isoformat(),
                files_analyzed=0,
                work_completed=[]
            )
        
        return {
            "success": True,
            "session_cost": cost.dict(),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session costs: {str(e)}")

@router.get("/history")
async def get_session_cost_history(days: int = 7):
    """Get session cost history for the last N days"""
    try:
        costs = read_session_costs()
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_costs = [
            cost for cost in costs 
            if datetime.fromisoformat(cost.session_date.replace('Z', '+00:00')) > cutoff_date
        ]
        
        # Sort by date
        recent_costs.sort(key=lambda x: x.session_date, reverse=True)
        
        return {
            "success": True,
            "count": len(recent_costs),
            "period_days": days,
            "costs": [cost.dict() for cost in recent_costs],
            "total_cost": sum(cost.total_cost for cost in recent_costs),
            "total_tokens": sum(cost.total_tokens for cost in recent_costs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost history: {str(e)}")

@router.post("/estimate")
async def create_cost_estimate():
    """Generate a new cost estimate for the current session"""
    try:
        cost = run_cost_estimator()
        
        if not cost:
            raise HTTPException(status_code=500, detail="Failed to generate cost estimate")
        
        return {
            "success": True,
            "session_cost": cost.dict(),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create estimate: {str(e)}")

@router.get("/summary")
async def get_cost_summary():
    """Get a summary of all session costs"""
    try:
        costs = read_session_costs()
        
        if not costs:
            return {
                "success": True,
                "total_sessions": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "average_cost_per_session": 0.0,
                "average_tokens_per_session": 0,
                "date_range": None
            }
        
        total_cost = sum(cost.total_cost for cost in costs)
        total_tokens = sum(cost.total_tokens for cost in costs)
        
        # Sort by date to get range
        costs.sort(key=lambda x: x.session_date)
        
        return {
            "success": True,
            "total_sessions": len(costs),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "average_cost_per_session": total_cost / len(costs) if costs else 0,
            "average_tokens_per_session": total_tokens // len(costs) if costs else 0,
            "date_range": {
                "start": costs[0].session_date,
                "end": costs[-1].session_date
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")