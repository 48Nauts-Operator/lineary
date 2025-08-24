# ABOUTME: API versioning and routing management for BETTY Memory System v2
# ABOUTME: Handles version routing, backward compatibility, and API evolution

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from core.security import get_current_user
from core.dependencies import DatabaseDependencies, get_all_databases

logger = structlog.get_logger(__name__)

# API version metadata
API_V2_METADATA = {
    "version": "2.0.0",
    "release_date": "2024-08-08",
    "status": "stable",
    "deprecated": False,
    "sunset_date": None,
    "changelog_url": "/docs/v2/changelog",
    "migration_guide_url": "/docs/v2/migration",
    "features": [
        "Advanced Query APIs",
        "Batch Operations", 
        "Cross-Project Intelligence",
        "Enhanced Performance",
        "Real-time Progress Tracking"
    ],
    "breaking_changes": [
        "New authentication requirements for advanced features",
        "Enhanced permission model for cross-project operations",
        "Updated response formats for consistency"
    ],
    "backward_compatibility": {
        "v1_supported": True,
        "v1_sunset_date": "2025-12-31",
        "migration_required": False,
        "auto_upgrade_available": True
    }
}

# Version compatibility matrix
VERSION_COMPATIBILITY = {
    "1.0": {
        "supported": True,
        "deprecated": False,
        "sunset_date": "2025-12-31",
        "compatibility_level": "full"
    },
    "1.1": {
        "supported": True,
        "deprecated": False,
        "sunset_date": "2025-12-31", 
        "compatibility_level": "full"
    },
    "2.0": {
        "supported": True,
        "deprecated": False,
        "sunset_date": None,
        "compatibility_level": "native"
    }
}

class APIVersionManager:
    """Manages API versioning and compatibility"""
    
    def __init__(self):
        self.current_version = "2.0"
        self.supported_versions = list(VERSION_COMPATIBILITY.keys())
        self.default_version = "2.0"
    
    def get_version_from_request(self, request: Request) -> str:
        """Extract API version from request headers or path"""
        # Check version in header
        version = request.headers.get("API-Version")
        if version and self.is_supported_version(version):
            return version
        
        # Check version in Accept header
        accept_header = request.headers.get("Accept", "")
        if "application/vnd.betty.v" in accept_header:
            try:
                version = accept_header.split("application/vnd.betty.v")[1].split("+")[0]
                if self.is_supported_version(version):
                    return version
            except (IndexError, ValueError):
                pass
        
        # Check version in path (handled by router)
        path = str(request.url.path)
        if "/v2/" in path:
            return "2.0"
        elif "/v1/" in path:
            return "1.0"
        
        # Default to current version
        return self.default_version
    
    def is_supported_version(self, version: str) -> bool:
        """Check if version is supported"""
        return version in self.supported_versions
    
    def get_version_info(self, version: str) -> Dict[str, Any]:
        """Get detailed information about a specific version"""
        if not self.is_supported_version(version):
            raise ValueError(f"Unsupported version: {version}")
        
        base_info = VERSION_COMPATIBILITY[version].copy()
        
        if version == "2.0":
            base_info.update(API_V2_METADATA)
        
        return base_info
    
    def check_feature_availability(self, version: str, feature: str) -> bool:
        """Check if a feature is available in the specified version"""
        version_features = {
            "1.0": [
                "basic_knowledge_management",
                "simple_search", 
                "session_management",
                "basic_analytics"
            ],
            "1.1": [
                "basic_knowledge_management",
                "simple_search",
                "session_management", 
                "basic_analytics",
                "improved_search",
                "graphiti_integration"
            ],
            "2.0": [
                "basic_knowledge_management",
                "simple_search",
                "session_management",
                "basic_analytics", 
                "improved_search",
                "graphiti_integration",
                "advanced_query_apis",
                "batch_operations",
                "cross_project_intelligence",
                "enhanced_performance",
                "progress_tracking",
                "semantic_clustering",
                "pattern_matching",
                "collaborative_filtering"
            ]
        }
        
        return feature in version_features.get(version, [])

# Global version manager instance
version_manager = APIVersionManager()

# Version middleware
async def version_middleware(request: Request, call_next):
    """Middleware to handle API versioning"""
    try:
        # Get version from request
        api_version = version_manager.get_version_from_request(request)
        
        # Check if version is supported
        if not version_manager.is_supported_version(api_version):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Unsupported API Version",
                    "message": f"API version {api_version} is not supported",
                    "supported_versions": version_manager.supported_versions,
                    "current_version": version_manager.current_version
                }
            )
        
        # Add version info to request state
        request.state.api_version = api_version
        request.state.version_info = version_manager.get_version_info(api_version)
        
        # Process request
        response = await call_next(request)
        
        # Add version headers to response
        response.headers["API-Version"] = api_version
        response.headers["API-Version-Supported"] = ",".join(version_manager.supported_versions)
        response.headers["API-Version-Current"] = version_manager.current_version
        
        # Add deprecation warnings if needed
        version_info = version_manager.get_version_info(api_version)
        if version_info.get("deprecated"):
            response.headers["Deprecation"] = "true"
            if version_info.get("sunset_date"):
                response.headers["Sunset"] = version_info["sunset_date"]
        
        return response
        
    except Exception as e:
        logger.error("Version middleware error", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Version Processing Error",
                "message": "Failed to process API version"
            }
        )

# Versioning router
versioning_router = APIRouter(prefix="/version", tags=["API Versioning"])

@versioning_router.get("/info")
async def get_api_version_info(
    request: Request,
    version: Optional[str] = None
) -> Dict[str, Any]:
    """Get API version information"""
    try:
        target_version = version or getattr(request.state, 'api_version', version_manager.current_version)
        
        if not version_manager.is_supported_version(target_version):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported version: {target_version}"
            )
        
        version_info = version_manager.get_version_info(target_version)
        
        return {
            "api_version": target_version,
            "version_info": version_info,
            "server_time": datetime.utcnow().isoformat(),
            "supported_versions": version_manager.supported_versions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get version info", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve version information"
        )

@versioning_router.get("/compatibility/{source_version}/{target_version}")
async def check_version_compatibility(
    source_version: str,
    target_version: str
) -> Dict[str, Any]:
    """Check compatibility between API versions"""
    try:
        if not version_manager.is_supported_version(source_version):
            raise HTTPException(
                status_code=400,
                detail=f"Source version {source_version} is not supported"
            )
        
        if not version_manager.is_supported_version(target_version):
            raise HTTPException(
                status_code=400,
                detail=f"Target version {target_version} is not supported"
            )
        
        source_info = version_manager.get_version_info(source_version)
        target_info = version_manager.get_version_info(target_version)
        
        # Determine compatibility level
        compatibility_level = "unknown"
        migration_required = True
        breaking_changes = []
        
        if source_version == target_version:
            compatibility_level = "identical"
            migration_required = False
        elif source_version < target_version:
            compatibility_level = "forward_compatible"
            migration_required = False
            if target_version == "2.0" and source_version.startswith("1."):
                breaking_changes = API_V2_METADATA.get("breaking_changes", [])
        else:
            compatibility_level = "backward_compatible"
            migration_required = True
        
        return {
            "source_version": source_version,
            "target_version": target_version,
            "compatibility_level": compatibility_level,
            "migration_required": migration_required,
            "breaking_changes": breaking_changes,
            "source_info": source_info,
            "target_info": target_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to check compatibility", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to check version compatibility"
        )

@versioning_router.get("/features")
async def list_version_features(
    request: Request,
    version: Optional[str] = None
) -> Dict[str, Any]:
    """List features available in a specific API version"""
    try:
        target_version = version or getattr(request.state, 'api_version', version_manager.current_version)
        
        if not version_manager.is_supported_version(target_version):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported version: {target_version}"
            )
        
        # Get version-specific features
        all_features = [
            "basic_knowledge_management",
            "simple_search",
            "session_management",
            "basic_analytics",
            "improved_search", 
            "graphiti_integration",
            "advanced_query_apis",
            "batch_operations",
            "cross_project_intelligence",
            "enhanced_performance",
            "progress_tracking",
            "semantic_clustering",
            "pattern_matching",
            "collaborative_filtering"
        ]
        
        available_features = [
            {
                "name": feature,
                "available": version_manager.check_feature_availability(target_version, feature),
                "since_version": "1.0"  # Would be determined based on feature history
            }
            for feature in all_features
        ]
        
        return {
            "api_version": target_version,
            "features": available_features,
            "feature_count": len([f for f in available_features if f["available"]])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list features", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to list version features"
        )

@versioning_router.post("/migrate")
async def create_migration_plan(
    source_version: str,
    target_version: str,
    current_user: dict = Depends(get_current_user),
    databases: DatabaseDependencies = Depends(get_all_databases)
) -> Dict[str, Any]:
    """Create a migration plan between API versions"""
    try:
        if not version_manager.is_supported_version(source_version):
            raise HTTPException(
                status_code=400,
                detail=f"Source version {source_version} is not supported"
            )
        
        if not version_manager.is_supported_version(target_version):
            raise HTTPException(
                status_code=400,
                detail=f"Target version {target_version} is not supported"
            )
        
        # Generate migration plan
        migration_plan = {
            "migration_id": f"migration_{source_version}_to_{target_version}_{int(datetime.utcnow().timestamp())}",
            "source_version": source_version,
            "target_version": target_version,
            "migration_type": "api_version_upgrade",
            "estimated_duration": "5-10 minutes",
            "risk_level": "low",
            "rollback_supported": True,
            "steps": [
                {
                    "step": 1,
                    "title": "Backup current configuration",
                    "description": "Create backup of current API settings and data",
                    "estimated_duration": "1-2 minutes"
                },
                {
                    "step": 2, 
                    "title": "Update API endpoints",
                    "description": "Update client code to use new API version endpoints",
                    "estimated_duration": "2-3 minutes"
                },
                {
                    "step": 3,
                    "title": "Test compatibility",
                    "description": "Run compatibility tests with new API version",
                    "estimated_duration": "1-2 minutes"
                },
                {
                    "step": 4,
                    "title": "Update authentication",
                    "description": "Update authentication headers and permissions",
                    "estimated_duration": "1-2 minutes"
                }
            ],
            "prerequisites": [
                "Valid API authentication",
                "Read/write permissions to knowledge base",
                "Network connectivity to API endpoints"
            ],
            "breaking_changes": API_V2_METADATA.get("breaking_changes", []) if target_version == "2.0" else [],
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("user_id")
        }
        
        return {
            "message": "Migration plan created successfully",
            "migration_plan": migration_plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create migration plan", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to create migration plan"
        )

# Dependency to check feature availability
def require_feature(feature_name: str):
    """Dependency to check if a feature is available in the current API version"""
    def check_feature(request: Request):
        api_version = getattr(request.state, 'api_version', version_manager.current_version)
        
        if not version_manager.check_feature_availability(api_version, feature_name):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Feature Not Available",
                    "message": f"Feature '{feature_name}' is not available in API version {api_version}",
                    "current_version": api_version,
                    "required_version": "2.0",
                    "upgrade_url": "/version/migrate"
                }
            )
        
        return True
    
    return check_feature

# Version-specific response wrapper
async def version_aware_response(data: Any, request: Request) -> JSONResponse:
    """Wrap response with version-specific formatting"""
    api_version = getattr(request.state, 'api_version', version_manager.current_version)
    
    response_data = {
        "api_version": api_version,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add version-specific metadata for v2
    if api_version.startswith("2."):
        response_data["metadata"] = {
            "version_info": getattr(request.state, 'version_info', {}),
            "server_version": version_manager.current_version,
            "compatibility_level": "native" if api_version == version_manager.current_version else "compatible"
        }
    
    return JSONResponse(content=response_data)