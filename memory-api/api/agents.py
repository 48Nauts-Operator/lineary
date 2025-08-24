# ABOUTME: FastAPI routes for BETTY Multi-Agent Platform with Context-Aware Routing
# ABOUTME: Provides REST API endpoints for agent registration, intelligent routing, and operations

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import structlog
import json
import asyncio
from pydantic import BaseModel, Field

from ..services.agent_service import AgentService, AgentRegistration, AgentConfig
from ..services.agent_manager import AgentManager
from ..providers.base_provider import ChatRequest, Message
from ..core.dependencies import get_databases, DatabaseDependencies

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/register", response_model=Dict[str, Any])
async def register_agent(
    registration: AgentRegistration,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Register a new agent in the system"""
    try:
        agent_service = AgentService(databases)
        await agent_service.initialize()
        
        result = await agent_service.register_agent(registration)
        
        logger.info("Agent registration requested", 
                   agent_name=registration.name,
                   provider=registration.provider)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Agent registration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """List all registered agents with optional filtering"""
    try:
        agent_service = AgentService(databases)
        await agent_service.initialize()
        
        agents = await agent_service.get_agents(status=status)
        
        # Filter by provider if specified
        if provider:
            agents = [agent for agent in agents if agent['provider'] == provider]
        
        return agents
        
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/capabilities", response_model=List[Dict[str, Any]])
async def list_capabilities(
    databases: DatabaseDependencies = Depends(get_databases)
):
    """List all available capabilities across agents"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        capabilities = await agent_manager.get_all_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error("Failed to list capabilities", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def agents_health():
    """Health check endpoint for the agent system"""
    return {
        "status": "healthy",
        "service": "BETTY Multi-Agent Platform",
        "version": "1.0.0",
        "context_aware_routing": "available",  # Ready for full deployment
        "timestamp": datetime.utcnow()
    }

# Additional endpoints will be added as Context-Aware Routing is fully tested