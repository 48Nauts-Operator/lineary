"""
ABOUTME: Enhanced Task Management API with Git integration and Sprint Poker estimation
ABOUTME: Provides comprehensive task workflow management for AI-driven development
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

router = APIRouter()

# Database dependency
async def get_db_session(request: Request):
    """Get database session from app state"""
    db_manager = request.app.state.db_manager
    async with db_manager.get_postgres_session() as session:
        yield session

# Enhanced Task Models
class TaskDescription(BaseModel):
    description: str
    acceptance_criteria: List[str] = []
    technical_notes: Optional[str] = None
    dependencies: List[str] = []

class SprintEstimate(BaseModel):
    complexity_score: int = Field(ge=1, le=13)  # Fibonacci scale
    story_points: int = Field(ge=1, le=13)
    estimated_hours: float = Field(ge=0.1, le=100.0)
    estimated_tokens: int = Field(ge=0)
    estimated_cost: float = Field(ge=0.0)
    confidence_level: float = Field(ge=0.0, le=1.0)
    model_used: str = "claude-sonnet"
    analysis_factors: Dict[str, Any] = {}
    similar_tasks: List[str] = []
    reusability_score: float = Field(ge=0.0, le=1.0, default=0.0)
    optimization_suggestions: List[str] = []

class GitIntegration(BaseModel):
    branch_name: Optional[str] = None
    worktree_path: Optional[str] = None
    commit_hashes: List[str] = []
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    base_branch: str = "main"
    merge_status: str = "pending"

class TaskState(BaseModel):
    state: str = "planning"  # planning, implementing, validating, pushing, testing, merging, closing, done
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}

class EnhancedTaskCreate(BaseModel):
    task: str
    priority: int = 3
    description: TaskDescription
    sprint_estimate: Optional[SprintEstimate] = None
    git_integration: Optional[GitIntegration] = None
    initial_state: str = "planning"

class EnhancedTaskResponse(BaseModel):
    id: str
    task: str
    status: str
    priority: int
    created: str
    updated: str
    description: Optional[TaskDescription] = None
    sprint_estimate: Optional[SprintEstimate] = None
    git_integration: Optional[GitIntegration] = None
    current_state: Optional[str] = None
    validation_status: Dict[str, str] = {}
    metrics: Optional[Dict[str, Any]] = None

# Sprint Poker Estimation Engine
class SprintPokerEngine:
    def __init__(self):
        self.complexity_factors = {
            "code_footprint": 0.3,    # Lines of code / files
            "integration_depth": 0.25, # Number of systems/APIs
            "test_complexity": 0.2,   # Testing requirements
            "uncertainty": 0.15,      # Novel/unknown aspects  
            "data_volume": 0.1        # Data processing needs
        }
        
        # Base token costs for different task types
        self.base_token_costs = {
            "ui_component": {"input": 8000, "output": 12000},
            "api_endpoint": {"input": 6000, "output": 8000},
            "database_migration": {"input": 4000, "output": 6000},
            "bug_fix": {"input": 5000, "output": 7000},
            "integration": {"input": 10000, "output": 15000},
            "testing": {"input": 3000, "output": 5000},
            "documentation": {"input": 4000, "output": 8000}
        }
        
        # LLM pricing per 1M tokens
        self.llm_pricing = {
            "claude-opus": {"input": 15.00, "output": 75.00},
            "claude-sonnet": {"input": 3.00, "output": 15.00},
            "claude-haiku": {"input": 0.25, "output": 1.25}
        }
    
    async def estimate_task(self, task_text: str, description: TaskDescription, session: AsyncSession) -> SprintEstimate:
        """Generate AI-powered sprint poker estimation"""
        
        # Analyze task complexity
        complexity_analysis = self._analyze_complexity(task_text, description)
        
        # Find similar completed tasks
        similar_tasks = await self._find_similar_tasks(task_text, session)
        
        # Calculate story points and time estimates
        story_points = self._calculate_story_points(complexity_analysis)
        estimated_hours = self._calculate_time_estimate(story_points, similar_tasks)
        
        # Estimate token usage and cost
        token_estimate = self._estimate_tokens(task_text, description, complexity_analysis)
        cost_estimate = self._calculate_cost(token_estimate, "claude-sonnet")
        
        # Calculate confidence and reusability
        confidence = self._calculate_confidence(similar_tasks, complexity_analysis)
        reusability = await self._calculate_reusability(description, session)
        
        return SprintEstimate(
            complexity_score=complexity_analysis["total_score"],
            story_points=story_points,
            estimated_hours=estimated_hours,
            estimated_tokens=token_estimate["total"],
            estimated_cost=cost_estimate,
            confidence_level=confidence,
            analysis_factors=complexity_analysis,
            similar_tasks=[t["id"] for t in similar_tasks],
            reusability_score=reusability,
            optimization_suggestions=self._generate_optimizations(complexity_analysis, reusability)
        )
    
    def _analyze_complexity(self, task_text: str, description: TaskDescription) -> Dict[str, Any]:
        """Analyze task complexity across multiple dimensions"""
        
        # Determine task type
        task_type = self._determine_task_type(task_text, description)
        
        # Score complexity factors (1-13 Fibonacci scale)
        scores = {}
        
        # Code footprint analysis
        if any(keyword in task_text.lower() for keyword in ["dashboard", "ui", "interface", "component"]):
            scores["code_footprint"] = 8  # UI work is typically complex
        elif any(keyword in task_text.lower() for keyword in ["api", "endpoint", "service"]):
            scores["code_footprint"] = 5  # API work is moderate
        elif any(keyword in task_text.lower() for keyword in ["fix", "bug", "patch"]):
            scores["code_footprint"] = 3  # Bug fixes are usually small
        else:
            scores["code_footprint"] = 5  # Default moderate
        
        # Integration depth
        integration_keywords = len([k for k in ["integration", "api", "database", "git", "docker"] 
                                  if k in task_text.lower() or k in description.description.lower()])
        scores["integration_depth"] = min(13, max(1, integration_keywords * 3))
        
        # Test complexity
        if any(keyword in description.description.lower() for keyword in ["test", "validation", "coverage"]):
            scores["test_complexity"] = 8
        else:
            scores["test_complexity"] = 3  # Assume basic testing
        
        # Uncertainty factor
        uncertainty_indicators = len([k for k in ["new", "research", "explore", "experimental"] 
                                    if k in task_text.lower()])
        scores["uncertainty"] = min(13, max(1, uncertainty_indicators * 4 + 1))
        
        # Data volume
        if any(keyword in task_text.lower() for keyword in ["migration", "data", "bulk", "process"]):
            scores["data_volume"] = 8
        else:
            scores["data_volume"] = 2
        
        # Calculate weighted total
        total_score = sum(scores[factor] * weight for factor, weight in self.complexity_factors.items())
        total_score = min(13, max(1, round(total_score)))
        
        return {
            "task_type": task_type,
            "scores": scores,
            "total_score": int(total_score),
            "complexity_factors": self.complexity_factors
        }
    
    def _determine_task_type(self, task_text: str, description: TaskDescription) -> str:
        """Determine the primary type of task"""
        text = (task_text + " " + description.description).lower()
        
        if any(keyword in text for keyword in ["ui", "dashboard", "component", "interface"]):
            return "ui_component"
        elif any(keyword in text for keyword in ["api", "endpoint", "service", "route"]):
            return "api_endpoint"
        elif any(keyword in text for keyword in ["database", "migration", "schema"]):
            return "database_migration"
        elif any(keyword in text for keyword in ["fix", "bug", "patch", "error"]):
            return "bug_fix"
        elif any(keyword in text for keyword in ["integration", "connect", "sync"]):
            return "integration"
        elif any(keyword in text for keyword in ["test", "testing", "validation"]):
            return "testing"
        elif any(keyword in text for keyword in ["doc", "documentation", "readme"]):
            return "documentation"
        else:
            return "api_endpoint"  # Default
    
    async def _find_similar_tasks(self, task_text: str, session: AsyncSession) -> List[Dict[str, Any]]:
        """Find similar completed tasks for estimation reference"""
        try:
            # Simple keyword-based similarity for now
            # In production, would use vector similarity with embeddings
            keywords = [word.lower() for word in task_text.split() if len(word) > 3]
            
            if not keywords:
                return []
            
            # Search for tasks with similar keywords
            keyword_query = " OR ".join([f"t.task ILIKE '%{keyword}%'" for keyword in keywords[:3]])
            
            query = f"""
            SELECT t.id, t.task, tm.actual_hours, tm.actual_tokens, tm.actual_cost,
                   tm.efficiency_score, se.story_points, se.complexity_score
            FROM tasks t
            LEFT JOIN task_metrics tm ON t.id = tm.task_id
            LEFT JOIN sprint_estimates se ON t.id = se.task_id
            WHERE t.status = 'completed' 
            AND ({keyword_query})
            ORDER BY t.updated DESC
            LIMIT 5
            """
            
            result = await session.execute(text(query))
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]
            
        except Exception as e:
            print(f"Error finding similar tasks: {e}")
            return []
    
    def _calculate_story_points(self, complexity_analysis: Dict[str, Any]) -> int:
        """Convert complexity score to Fibonacci story points"""
        score = complexity_analysis["total_score"]
        
        # Map to Fibonacci scale: 1, 2, 3, 5, 8, 13
        if score <= 2:
            return 1
        elif score <= 4:
            return 2
        elif score <= 6:
            return 3
        elif score <= 9:
            return 5
        elif score <= 11:
            return 8
        else:
            return 13
    
    def _calculate_time_estimate(self, story_points: int, similar_tasks: List[Dict[str, Any]]) -> float:
        """Calculate time estimate based on story points and historical data"""
        
        # Base time estimates per story point (in hours)
        base_hours_per_point = {1: 0.5, 2: 1.0, 3: 2.0, 5: 4.0, 8: 8.0, 13: 16.0}
        base_estimate = base_hours_per_point.get(story_points, 4.0)
        
        # Adjust based on similar tasks
        if similar_tasks:
            historical_hours = [t.get("actual_hours", 0) for t in similar_tasks if t.get("actual_hours")]
            if historical_hours:
                avg_historical = sum(historical_hours) / len(historical_hours)
                # Weight 70% base estimate, 30% historical average
                base_estimate = (base_estimate * 0.7) + (avg_historical * 0.3)
        
        return round(base_estimate, 1)
    
    def _estimate_tokens(self, task_text: str, description: TaskDescription, complexity_analysis: Dict[str, Any]) -> Dict[str, int]:
        """Estimate token usage for the task"""
        
        task_type = complexity_analysis["task_type"]
        base_tokens = self.base_token_costs.get(task_type, self.base_token_costs["api_endpoint"])
        
        # Adjust based on complexity
        complexity_multiplier = complexity_analysis["total_score"] / 5.0  # Normalize to ~1.0
        
        input_tokens = int(base_tokens["input"] * complexity_multiplier)
        output_tokens = int(base_tokens["output"] * complexity_multiplier)
        
        return {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens
        }
    
    def _calculate_cost(self, token_estimate: Dict[str, int], model: str = "claude-sonnet") -> float:
        """Calculate cost based on token usage and model pricing"""
        
        pricing = self.llm_pricing.get(model, self.llm_pricing["claude-sonnet"])
        
        input_cost = (token_estimate["input"] / 1_000_000) * pricing["input"]
        output_cost = (token_estimate["output"] / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 4)
    
    def _calculate_confidence(self, similar_tasks: List[Dict[str, Any]], complexity_analysis: Dict[str, Any]) -> float:
        """Calculate confidence level in the estimate"""
        
        base_confidence = 0.7  # Start with 70% confidence
        
        # Boost confidence if we have similar tasks
        if similar_tasks:
            similarity_boost = min(0.2, len(similar_tasks) * 0.05)
            base_confidence += similarity_boost
        
        # Reduce confidence for high uncertainty
        uncertainty_penalty = complexity_analysis["scores"].get("uncertainty", 1) * 0.02
        base_confidence -= uncertainty_penalty
        
        return round(max(0.3, min(0.95, base_confidence)), 2)
    
    async def _calculate_reusability(self, description: TaskDescription, session: AsyncSession) -> float:
        """Calculate how much existing code can be reused"""
        
        # Simple heuristic based on keywords
        reuse_keywords = ["similar", "existing", "template", "copy", "reuse"]
        
        reuse_mentions = sum(1 for keyword in reuse_keywords 
                           if keyword in description.description.lower())
        
        base_reusability = min(0.8, reuse_mentions * 0.2)
        
        return round(base_reusability, 2)
    
    def _generate_optimizations(self, complexity_analysis: Dict[str, Any], reusability: float) -> List[str]:
        """Generate optimization suggestions"""
        
        suggestions = []
        
        if complexity_analysis["scores"].get("code_footprint", 0) > 8:
            suggestions.append("Consider breaking into smaller, focused tasks")
        
        if reusability < 0.3:
            suggestions.append("Look for existing patterns or components to reuse")
        
        if complexity_analysis["scores"].get("integration_depth", 0) > 8:
            suggestions.append("Plan integration points carefully to avoid conflicts")
        
        if complexity_analysis["scores"].get("uncertainty", 0) > 8:
            suggestions.append("Consider a research spike or proof-of-concept first")
        
        return suggestions

# Git Integration Service
class GitIntegrationService:
    def __init__(self, base_repo_path: str = "/home/jarvis/projects/Betty"):
        self.base_repo_path = Path(base_repo_path)
        self.worktrees_dir = self.base_repo_path / "worktrees"
        self.worktrees_dir.mkdir(exist_ok=True)
        
        # Add git safe directory for container environment
        try:
            subprocess.run(["git", "config", "--global", "--add", "safe.directory", str(self.base_repo_path)], 
                         capture_output=True, check=False)
        except:
            pass
    
    async def create_task_branch(self, task_id: str, task_title: str) -> GitIntegration:
        """Create git branch and worktree for task"""
        
        # Generate branch name
        branch_name = self._generate_branch_name(task_id, task_title)
        worktree_path = self.worktrees_dir / f"task-{task_id}"
        
        try:
            # Ensure we're in the git repository
            os.chdir(self.base_repo_path)
            
            # Create worktree with new branch
            result = subprocess.run([
                "git", "worktree", "add", "-b", branch_name, 
                str(worktree_path), "main"
            ], cwd=self.base_repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Git worktree creation failed: {result.stderr}")
                # Return without Git integration but don't fail the whole task
                return None
            
            return GitIntegration(
                branch_name=branch_name,
                worktree_path=str(worktree_path),
                base_branch="main",
                merge_status="pending"
            )
            
        except Exception as e:
            print(f"Git integration failed: {e}")
            # Return None to allow task creation without Git integration
            return None
    
    def _generate_branch_name(self, task_id: str, task_title: str) -> str:
        """Generate standardized branch name"""
        
        # Clean task title for branch name
        clean_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in task_title.lower())
        clean_title = clean_title[:30]  # Limit length
        
        return f"feature/TASK-{task_id[:8]}-{clean_title}"
    
    async def create_pull_request(self, git_integration: GitIntegration, task_data: Dict[str, Any]) -> str:
        """Create pull request for task (placeholder - would integrate with GitHub API)"""
        
        # In a real implementation, this would use GitHub/GitLab API
        # For now, return a mock PR URL
        pr_number = hash(git_integration.branch_name) % 10000
        pr_url = f"https://github.com/user/betty/pull/{pr_number}"
        
        return pr_url

# API Endpoints
@router.post("/enhanced-tasks", response_model=EnhancedTaskResponse)
async def create_enhanced_task(
    task_data: EnhancedTaskCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create enhanced task with full workflow integration"""
    
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create base task
        task_query = """
        INSERT INTO tasks (id, task, status, priority, type, created, updated)
        VALUES (:id, :task, 'pending', :priority, 'enhanced', NOW(), NOW())
        """
        
        await session.execute(text(task_query), {
            "id": task_id,
            "task": task_data.task,
            "priority": task_data.priority
        })
        
        # Add task description
        desc_query = """
        INSERT INTO task_descriptions (task_id, description, acceptance_criteria, technical_notes, dependencies)
        VALUES (:task_id, :description, :criteria, :notes, :deps)
        """
        
        await session.execute(text(desc_query), {
            "task_id": task_id,
            "description": task_data.description.description,
            "criteria": task_data.description.acceptance_criteria,
            "notes": task_data.description.technical_notes,
            "deps": task_data.description.dependencies
        })
        
        # Generate Sprint Poker estimation if not provided
        poker_engine = SprintPokerEngine()
        if task_data.sprint_estimate:
            estimate = task_data.sprint_estimate
        else:
            estimate = await poker_engine.estimate_task(task_data.task, task_data.description, session)
        
        # Save sprint estimate
        estimate_query = """
        INSERT INTO sprint_estimates (
            task_id, complexity_score, story_points, estimated_hours, 
            estimated_tokens, estimated_cost, confidence_level, model_used,
            analysis_factors, similar_tasks, reusability_score, optimization_suggestions
        ) VALUES (
            :task_id, :complexity, :points, :hours, :tokens, :cost, :confidence, :model,
            :factors, :similar, :reusability, :suggestions
        )
        """
        
        await session.execute(text(estimate_query), {
            "task_id": task_id,
            "complexity": estimate.complexity_score,
            "points": estimate.story_points,
            "hours": estimate.estimated_hours,
            "tokens": estimate.estimated_tokens,
            "cost": estimate.estimated_cost,
            "confidence": estimate.confidence_level,
            "model": estimate.model_used,
            "factors": json.dumps(estimate.analysis_factors),
            "similar": json.dumps(estimate.similar_tasks),
            "reusability": estimate.reusability_score,
            "suggestions": estimate.optimization_suggestions
        })
        
        # Create git integration if requested
        git_data = None
        if task_data.git_integration:
            try:
                git_service = GitIntegrationService()
                git_data = await git_service.create_task_branch(task_id, task_data.task)
                
                if git_data:  # Only insert if Git integration succeeded
                    git_query = """
                    INSERT INTO git_integration (task_id, branch_name, worktree_path, base_branch, merge_status)
                    VALUES (:task_id, :branch, :worktree, :base, :status)
                    """
                    
                    await session.execute(text(git_query), {
                        "task_id": task_id,
                        "branch": git_data.branch_name,
                        "worktree": git_data.worktree_path,
                        "base": git_data.base_branch,
                        "status": git_data.merge_status
                    })
                else:
                    print(f"Git integration not available for task {task_id}")
            except Exception as e:
                print(f"Git integration failed: {e}")
                # Continue without git integration
        
        # Set initial task state
        state_query = """
        INSERT INTO task_states (task_id, state, changed_by, notes)
        VALUES (:task_id, :state, :changed_by, :notes)
        """
        
        await session.execute(text(state_query), {
            "task_id": task_id,
            "state": task_data.initial_state,
            "changed_by": "system",
            "notes": "Task created with enhanced workflow"
        })
        
        await session.commit()
        
        return EnhancedTaskResponse(
            id=task_id,
            task=task_data.task,
            status="pending",
            priority=task_data.priority,
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
            description=task_data.description,
            sprint_estimate=estimate,
            git_integration=git_data,
            current_state=task_data.initial_state
        )
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced task: {str(e)}")

@router.get("/enhanced-tasks/{task_id}", response_model=EnhancedTaskResponse)
async def get_enhanced_task(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get enhanced task with all related data"""
    
    try:
        query = """
        SELECT 
            t.id, t.task, t.status, t.priority, t.created, t.updated,
            td.description, td.acceptance_criteria, td.technical_notes, td.dependencies,
            se.complexity_score, se.story_points, se.estimated_hours, se.estimated_tokens,
            se.estimated_cost, se.confidence_level, se.model_used, se.analysis_factors,
            se.similar_tasks, se.reusability_score, se.optimization_suggestions,
            gi.branch_name, gi.worktree_path, gi.commit_hashes, gi.pr_url, gi.pr_number,
            gi.base_branch, gi.merge_status,
            ts.state as current_state
        FROM tasks t
        LEFT JOIN task_descriptions td ON t.id = td.task_id
        LEFT JOIN sprint_estimates se ON t.id = se.task_id
        LEFT JOIN git_integration gi ON t.id = gi.task_id
        LEFT JOIN task_states ts ON t.id = ts.task_id AND ts.id = (
            SELECT id FROM task_states WHERE task_id = t.id ORDER BY changed_at DESC LIMIT 1
        )
        WHERE t.id = :task_id
        """
        
        result = await session.execute(text(query), {"task_id": task_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        data = dict(row._mapping)
        
        # Build response
        response = EnhancedTaskResponse(
            id=data["id"],
            task=data["task"],
            status=data["status"],
            priority=data["priority"],
            created=data["created"].isoformat() if data["created"] else "",
            updated=data["updated"].isoformat() if data["updated"] else "",
            current_state=data["current_state"]
        )
        
        # Add description if available
        if data["description"]:
            response.description = TaskDescription(
                description=data["description"],
                acceptance_criteria=data["acceptance_criteria"] or [],
                technical_notes=data["technical_notes"],
                dependencies=data["dependencies"] or []
            )
        
        # Add sprint estimate if available
        if data["story_points"]:
            response.sprint_estimate = SprintEstimate(
                complexity_score=data["complexity_score"],
                story_points=data["story_points"],
                estimated_hours=float(data["estimated_hours"]),
                estimated_tokens=data["estimated_tokens"],
                estimated_cost=float(data["estimated_cost"]),
                confidence_level=float(data["confidence_level"]),
                model_used=data["model_used"],
                analysis_factors=json.loads(data["analysis_factors"]) if data["analysis_factors"] else {},
                similar_tasks=json.loads(data["similar_tasks"]) if data["similar_tasks"] else [],
                reusability_score=float(data["reusability_score"]) if data["reusability_score"] else 0.0,
                optimization_suggestions=data["optimization_suggestions"] or []
            )
        
        # Add git integration if available
        if data["branch_name"]:
            response.git_integration = GitIntegration(
                branch_name=data["branch_name"],
                worktree_path=data["worktree_path"],
                commit_hashes=data["commit_hashes"] or [],
                pr_url=data["pr_url"],
                pr_number=data["pr_number"],
                base_branch=data["base_branch"],
                merge_status=data["merge_status"]
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced task: {str(e)}")

@router.put("/enhanced-tasks/{task_id}/state")
async def update_task_state(
    task_id: str,
    state_data: TaskState,
    session: AsyncSession = Depends(get_db_session)
):
    """Update task workflow state"""
    
    try:
        # Insert new state record
        query = """
        INSERT INTO task_states (task_id, state, previous_state, changed_by, notes, metadata)
        VALUES (:task_id, :state, 
                (SELECT state FROM task_states WHERE task_id = :task_id ORDER BY changed_at DESC LIMIT 1),
                :changed_by, :notes, :metadata)
        """
        
        await session.execute(text(query), {
            "task_id": task_id,
            "state": state_data.state,
            "changed_by": "api",
            "notes": state_data.notes,
            "metadata": json.dumps(state_data.metadata)
        })
        
        await session.commit()
        
        return {"success": True, "message": f"Task state updated to {state_data.state}"}
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update task state: {str(e)}")

@router.post("/enhanced-tasks/estimate")
async def estimate_task(
    task_data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Generate AI Sprint Poker estimation for a task"""
    
    try:
        poker_engine = SprintPokerEngine()
        
        # Create TaskDescription from dict
        description = TaskDescription(
            description=task_data.get("description", {}).get("description", ""),
            acceptance_criteria=task_data.get("description", {}).get("acceptance_criteria", []),
            technical_notes=task_data.get("description", {}).get("technical_notes"),
            dependencies=task_data.get("description", {}).get("dependencies", [])
        )
        
        # Generate estimation
        estimate = await poker_engine.estimate_task(
            task_data.get("task", ""),
            description,
            session
        )
        
        return estimate.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation failed: {str(e)}")

# Simple task creation model for basic dashboard use
class SimpleTaskCreate(BaseModel):
    task: str
    priority: int = 3
    status: str = "pending"
    description: Optional[str] = None

@router.post("/enhanced-tasks/create")
async def create_simple_enhanced_task(
    task_data: SimpleTaskCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create enhanced task with simple input - for dashboard compatibility"""
    
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create base task
        task_query = """
        INSERT INTO tasks (id, task, status, priority, type, created, updated)
        VALUES (:id, :task, :status, :priority, 'enhanced', NOW(), NOW())
        """
        
        await session.execute(text(task_query), {
            "id": task_id,
            "task": task_data.task,
            "status": task_data.status,
            "priority": task_data.priority
        })
        
        # Add basic description
        description_text = task_data.description or task_data.task
        desc_query = """
        INSERT INTO task_descriptions (task_id, description, acceptance_criteria, technical_notes, dependencies)
        VALUES (:task_id, :description, :criteria, :notes, :deps)
        """
        
        await session.execute(text(desc_query), {
            "task_id": task_id,
            "description": description_text,
            "criteria": ["Task completed successfully"],
            "notes": "Auto-generated task",
            "deps": []
        })
        
        # Generate automatic estimation
        poker_engine = SprintPokerEngine()
        task_desc = TaskDescription(
            description=description_text,
            acceptance_criteria=["Task completed successfully"],
            technical_notes="Auto-generated task",
            dependencies=[]
        )
        
        estimate = await poker_engine.estimate_task(task_data.task, task_desc, session)
        
        # Save sprint estimate
        estimate_query = """
        INSERT INTO sprint_estimates (
            task_id, complexity_score, story_points, estimated_hours, 
            estimated_tokens, estimated_cost, confidence_level, model_used,
            analysis_factors, similar_tasks, reusability_score, optimization_suggestions
        ) VALUES (
            :task_id, :complexity, :points, :hours, :tokens, :cost, :confidence, :model,
            :factors, :similar, :reusability, :suggestions
        )
        """
        
        await session.execute(text(estimate_query), {
            "task_id": task_id,
            "complexity": estimate.complexity_score,
            "points": estimate.story_points,
            "hours": estimate.estimated_hours,
            "tokens": estimate.estimated_tokens,
            "cost": estimate.estimated_cost,
            "confidence": estimate.confidence_level,
            "model": estimate.model_used,
            "factors": json.dumps(estimate.analysis_factors),
            "similar": json.dumps(estimate.similar_tasks),
            "reusability": estimate.reusability_score,
            "suggestions": estimate.optimization_suggestions
        })
        
        # Set initial task state
        state_query = """
        INSERT INTO task_states (task_id, state, changed_by, notes)
        VALUES (:task_id, :state, :changed_by, :notes)
        """
        
        await session.execute(text(state_query), {
            "task_id": task_id,
            "state": "planning",
            "changed_by": "dashboard",
            "notes": "Task created via dashboard"
        })
        
        await session.commit()
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Enhanced task created successfully",
            "estimate": {
                "story_points": estimate.story_points,
                "estimated_hours": estimate.estimated_hours,
                "estimated_cost": estimate.estimated_cost
            }
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced task: {str(e)}")

@router.put("/enhanced-tasks/{task_id}/update")
async def update_enhanced_task(
    task_id: str,
    update_data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Update enhanced task properties"""
    
    try:
        # Update base task if needed
        if any(key in update_data for key in ["task", "status", "priority"]):
            update_fields = []
            params = {"task_id": task_id}
            
            if "task" in update_data:
                update_fields.append("task = :task")
                params["task"] = update_data["task"]
            
            if "status" in update_data:
                update_fields.append("status = :status")
                params["status"] = update_data["status"]
            
            if "priority" in update_data:
                update_fields.append("priority = :priority")
                params["priority"] = update_data["priority"]
            
            update_fields.append("updated = NOW()")
            
            update_query = f"""
            UPDATE tasks 
            SET {', '.join(update_fields)}
            WHERE id = :task_id
            """
            
            await session.execute(text(update_query), params)
        
        # Add state change if status changed
        if "status" in update_data:
            state_query = """
            INSERT INTO task_states (task_id, state, changed_by, notes)
            VALUES (:task_id, :state, :changed_by, :notes)
            """
            
            await session.execute(text(state_query), {
                "task_id": task_id,
                "state": "implementing" if update_data["status"] == "in_progress" else "planning",
                "changed_by": "dashboard",
                "notes": f"Status updated to {update_data['status']}"
            })
        
        await session.commit()
        
        return {
            "success": True,
            "message": "Task updated successfully"
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.get("/enhanced-tasks")
async def list_enhanced_tasks(
    state: Optional[str] = None,
    priority: Optional[int] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session)
):
    """List enhanced tasks with filtering"""
    
    try:
        where_clauses = []
        params = {"limit": limit}
        
        if state:
            where_clauses.append("ts.state = :state")
            params["state"] = state
        
        if priority:
            where_clauses.append("t.priority = :priority")
            params["priority"] = priority
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
        SELECT 
            t.id, t.task, t.status, t.priority, t.created, t.updated,
            ts.state as current_state,
            se.story_points, se.estimated_hours, se.estimated_cost,
            gi.branch_name, gi.merge_status
        FROM tasks t
        LEFT JOIN task_states ts ON t.id = ts.task_id AND ts.id = (
            SELECT id FROM task_states WHERE task_id = t.id ORDER BY changed_at DESC LIMIT 1
        )
        LEFT JOIN sprint_estimates se ON t.id = se.task_id
        LEFT JOIN git_integration gi ON t.id = gi.task_id
        {where_sql}
        ORDER BY t.priority ASC, t.created DESC
        LIMIT :limit
        """
        
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        
        tasks = []
        for row in rows:
            data = dict(row._mapping)
            tasks.append({
                "id": data["id"],
                "task": data["task"],
                "status": data["status"],
                "priority": data["priority"],
                "current_state": data["current_state"],
                "story_points": data["story_points"],
                "estimated_hours": float(data["estimated_hours"]) if data["estimated_hours"] else None,
                "estimated_cost": float(data["estimated_cost"]) if data["estimated_cost"] else None,
                "branch_name": data["branch_name"],
                "merge_status": data["merge_status"],
                "created": data["created"].isoformat() if data["created"] else "",
                "updated": data["updated"].isoformat() if data["updated"] else ""
            })
        
        return {
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list enhanced tasks: {str(e)}")