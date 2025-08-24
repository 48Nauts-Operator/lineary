# ABOUTME: Performance monitoring utilities for Betty's Executive Dashboard with <200ms targets
# ABOUTME: Provides decorators and tools for monitoring API performance and scalability requirements

import time
import asyncio
from functools import wraps
from typing import Dict, Any, Callable, Optional
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)

# Global performance metrics storage (would use Redis in production)
performance_metrics = {
    "api_calls": [],
    "response_times": {},
    "error_rates": {},
    "cache_hits": {},
    "concurrent_users": 0
}

def monitor_performance(target_ms: int = 1000):
    """
    Decorator to monitor API performance with target response time
    
    Args:
        target_ms: Target response time in milliseconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func.__name__
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Calculate performance metrics
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                # Log performance
                performance_data = {
                    "function": function_name,
                    "response_time_ms": round(response_time_ms, 2),
                    "target_ms": target_ms,
                    "target_met": response_time_ms <= target_ms,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Store metrics
                _store_performance_metrics(function_name, performance_data)
                
                # Log if target not met
                if response_time_ms > target_ms:
                    logger.warning(
                        "Performance target missed",
                        function=function_name,
                        response_time_ms=response_time_ms,
                        target_ms=target_ms,
                        overage_ms=response_time_ms - target_ms
                    )
                else:
                    logger.debug(
                        "Performance target met",
                        function=function_name,
                        response_time_ms=response_time_ms,
                        target_ms=target_ms
                    )
                
                # Add performance data to result if it's a dict
                if isinstance(result, dict) and "performance" not in result:
                    result["performance"] = {
                        "response_time_ms": round(response_time_ms, 2),
                        "target_met": response_time_ms <= target_ms
                    }
                
                return result
                
            except Exception as e:
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                # Log error with performance data
                logger.error(
                    "Function failed with performance data",
                    function=function_name,
                    error=str(e),
                    response_time_ms=response_time_ms,
                    target_ms=target_ms
                )
                
                # Store error metrics
                _store_error_metrics(function_name, str(e), response_time_ms)
                
                raise
                
        return wrapper
    return decorator

def cache_with_ttl(seconds: int = 300):
    """
    Decorator to cache function results with TTL
    
    Args:
        seconds: Cache TTL in seconds
    """
    cache_storage = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check if cached result exists and is valid
            if cache_key in cache_storage:
                cached_data = cache_storage[cache_key]
                cache_time = cached_data["timestamp"]
                if time.time() - cache_time < seconds:
                    # Cache hit
                    _record_cache_hit(func.__name__, True)
                    logger.debug("Cache hit", function=func.__name__, cache_key=cache_key)
                    
                    result = cached_data["result"]
                    # Add cache info to result if it's a dict
                    if isinstance(result, dict):
                        result["cached"] = True
                        result["cache_age_seconds"] = int(time.time() - cache_time)
                    
                    return result
            
            # Cache miss - execute function
            _record_cache_hit(func.__name__, False)
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_storage[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
            
            # Clean old cache entries periodically
            _cleanup_cache(cache_storage, seconds)
            
            logger.debug("Cache miss", function=func.__name__, cache_key=cache_key)
            
            return result
            
        return wrapper
    return decorator

class ConcurrentUserTracker:
    """Track concurrent users for scalability monitoring"""
    
    def __init__(self):
        self.active_sessions = set()
        self.max_concurrent = 0
        self.session_start_times = {}
    
    async def add_user_session(self, session_id: str) -> int:
        """Add a user session and return current concurrent count"""
        self.active_sessions.add(session_id)
        self.session_start_times[session_id] = time.time()
        
        current_count = len(self.active_sessions)
        if current_count > self.max_concurrent:
            self.max_concurrent = current_count
        
        # Update global metrics
        performance_metrics["concurrent_users"] = current_count
        
        logger.info(
            "User session added",
            session_id=session_id,
            concurrent_users=current_count,
            max_concurrent=self.max_concurrent
        )
        
        return current_count
    
    async def remove_user_session(self, session_id: str) -> int:
        """Remove a user session and return current concurrent count"""
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
            
            # Calculate session duration
            start_time = self.session_start_times.pop(session_id, time.time())
            session_duration = time.time() - start_time
            
            current_count = len(self.active_sessions)
            performance_metrics["concurrent_users"] = current_count
            
            logger.info(
                "User session removed",
                session_id=session_id,
                concurrent_users=current_count,
                session_duration_seconds=round(session_duration, 2)
            )
            
            return current_count
        
        return len(self.active_sessions)
    
    def get_concurrent_stats(self) -> Dict[str, Any]:
        """Get concurrent user statistics"""
        return {
            "current_concurrent": len(self.active_sessions),
            "max_concurrent": self.max_concurrent,
            "active_sessions": list(self.active_sessions),
            "target_capacity": 1000,  # Executive dashboard requirement
            "capacity_utilization": len(self.active_sessions) / 1000,
            "capacity_available": max(0, 1000 - len(self.active_sessions))
        }

class PerformanceAnalyzer:
    """Analyze performance metrics and provide recommendations"""
    
    @staticmethod
    def analyze_response_times(function_name: str) -> Dict[str, Any]:
        """Analyze response times for a specific function"""
        metrics = performance_metrics["response_times"].get(function_name, [])
        
        if not metrics:
            return {"status": "no_data", "function": function_name}
        
        response_times = [m["response_time_ms"] for m in metrics]
        target_times = [m["target_ms"] for m in metrics]
        
        analysis = {
            "function": function_name,
            "total_calls": len(metrics),
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "avg_target_ms": sum(target_times) / len(target_times),
            "target_met_percentage": (sum(1 for m in metrics if m["target_met"]) / len(metrics)) * 100,
            "performance_trend": _calculate_performance_trend(metrics),
            "recommendations": _generate_performance_recommendations(metrics)
        }
        
        return analysis
    
    @staticmethod
    def get_system_performance_summary() -> Dict[str, Any]:
        """Get overall system performance summary"""
        all_metrics = []
        for func_metrics in performance_metrics["response_times"].values():
            all_metrics.extend(func_metrics)
        
        if not all_metrics:
            return {"status": "no_data"}
        
        response_times = [m["response_time_ms"] for m in all_metrics]
        target_met_count = sum(1 for m in all_metrics if m["target_met"])
        
        return {
            "total_api_calls": len(all_metrics),
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "target_met_percentage": (target_met_count / len(all_metrics)) * 100,
            "concurrent_users": performance_metrics["concurrent_users"],
            "cache_hit_rates": _calculate_cache_hit_rates(),
            "error_rates": _calculate_error_rates(),
            "performance_grade": _calculate_performance_grade(all_metrics),
            "bottlenecks": _identify_bottlenecks(),
            "optimization_suggestions": _generate_system_optimization_suggestions()
        }
    
    @staticmethod
    def check_scalability_limits() -> Dict[str, Any]:
        """Check if system is approaching scalability limits"""
        current_concurrent = performance_metrics["concurrent_users"]
        target_capacity = 1000
        
        utilization = current_concurrent / target_capacity
        
        status = "green"
        if utilization > 0.9:
            status = "red"
        elif utilization > 0.7:
            status = "yellow"
        
        return {
            "current_concurrent_users": current_concurrent,
            "target_capacity": target_capacity,
            "utilization_percentage": utilization * 100,
            "status": status,
            "estimated_capacity_remaining": max(0, target_capacity - current_concurrent),
            "scale_up_recommended": utilization > 0.8,
            "estimated_breaking_point": target_capacity * 1.1  # 10% buffer
        }

# Global concurrent user tracker
concurrent_tracker = ConcurrentUserTracker()

# === PRIVATE HELPER FUNCTIONS === #

def _store_performance_metrics(function_name: str, performance_data: Dict[str, Any]):
    """Store performance metrics in memory (would use Redis in production)"""
    if function_name not in performance_metrics["response_times"]:
        performance_metrics["response_times"][function_name] = []
    
    performance_metrics["response_times"][function_name].append(performance_data)
    
    # Keep only last 1000 entries per function
    if len(performance_metrics["response_times"][function_name]) > 1000:
        performance_metrics["response_times"][function_name] = \
            performance_metrics["response_times"][function_name][-1000:]

def _store_error_metrics(function_name: str, error: str, response_time_ms: float):
    """Store error metrics"""
    if function_name not in performance_metrics["error_rates"]:
        performance_metrics["error_rates"][function_name] = []
    
    error_data = {
        "error": error,
        "response_time_ms": response_time_ms,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    performance_metrics["error_rates"][function_name].append(error_data)
    
    # Keep only last 500 error entries per function
    if len(performance_metrics["error_rates"][function_name]) > 500:
        performance_metrics["error_rates"][function_name] = \
            performance_metrics["error_rates"][function_name][-500:]

def _record_cache_hit(function_name: str, is_hit: bool):
    """Record cache hit/miss statistics"""
    if function_name not in performance_metrics["cache_hits"]:
        performance_metrics["cache_hits"][function_name] = {"hits": 0, "misses": 0}
    
    if is_hit:
        performance_metrics["cache_hits"][function_name]["hits"] += 1
    else:
        performance_metrics["cache_hits"][function_name]["misses"] += 1

def _cleanup_cache(cache_storage: Dict, ttl_seconds: int):
    """Clean up expired cache entries"""
    current_time = time.time()
    expired_keys = []
    
    for key, cached_data in cache_storage.items():
        if current_time - cached_data["timestamp"] > ttl_seconds:
            expired_keys.append(key)
    
    for key in expired_keys:
        del cache_storage[key]

def _calculate_performance_trend(metrics: list) -> str:
    """Calculate performance trend from metrics"""
    if len(metrics) < 10:
        return "insufficient_data"
    
    recent_metrics = metrics[-10:]  # Last 10 calls
    older_metrics = metrics[-20:-10] if len(metrics) >= 20 else metrics[:-10]
    
    if not older_metrics:
        return "insufficient_data"
    
    recent_avg = sum(m["response_time_ms"] for m in recent_metrics) / len(recent_metrics)
    older_avg = sum(m["response_time_ms"] for m in older_metrics) / len(older_metrics)
    
    if recent_avg < older_avg * 0.9:
        return "improving"
    elif recent_avg > older_avg * 1.1:
        return "degrading"
    else:
        return "stable"

def _generate_performance_recommendations(metrics: list) -> list[str]:
    """Generate performance recommendations based on metrics"""
    recommendations = []
    
    if not metrics:
        return recommendations
    
    response_times = [m["response_time_ms"] for m in metrics]
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    target_met_rate = sum(1 for m in metrics if m["target_met"]) / len(metrics)
    
    if target_met_rate < 0.9:
        recommendations.append("Performance targets are being missed frequently - consider optimization")
    
    if max_response_time > avg_response_time * 3:
        recommendations.append("High variability in response times detected - investigate outliers")
    
    if avg_response_time > 1000:
        recommendations.append("Average response time is high - consider caching or optimization")
    
    return recommendations

def _calculate_cache_hit_rates() -> Dict[str, float]:
    """Calculate cache hit rates for all functions"""
    hit_rates = {}
    
    for function_name, cache_data in performance_metrics["cache_hits"].items():
        total_requests = cache_data["hits"] + cache_data["misses"]
        if total_requests > 0:
            hit_rates[function_name] = cache_data["hits"] / total_requests
        else:
            hit_rates[function_name] = 0.0
    
    return hit_rates

def _calculate_error_rates() -> Dict[str, float]:
    """Calculate error rates for all functions"""
    error_rates = {}
    
    for function_name in performance_metrics["response_times"].keys():
        total_calls = len(performance_metrics["response_times"][function_name])
        error_count = len(performance_metrics["error_rates"].get(function_name, []))
        
        if total_calls > 0:
            error_rates[function_name] = error_count / total_calls
        else:
            error_rates[function_name] = 0.0
    
    return error_rates

def _calculate_performance_grade(all_metrics: list) -> str:
    """Calculate overall performance grade"""
    if not all_metrics:
        return "N/A"
    
    target_met_rate = sum(1 for m in all_metrics if m["target_met"]) / len(all_metrics)
    
    if target_met_rate >= 0.95:
        return "A"
    elif target_met_rate >= 0.9:
        return "B"
    elif target_met_rate >= 0.8:
        return "C"
    elif target_met_rate >= 0.7:
        return "D"
    else:
        return "F"

def _identify_bottlenecks() -> list[str]:
    """Identify performance bottlenecks"""
    bottlenecks = []
    
    for function_name, metrics in performance_metrics["response_times"].items():
        if not metrics:
            continue
        
        avg_response_time = sum(m["response_time_ms"] for m in metrics) / len(metrics)
        target_met_rate = sum(1 for m in metrics if m["target_met"]) / len(metrics)
        
        if avg_response_time > 1000 or target_met_rate < 0.8:
            bottlenecks.append(f"{function_name}: avg {avg_response_time:.1f}ms, {target_met_rate:.1%} target met")
    
    return bottlenecks

def _generate_system_optimization_suggestions() -> list[str]:
    """Generate system-wide optimization suggestions"""
    suggestions = []
    
    # Check cache hit rates
    cache_hit_rates = _calculate_cache_hit_rates()
    avg_cache_hit_rate = sum(cache_hit_rates.values()) / len(cache_hit_rates) if cache_hit_rates else 0
    
    if avg_cache_hit_rate < 0.7:
        suggestions.append("Improve caching strategy - current hit rate is low")
    
    # Check concurrent users
    if performance_metrics["concurrent_users"] > 800:
        suggestions.append("Consider scaling up - approaching concurrent user limit")
    
    # Check error rates
    error_rates = _calculate_error_rates()
    avg_error_rate = sum(error_rates.values()) / len(error_rates) if error_rates else 0
    
    if avg_error_rate > 0.05:
        suggestions.append("High error rate detected - investigate error causes")
    
    return suggestions