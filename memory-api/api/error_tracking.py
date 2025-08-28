# ABOUTME: Error tracking API endpoints for BETTY Memory System
# ABOUTME: Provides error monitoring, logging, and debugging information

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
import json
from collections import defaultdict

from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory error storage for development (replace with database in production)
error_logs: List[Dict[str, Any]] = []
MAX_ERROR_LOGS = 1000

def store_error(error_data: Dict[str, Any]):
    """Store error data in memory"""
    error_data['timestamp'] = datetime.now().isoformat()
    error_logs.append(error_data)
    
    # Keep only the most recent errors
    if len(error_logs) > MAX_ERROR_LOGS:
        error_logs.pop(0)

@router.post("/log")
async def log_error(
    error_data: Dict[str, Any]
):
    """Log a client-side error (no auth required for error logging)"""
    try:
        # Sanitize and validate error data
        sanitized_error = {
            'source': 'frontend',
            'user_id': 'anonymous',  # No auth required for error logging
            'error_type': error_data.get('error_type', 'unknown'),
            'message': str(error_data.get('message', ''))[:1000],  # Limit message length
            'url': str(error_data.get('url', ''))[:500],
            'method': error_data.get('method', 'unknown'),
            'status': error_data.get('status'),
            'user_agent': error_data.get('user_agent', ''),
            'timestamp': datetime.now().isoformat(),
            'additional_info': error_data.get('additional_info', {})
        }
        
        store_error(sanitized_error)
        
        logger.info(
            "Client error logged",
            error_type=sanitized_error['error_type'],
            url=sanitized_error['url'],
            user_id=sanitized_error['user_id']
        )
        
        return {
            "message": "Error logged successfully",
            "error_id": f"client-{len(error_logs)}"
        }
        
    except Exception as e:
        logger.error("Failed to log client error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to log error"
        )

@router.get("/logs")
async def get_error_logs(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    error_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    since_hours: Optional[int] = Query(None, le=168),  # Max 1 week
    current_user: dict = Depends(get_current_user)
):
    """Get error logs with filtering"""
    try:
        filtered_logs = error_logs.copy()
        
        # Apply filters
        if error_type:
            filtered_logs = [log for log in filtered_logs if log.get('error_type') == error_type]
        
        if source:
            filtered_logs = [log for log in filtered_logs if log.get('source') == source]
        
        if since_hours:
            cutoff_time = datetime.now() - timedelta(hours=since_hours)
            filtered_logs = [
                log for log in filtered_logs 
                if datetime.fromisoformat(log.get('timestamp', '2000-01-01')) >= cutoff_time
            ]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        total_count = len(filtered_logs)
        paginated_logs = filtered_logs[offset:offset + limit]
        
        return {
            "message": f"Retrieved {len(paginated_logs)} error logs",
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "logs": paginated_logs
        }
        
    except Exception as e:
        logger.error("Failed to retrieve error logs", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve error logs"
        )

@router.get("/summary")
async def get_error_summary(
    hours: int = Query(24, le=168),
    current_user: dict = Depends(get_current_user)
):
    """Get error summary statistics"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [
            log for log in error_logs 
            if datetime.fromisoformat(log.get('timestamp', '2000-01-01')) >= cutoff_time
        ]
        
        # Calculate statistics
        error_counts_by_type = defaultdict(int)
        error_counts_by_source = defaultdict(int)
        error_counts_by_hour = defaultdict(int)
        status_codes = defaultdict(int)
        
        for error in recent_errors:
            error_counts_by_type[error.get('error_type', 'unknown')] += 1
            error_counts_by_source[error.get('source', 'unknown')] += 1
            
            # Group by hour
            timestamp = datetime.fromisoformat(error.get('timestamp', '2000-01-01'))
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            error_counts_by_hour[hour_key] += 1
            
            # Status codes
            if error.get('status'):
                status_codes[str(error['status'])] += 1
        
        # Find most common errors
        most_common_errors = sorted(
            error_counts_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Calculate error rate per hour
        total_hours = max(1, hours)  # Avoid division by zero
        error_rate = len(recent_errors) / total_hours
        
        return {
            "message": f"Error summary for last {hours} hours",
            "summary": {
                "total_errors": len(recent_errors),
                "error_rate_per_hour": round(error_rate, 2),
                "most_common_errors": most_common_errors,
                "errors_by_source": dict(error_counts_by_source),
                "errors_by_hour": dict(error_counts_by_hour),
                "status_code_distribution": dict(status_codes),
                "time_range": {
                    "from": cutoff_time.isoformat(),
                    "to": datetime.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error("Failed to generate error summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate error summary"
        )

@router.delete("/logs")
async def clear_error_logs(
    confirm: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """Clear all error logs (development only)"""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear logs"
        )
    
    try:
        cleared_count = len(error_logs)
        error_logs.clear()
        
        logger.info("Error logs cleared", count=cleared_count, user_id=current_user.get('user_id'))
        
        return {
            "message": f"Cleared {cleared_count} error logs",
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error("Failed to clear error logs", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to clear error logs"
        )

@router.get("/health-check")
async def error_tracking_health():
    """Health check for error tracking system"""
    return {
        "status": "healthy",
        "error_logs_count": len(error_logs),
        "max_capacity": MAX_ERROR_LOGS,
        "usage_percentage": round((len(error_logs) / MAX_ERROR_LOGS) * 100, 2),
        "timestamp": datetime.now().isoformat()
    }