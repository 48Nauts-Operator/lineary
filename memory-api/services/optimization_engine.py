# ABOUTME: Performance Optimization Engine for Betty's Knowledge Analytics
# ABOUTME: Resource optimization, process improvement, and performance enhancement recommendations

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
import structlog
from collections import defaultdict, Counter
from dataclasses import dataclass
import psutil
import gc
import sys

from core.dependencies import DatabaseDependencies
from models.advanced_analytics import (
    OptimizationRecommendation, TimeSeriesPoint, 
    AnalyticsTimeRange, PredictionResult
)

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization analysis"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    query_response_time: float
    cache_hit_rate: float
    error_rate: float
    throughput: float
    concurrent_users: int
    timestamp: datetime


@dataclass
class OptimizationTarget:
    """Optimization target with current and desired values"""
    metric_name: str
    current_value: float
    target_value: float
    priority: str  # high, medium, low
    impact_estimate: float  # Expected improvement percentage


class PerformanceOptimizationEngine:
    """
    Comprehensive Performance Optimization Engine providing intelligent
    recommendations for resource allocation, process improvements, and performance tuning
    """
    
    def __init__(self, databases: DatabaseDependencies):
        self.databases = databases
        self.postgres = databases.postgres
        self.redis = databases.redis
        
        # Performance monitoring
        self._performance_history = []
        self._optimization_cache = {}
        self._baseline_metrics = None
        
        # Optimization thresholds
        self.performance_thresholds = {
            "cpu_usage_warning": 80.0,      # CPU usage > 80%
            "memory_usage_warning": 85.0,    # Memory usage > 85%
            "response_time_warning": 500.0,  # Response time > 500ms
            "cache_hit_rate_target": 90.0,   # Cache hit rate target
            "error_rate_threshold": 1.0,     # Error rate > 1%
            "disk_usage_warning": 90.0       # Disk usage > 90%
        }
        
        # Optimization strategies
        self.optimization_strategies = {
            "performance": ["caching", "indexing", "query_optimization", "connection_pooling"],
            "resource": ["memory_tuning", "cpu_scaling", "disk_cleanup", "load_balancing"],
            "process": ["workflow_optimization", "automation", "batch_processing", "parallel_execution"],
            "knowledge": ["content_deduplication", "quality_filtering", "smart_archiving", "semantic_indexing"]
        }
        
        # ROI calculation factors
        self.roi_factors = {
            "performance_improvement": 0.3,
            "resource_savings": 0.4,
            "operational_efficiency": 0.2,
            "user_experience": 0.1
        }
    
    async def analyze_system_performance(
        self, 
        time_range: AnalyticsTimeRange = AnalyticsTimeRange.DAY
    ) -> Dict[str, Any]:
        """
        Analyze current system performance and identify optimization opportunities
        
        Args:
            time_range: Time range for performance analysis
            
        Returns:
            Comprehensive performance analysis with optimization recommendations
        """
        logger.info("Analyzing system performance", time_range=time_range)
        
        try:
            # Collect current performance metrics
            current_metrics = await self._collect_performance_metrics()
            
            # Get historical performance data
            historical_metrics = await self._get_historical_performance_data(time_range)
            
            # Analyze performance trends
            performance_trends = self._analyze_performance_trends(historical_metrics)
            
            # Identify performance bottlenecks
            bottlenecks = await self._identify_performance_bottlenecks(current_metrics, historical_metrics)
            
            # Generate optimization recommendations
            optimizations = await self._generate_performance_optimizations(
                current_metrics, bottlenecks, performance_trends
            )
            
            # Calculate system health score
            health_score = self._calculate_system_health_score(current_metrics)
            
            # Predict future performance issues
            performance_predictions = await self._predict_performance_issues(historical_metrics)
            
            analysis_result = {
                "performance_overview": {
                    "system_health_score": health_score,
                    "overall_status": self._get_health_status(health_score),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "time_range_analyzed": time_range.value
                },
                "current_metrics": {
                    "cpu_usage_percent": current_metrics.cpu_usage,
                    "memory_usage_percent": current_metrics.memory_usage,
                    "disk_usage_percent": current_metrics.disk_usage,
                    "avg_response_time_ms": current_metrics.query_response_time,
                    "cache_hit_rate_percent": current_metrics.cache_hit_rate,
                    "error_rate_percent": current_metrics.error_rate,
                    "throughput_per_second": current_metrics.throughput,
                    "concurrent_users": current_metrics.concurrent_users
                },
                "performance_trends": performance_trends,
                "identified_bottlenecks": bottlenecks,
                "optimization_recommendations": [opt.dict() for opt in optimizations],
                "performance_predictions": performance_predictions,
                "priority_actions": self._get_priority_actions(optimizations),
                "estimated_improvements": self._calculate_total_improvement_potential(optimizations)
            }
            
            # Cache analysis results
            cache_key = f"performance_analysis_{time_range.value}"
            self._optimization_cache[cache_key] = analysis_result
            
            logger.info("Performance analysis completed", 
                       health_score=health_score,
                       bottlenecks=len(bottlenecks),
                       recommendations=len(optimizations))
            
            return analysis_result
            
        except Exception as e:
            logger.error("Performance analysis failed", error=str(e))
            raise
    
    async def optimize_query_performance(
        self, 
        query_patterns: List[Dict[str, Any]]
    ) -> List[OptimizationRecommendation]:
        """
        Analyze query patterns and provide optimization recommendations
        
        Args:
            query_patterns: List of query execution patterns and performance data
            
        Returns:
            Query-specific optimization recommendations
        """
        logger.info("Optimizing query performance", queries=len(query_patterns))
        
        try:
            optimizations = []
            
            for query_pattern in query_patterns:
                query_analysis = await self._analyze_query_pattern(query_pattern)
                query_optimizations = self._generate_query_optimizations(query_analysis)
                optimizations.extend(query_optimizations)
            
            # Prioritize optimizations by impact
            optimizations.sort(key=lambda x: x.estimated_roi or 0, reverse=True)
            
            logger.info("Query optimization completed", 
                       total_recommendations=len(optimizations))
            
            return optimizations
            
        except Exception as e:
            logger.error("Query optimization failed", error=str(e))
            return []
    
    async def optimize_resource_allocation(
        self, 
        resource_usage_data: Dict[str, List[float]],
        allocation_constraints: Dict[str, float]
    ) -> List[OptimizationRecommendation]:
        """
        Optimize resource allocation based on usage patterns and constraints
        
        Args:
            resource_usage_data: Historical resource usage data
            allocation_constraints: Resource allocation constraints and limits
            
        Returns:
            Resource allocation optimization recommendations
        """
        logger.info("Optimizing resource allocation", 
                   resources=len(resource_usage_data))
        
        try:
            optimizations = []
            
            # Analyze each resource type
            for resource_type, usage_data in resource_usage_data.items():
                if not usage_data:
                    continue
                
                # Calculate usage statistics
                avg_usage = np.mean(usage_data)
                max_usage = np.max(usage_data)
                usage_variance = np.var(usage_data)
                
                # Get constraint for this resource
                constraint = allocation_constraints.get(resource_type, 100.0)
                
                # Generate optimization based on usage patterns
                if max_usage > constraint * 0.9:  # Near capacity
                    optimization = OptimizationRecommendation(
                        optimization_type="resource",
                        title=f"Scale {resource_type.title()} Resources",
                        description=f"{resource_type.title()} usage reaches {max_usage:.1f}% of capacity. Consider scaling up to prevent performance degradation.",
                        current_state_metrics={
                            f"{resource_type}_avg_usage": avg_usage,
                            f"{resource_type}_max_usage": max_usage,
                            f"{resource_type}_capacity": constraint
                        },
                        predicted_improvement={
                            "performance_improvement": 25.0,
                            "stability_improvement": 40.0,
                            "user_experience_improvement": 30.0
                        },
                        implementation_effort="medium",
                        estimated_roi=30.0,
                        risk_assessment="low",
                        prerequisites=[f"Budget approval for {resource_type} scaling"],
                        implementation_steps=[
                            f"Analyze current {resource_type} bottlenecks",
                            f"Plan {resource_type} scaling strategy",
                            f"Implement {resource_type} scaling",
                            "Monitor performance improvements"
                        ],
                        success_metrics=[
                            f"{resource_type}_utilization < 80%",
                            "Improved response times",
                            "Reduced error rates"
                        ],
                        timeline_estimate="2-4 weeks",
                        confidence_score=0.85
                    )
                    optimizations.append(optimization)
                
                elif avg_usage < constraint * 0.3:  # Underutilized
                    potential_savings = (constraint - avg_usage) * 0.8  # 80% of unused capacity
                    
                    optimization = OptimizationRecommendation(
                        optimization_type="resource",
                        title=f"Optimize {resource_type.title()} Allocation",
                        description=f"{resource_type.title()} is underutilized (avg {avg_usage:.1f}% vs {constraint:.1f}% allocated). Consider rightsizing for cost savings.",
                        current_state_metrics={
                            f"{resource_type}_avg_usage": avg_usage,
                            f"{resource_type}_allocated": constraint,
                            f"{resource_type}_waste_percentage": ((constraint - avg_usage) / constraint) * 100
                        },
                        predicted_improvement={
                            "cost_reduction": potential_savings,
                            "efficiency_improvement": 20.0
                        },
                        implementation_effort="low",
                        estimated_roi=potential_savings * 2,  # ROI based on cost savings
                        risk_assessment="low",
                        prerequisites=["Performance monitoring during transition"],
                        implementation_steps=[
                            f"Analyze {resource_type} usage patterns",
                            f"Test reduced {resource_type} allocation",
                            f"Gradually reduce {resource_type} allocation",
                            "Monitor for performance impact"
                        ],
                        success_metrics=[
                            "Maintained performance levels",
                            f"Reduced {resource_type} costs",
                            f"Improved {resource_type} efficiency"
                        ],
                        timeline_estimate="1-2 weeks",
                        confidence_score=0.9
                    )
                    optimizations.append(optimization)
                
                # Check for high variance (inconsistent usage)
                if usage_variance > (avg_usage * 0.5) ** 2:  # High variance relative to mean
                    optimization = OptimizationRecommendation(
                        optimization_type="process",
                        title=f"Stabilize {resource_type.title()} Usage Patterns",
                        description=f"{resource_type.title()} shows high usage variance. Implement load balancing or workload smoothing.",
                        current_state_metrics={
                            f"{resource_type}_usage_variance": usage_variance,
                            f"{resource_type}_coefficient_variation": np.sqrt(usage_variance) / avg_usage
                        },
                        predicted_improvement={
                            "stability_improvement": 35.0,
                            "predictability_improvement": 50.0
                        },
                        implementation_effort="medium",
                        estimated_roi=25.0,
                        risk_assessment="medium",
                        prerequisites=["Workload analysis", "Load balancing infrastructure"],
                        implementation_steps=[
                            f"Analyze {resource_type} usage spikes",
                            "Implement workload smoothing",
                            "Set up load balancing",
                            "Monitor usage stabilization"
                        ],
                        success_metrics=[
                            f"Reduced {resource_type} usage variance",
                            "More predictable performance",
                            "Better resource utilization"
                        ],
                        timeline_estimate="3-6 weeks",
                        confidence_score=0.75
                    )
                    optimizations.append(optimization)
            
            logger.info("Resource allocation optimization completed", 
                       recommendations=len(optimizations))
            
            return optimizations
            
        except Exception as e:
            logger.error("Resource allocation optimization failed", error=str(e))
            return []
    
    async def optimize_knowledge_processes(
        self, 
        knowledge_metrics: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """
        Optimize knowledge management processes and workflows
        
        Args:
            knowledge_metrics: Knowledge system performance metrics
            
        Returns:
            Knowledge process optimization recommendations
        """
        logger.info("Optimizing knowledge processes")
        
        try:
            optimizations = []
            
            # Knowledge quality optimization
            if knowledge_metrics.get("avg_quality_score", 0) < 0.7:
                optimization = OptimizationRecommendation(
                    optimization_type="knowledge",
                    title="Improve Knowledge Quality Standards",
                    description="Average knowledge quality is below optimal levels. Implement quality improvement processes.",
                    current_state_metrics={
                        "avg_quality_score": knowledge_metrics.get("avg_quality_score", 0),
                        "low_quality_items": knowledge_metrics.get("low_quality_count", 0)
                    },
                    predicted_improvement={
                        "knowledge_effectiveness": 40.0,
                        "user_satisfaction": 35.0,
                        "decision_quality": 25.0
                    },
                    implementation_effort="medium",
                    estimated_roi=45.0,
                    risk_assessment="low",
                    prerequisites=["Quality scoring system", "Review processes"],
                    implementation_steps=[
                        "Establish quality standards",
                        "Implement automated quality scoring",
                        "Set up review workflows",
                        "Train content creators"
                    ],
                    success_metrics=[
                        "Average quality score > 0.8",
                        "Reduced low-quality content",
                        "Improved user ratings"
                    ],
                    timeline_estimate="4-8 weeks",
                    confidence_score=0.8
                )
                optimizations.append(optimization)
            
            # Knowledge utilization optimization
            utilization_rate = knowledge_metrics.get("utilization_rate", 0)
            if utilization_rate < 0.6:
                optimization = OptimizationRecommendation(
                    optimization_type="knowledge",
                    title="Increase Knowledge Utilization",
                    description=f"Knowledge utilization rate is {utilization_rate*100:.1f}%. Improve discoverability and accessibility.",
                    current_state_metrics={
                        "utilization_rate": utilization_rate,
                        "unused_knowledge_items": knowledge_metrics.get("unused_items", 0)
                    },
                    predicted_improvement={
                        "knowledge_roi": 60.0,
                        "decision_speed": 30.0,
                        "operational_efficiency": 25.0
                    },
                    implementation_effort="medium",
                    estimated_roi=50.0,
                    risk_assessment="low",
                    prerequisites=["Search improvements", "User training"],
                    implementation_steps=[
                        "Improve search functionality",
                        "Implement knowledge recommendations",
                        "Create usage dashboards",
                        "Conduct user training sessions"
                    ],
                    success_metrics=[
                        "Utilization rate > 80%",
                        "Increased search queries",
                        "Higher user engagement"
                    ],
                    timeline_estimate="6-10 weeks",
                    confidence_score=0.85
                )
                optimizations.append(optimization)
            
            # Knowledge redundancy optimization
            if knowledge_metrics.get("duplication_rate", 0) > 0.15:
                optimization = OptimizationRecommendation(
                    optimization_type="knowledge",
                    title="Reduce Knowledge Duplication",
                    description="High knowledge duplication detected. Implement deduplication and consolidation processes.",
                    current_state_metrics={
                        "duplication_rate": knowledge_metrics.get("duplication_rate", 0),
                        "duplicate_items": knowledge_metrics.get("duplicate_count", 0)
                    },
                    predicted_improvement={
                        "storage_efficiency": 30.0,
                        "maintenance_reduction": 40.0,
                        "content_clarity": 25.0
                    },
                    implementation_effort="high",
                    estimated_roi=35.0,
                    risk_assessment="medium",
                    prerequisites=["Deduplication algorithms", "Content review process"],
                    implementation_steps=[
                        "Implement similarity detection",
                        "Review duplicate content",
                        "Consolidate related items",
                        "Prevent future duplication"
                    ],
                    success_metrics=[
                        "Duplication rate < 5%",
                        "Reduced storage usage",
                        "Improved content coherence"
                    ],
                    timeline_estimate="8-12 weeks",
                    confidence_score=0.7
                )
                optimizations.append(optimization)
            
            return optimizations
            
        except Exception as e:
            logger.error("Knowledge process optimization failed", error=str(e))
            return []
    
    async def generate_capacity_planning_recommendations(
        self, 
        growth_projections: Dict[str, float],
        current_capacity: Dict[str, float]
    ) -> List[OptimizationRecommendation]:
        """
        Generate capacity planning recommendations based on growth projections
        
        Args:
            growth_projections: Expected growth rates for different metrics
            current_capacity: Current system capacity limits
            
        Returns:
            Capacity planning recommendations
        """
        logger.info("Generating capacity planning recommendations")
        
        try:
            recommendations = []
            
            for metric, growth_rate in growth_projections.items():
                current_cap = current_capacity.get(metric, 100.0)
                
                # Calculate future capacity needs (6 months projection)
                future_needs = current_cap * (1 + growth_rate * 6)  # 6 months
                capacity_gap = future_needs - current_cap
                
                if capacity_gap > current_cap * 0.2:  # More than 20% additional capacity needed
                    recommendation = OptimizationRecommendation(
                        optimization_type="resource",
                        title=f"Plan {metric.title()} Capacity Expansion",
                        description=f"Projected {growth_rate*100:+.1f}% monthly growth in {metric} requires {capacity_gap:.0f} additional capacity units within 6 months.",
                        current_state_metrics={
                            f"current_{metric}_capacity": current_cap,
                            f"projected_{metric}_needs": future_needs,
                            f"{metric}_growth_rate": growth_rate
                        },
                        predicted_improvement={
                            "capacity_adequacy": 100.0,
                            "service_reliability": 40.0,
                            "user_experience": 30.0
                        },
                        implementation_effort="high",
                        estimated_roi=abs(growth_rate) * 100,  # Higher ROI for faster growth
                        risk_assessment="medium",
                        prerequisites=[f"Budget for {metric} expansion", "Infrastructure planning"],
                        implementation_steps=[
                            f"Detailed {metric} capacity analysis",
                            f"Design {metric} expansion plan",
                            f"Procure {metric} resources",
                            f"Implement {metric} expansion",
                            "Monitor capacity utilization"
                        ],
                        success_metrics=[
                            f"Adequate {metric} capacity for projected growth",
                            "No capacity-related outages",
                            "Maintained performance during growth"
                        ],
                        timeline_estimate="8-16 weeks",
                        confidence_score=0.8
                    )
                    recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error("Capacity planning failed", error=str(e))
            return []
    
    # Helper Methods
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            # Network I/O (simplified)
            net_io = psutil.net_io_counters()
            network_io = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # MB
            
            # Mock application-specific metrics (would be collected from actual monitoring)
            query_response_time = 85.0  # ms
            cache_hit_rate = 87.5       # %
            error_rate = 0.2           # %
            throughput = 15.5          # requests/second
            concurrent_users = 8
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                query_response_time=query_response_time,
                cache_hit_rate=cache_hit_rate,
                error_rate=error_rate,
                throughput=throughput,
                concurrent_users=concurrent_users,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Performance metrics collection failed", error=str(e))
            # Return default metrics
            return PerformanceMetrics(
                cpu_usage=50.0, memory_usage=60.0, disk_usage=40.0, network_io=10.0,
                query_response_time=100.0, cache_hit_rate=80.0, error_rate=0.5,
                throughput=10.0, concurrent_users=5, timestamp=datetime.utcnow()
            )
    
    async def _get_historical_performance_data(
        self, 
        time_range: AnalyticsTimeRange
    ) -> List[PerformanceMetrics]:
        """Get historical performance data for analysis"""
        # Mock implementation - would query actual performance database
        historical_data = []
        
        days = {"1d": 1, "7d": 7, "30d": 30}[time_range.value] if time_range.value in ["1d", "7d", "30d"] else 7
        hours = days * 24
        
        for i in range(hours):
            timestamp = datetime.utcnow() - timedelta(hours=hours-i)
            
            # Generate realistic performance patterns
            base_cpu = 45 + 15 * np.sin(i * 2 * np.pi / 24)  # Daily cycle
            base_memory = 60 + 10 * np.sin(i * 2 * np.pi / (24 * 7))  # Weekly cycle
            
            metrics = PerformanceMetrics(
                cpu_usage=max(10, min(95, base_cpu + np.random.normal(0, 5))),
                memory_usage=max(30, min(90, base_memory + np.random.normal(0, 3))),
                disk_usage=40 + np.random.normal(0, 2),
                network_io=5 + np.random.exponential(2),
                query_response_time=80 + np.random.gamma(2, 10),
                cache_hit_rate=85 + np.random.normal(0, 5),
                error_rate=max(0, np.random.exponential(0.3)),
                throughput=12 + np.random.normal(0, 3),
                concurrent_users=int(5 + np.random.poisson(2)),
                timestamp=timestamp
            )
            historical_data.append(metrics)
        
        return historical_data
    
    def _analyze_performance_trends(
        self, 
        historical_metrics: List[PerformanceMetrics]
    ) -> Dict[str, Any]:
        """Analyze performance trends from historical data"""
        if not historical_metrics:
            return {}
        
        # Extract time series for each metric
        timestamps = [m.timestamp for m in historical_metrics]
        
        metrics_series = {
            "cpu_usage": [m.cpu_usage for m in historical_metrics],
            "memory_usage": [m.memory_usage for m in historical_metrics],
            "query_response_time": [m.query_response_time for m in historical_metrics],
            "cache_hit_rate": [m.cache_hit_rate for m in historical_metrics],
            "error_rate": [m.error_rate for m in historical_metrics],
            "throughput": [m.throughput for m in historical_metrics]
        }
        
        trends = {}
        for metric_name, values in metrics_series.items():
            if len(values) > 1:
                # Calculate basic trend
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)
                
                trends[metric_name] = {
                    "trend_direction": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
                    "trend_strength": abs(slope),
                    "current_value": values[-1],
                    "average_value": np.mean(values),
                    "volatility": np.std(values),
                    "min_value": min(values),
                    "max_value": max(values)
                }
        
        return trends
    
    async def _identify_performance_bottlenecks(
        self, 
        current_metrics: PerformanceMetrics,
        historical_metrics: List[PerformanceMetrics]
    ) -> List[Dict[str, Any]]:
        """Identify system performance bottlenecks"""
        bottlenecks = []
        
        # CPU bottleneck
        if current_metrics.cpu_usage > self.performance_thresholds["cpu_usage_warning"]:
            bottlenecks.append({
                "type": "cpu_bottleneck",
                "severity": "high" if current_metrics.cpu_usage > 90 else "medium",
                "current_value": current_metrics.cpu_usage,
                "threshold": self.performance_thresholds["cpu_usage_warning"],
                "impact": "System responsiveness and throughput degradation",
                "suggested_actions": ["Scale CPU resources", "Optimize CPU-intensive operations"]
            })
        
        # Memory bottleneck
        if current_metrics.memory_usage > self.performance_thresholds["memory_usage_warning"]:
            bottlenecks.append({
                "type": "memory_bottleneck", 
                "severity": "high" if current_metrics.memory_usage > 95 else "medium",
                "current_value": current_metrics.memory_usage,
                "threshold": self.performance_thresholds["memory_usage_warning"],
                "impact": "Potential system instability and performance degradation",
                "suggested_actions": ["Increase memory allocation", "Optimize memory usage", "Implement memory cleanup"]
            })
        
        # Response time bottleneck
        if current_metrics.query_response_time > self.performance_thresholds["response_time_warning"]:
            bottlenecks.append({
                "type": "response_time_bottleneck",
                "severity": "high" if current_metrics.query_response_time > 1000 else "medium",
                "current_value": current_metrics.query_response_time,
                "threshold": self.performance_thresholds["response_time_warning"],
                "impact": "Poor user experience and reduced productivity",
                "suggested_actions": ["Optimize queries", "Improve caching", "Scale database resources"]
            })
        
        # Cache performance bottleneck
        if current_metrics.cache_hit_rate < self.performance_thresholds["cache_hit_rate_target"]:
            bottlenecks.append({
                "type": "cache_performance_bottleneck",
                "severity": "medium",
                "current_value": current_metrics.cache_hit_rate,
                "threshold": self.performance_thresholds["cache_hit_rate_target"],
                "impact": "Increased database load and slower response times",
                "suggested_actions": ["Optimize cache strategy", "Increase cache size", "Improve cache key design"]
            })
        
        return bottlenecks
    
    def _calculate_system_health_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate overall system health score"""
        scores = []
        
        # CPU score (lower usage = better)
        cpu_score = max(0, 1 - metrics.cpu_usage / 100)
        scores.append(cpu_score * 0.2)
        
        # Memory score (lower usage = better)
        memory_score = max(0, 1 - metrics.memory_usage / 100)
        scores.append(memory_score * 0.2)
        
        # Response time score (lower = better)
        response_score = max(0, 1 - metrics.query_response_time / 1000)  # Normalize to 1 second
        scores.append(response_score * 0.25)
        
        # Cache hit rate score (higher = better)
        cache_score = metrics.cache_hit_rate / 100
        scores.append(cache_score * 0.15)
        
        # Error rate score (lower = better)
        error_score = max(0, 1 - metrics.error_rate / 10)  # Normalize to 10%
        scores.append(error_score * 0.2)
        
        return sum(scores)
    
    def _get_health_status(self, health_score: float) -> str:
        """Convert health score to status"""
        if health_score >= 0.8:
            return "excellent"
        elif health_score >= 0.6:
            return "good"
        elif health_score >= 0.4:
            return "fair"
        elif health_score >= 0.2:
            return "poor"
        else:
            return "critical"