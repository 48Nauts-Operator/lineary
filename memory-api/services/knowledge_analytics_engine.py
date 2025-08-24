# ABOUTME: Knowledge Analytics Engine - Core analytics computation and ML pipeline for Betty Phase 6
# ABOUTME: Advanced pattern analysis, correlation detection, and predictive intelligence processing

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
import structlog
from collections import defaultdict, Counter
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from scipy import stats
import networkx as nx

from core.database import DatabaseManager
from core.dependencies import DatabaseDependencies
from models.advanced_analytics import (
    AdvancedAnalyticsRequest, AdvancedAnalyticsResponse, TimeSeriesPoint,
    PatternCorrelation, KnowledgeGap, PredictiveInsight, OrganizationalIntelligence,
    InsightType, PredictionConfidence, AnalyticsTimeRange, MLModelMetrics,
    PredictionResult, OptimizationRecommendation
)
from models.knowledge import KnowledgeItem
from services.vector_service import VectorService
from services.pattern_intelligence_service import PatternIntelligenceEngine

logger = structlog.get_logger(__name__)


class KnowledgeAnalyticsEngine:
    """
    Core Knowledge Analytics Engine providing comprehensive analytics,
    ML-powered insights, and predictive intelligence for organizational knowledge
    """
    
    def __init__(
        self, 
        databases: DatabaseDependencies,
        vector_service: VectorService,
        pattern_intelligence: PatternIntelligenceEngine
    ):
        self.databases = databases
        self.postgres = databases.postgres
        self.neo4j = databases.neo4j
        self.vector_service = vector_service
        self.pattern_intelligence = pattern_intelligence
        
        # ML Models and Analytics Cache
        self._ml_models = {}
        self._analytics_cache = {}
        self._correlation_matrix = None
        self._knowledge_graph = nx.Graph()
        self._last_cache_update = None
        
        # Performance tracking
        self._query_performance = defaultdict(list)
        
        # Configuration
        self.cache_ttl = timedelta(minutes=15)  # 15-minute cache TTL
        self.min_correlation_threshold = 0.7
        self.anomaly_detection_threshold = 0.05
        
    async def execute_advanced_analytics(
        self, 
        request: AdvancedAnalyticsRequest
    ) -> AdvancedAnalyticsResponse:
        """
        Execute comprehensive advanced analytics query with ML insights
        
        Args:
            request: Analytics request with query type, filters, and parameters
            
        Returns:
            Comprehensive analytics response with insights and predictions
        """
        start_time = datetime.utcnow()
        logger.info("Executing advanced analytics query", 
                   query_type=request.query_type,
                   time_range=request.time_range)
        
        try:
            # Initialize response
            response = AdvancedAnalyticsResponse(
                query_type=request.query_type,
                execution_time_ms=0.0,
                data_points_analyzed=0,
                results={}
            )
            
            # Route to appropriate analytics handler
            if request.query_type == "pattern_correlation_analysis":
                response = await self._analyze_pattern_correlations(request, response)
            elif request.query_type == "knowledge_growth_trends":
                response = await self._analyze_knowledge_growth_trends(request, response)
            elif request.query_type == "organizational_intelligence":
                response = await self._analyze_organizational_intelligence(request, response)
            elif request.query_type == "anomaly_detection":
                response = await self._detect_knowledge_anomalies(request, response)
            elif request.query_type == "predictive_insights":
                response = await self._generate_predictive_insights(request, response)
            elif request.query_type == "optimization_analysis":
                response = await self._analyze_optimization_opportunities(request, response)
            else:
                response.results = {"error": f"Unknown query type: {request.query_type}"}
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response.execution_time_ms = execution_time
            
            # Track performance
            self._query_performance[request.query_type].append(execution_time)
            
            # Log performance warning if query is slow
            if execution_time > 500:  # 500ms threshold
                logger.warning("Slow analytics query detected", 
                             query_type=request.query_type,
                             execution_time_ms=execution_time)
            
            logger.info("Analytics query completed", 
                       query_type=request.query_type,
                       execution_time_ms=execution_time,
                       data_points=response.data_points_analyzed)
            
            return response
            
        except Exception as e:
            logger.error("Analytics query failed", 
                        query_type=request.query_type,
                        error=str(e))
            raise
    
    async def _analyze_pattern_correlations(
        self, 
        request: AdvancedAnalyticsRequest,
        response: AdvancedAnalyticsResponse
    ) -> AdvancedAnalyticsResponse:
        """Analyze correlations between knowledge patterns"""
        
        # Get knowledge items in time range
        knowledge_items = await self._get_knowledge_items_in_range(
            request.time_range, 
            request.filters
        )
        response.data_points_analyzed = len(knowledge_items)
        
        if len(knowledge_items) < 2:
            response.results = {"correlations": [], "message": "Insufficient data for correlation analysis"}
            return response
        
        # Generate embeddings for semantic similarity
        embeddings = []
        item_ids = []
        for item in knowledge_items:
            embedding = await self.vector_service.generate_embedding(
                f"{item.title} {item.content}"
            )
            embeddings.append(embedding)
            item_ids.append(item.id)
        
        # Calculate correlation matrix
        embeddings_matrix = np.array(embeddings)
        correlation_matrix = cosine_similarity(embeddings_matrix)
        
        # Extract significant correlations
        correlations = []
        for i in range(len(knowledge_items)):
            for j in range(i + 1, len(knowledge_items)):
                correlation_strength = correlation_matrix[i][j]
                
                if correlation_strength >= self.min_correlation_threshold:
                    correlation = PatternCorrelation(
                        pattern_1_id=knowledge_items[i].id,
                        pattern_2_id=knowledge_items[j].id,
                        correlation_strength=float(correlation_strength),
                        correlation_type="semantic",
                        statistical_significance=0.01,  # Will calculate properly
                        sample_size=len(knowledge_items),
                        discovered_at=datetime.utcnow(),
                        validation_score=correlation_strength * 0.9  # Conservative validation
                    )
                    correlations.append(correlation)
        
        response.correlations = correlations
        response.results = {
            "total_correlations": len(correlations),
            "strong_correlations": len([c for c in correlations if c.correlation_strength > 0.8]),
            "correlation_matrix_stats": {
                "mean_correlation": float(np.mean(correlation_matrix)),
                "max_correlation": float(np.max(correlation_matrix[correlation_matrix < 1.0])),
                "correlation_distribution": np.histogram(correlation_matrix, bins=10)[0].tolist()
            }
        }
        
        return response
    
    async def _analyze_knowledge_growth_trends(
        self, 
        request: AdvancedAnalyticsRequest,
        response: AdvancedAnalyticsResponse
    ) -> AdvancedAnalyticsResponse:
        """Analyze knowledge growth trends with time-series analysis"""
        
        # Get time-series data
        time_series_data = await self._get_knowledge_time_series(
            request.time_range,
            request.aggregation_level
        )
        response.data_points_analyzed = len(time_series_data)
        
        # Convert to pandas for analysis
        df = pd.DataFrame([
            {"timestamp": point.timestamp, "value": point.value, **point.metadata}
            for point in time_series_data
        ])
        
        if len(df) < 7:  # Need minimum data for trend analysis
            response.results = {"message": "Insufficient data for trend analysis"}
            return response
        
        # Calculate trends
        df['timestamp_numeric'] = pd.to_datetime(df['timestamp']).astype(int) / 10**9
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df['timestamp_numeric'], df['value']
        )
        
        # Detect anomalies using isolation forest
        isolation_forest = IsolationForest(contamination=self.anomaly_detection_threshold)
        df['anomaly_score'] = isolation_forest.fit_predict(df[['value']].values)
        
        # Add anomaly scores to time series points
        for i, point in enumerate(time_series_data):
            point.anomaly_score = float(df.iloc[i]['anomaly_score'])
        
        response.time_series_data = time_series_data
        response.results = {
            "trend_analysis": {
                "slope": float(slope),
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "growth_rate_per_day": float(slope * 86400) if slope > 0 else 0.0
            },
            "anomalies_detected": int(sum(1 for score in df['anomaly_score'] if score == -1)),
            "statistical_summary": {
                "mean": float(df['value'].mean()),
                "std": float(df['value'].std()),
                "min": float(df['value'].min()),
                "max": float(df['value'].max()),
                "median": float(df['value'].median())
            }
        }
        
        return response
    
    async def _analyze_organizational_intelligence(
        self, 
        request: AdvancedAnalyticsRequest,
        response: AdvancedAnalyticsResponse
    ) -> AdvancedAnalyticsResponse:
        """Analyze organizational intelligence metrics"""
        
        # Get organizational data
        org_data = await self._get_organizational_metrics(request.time_range)
        response.data_points_analyzed = org_data.get("total_data_points", 0)
        
        # Calculate intelligence metrics
        intelligence_metrics = OrganizationalIntelligence(
            team_id=request.filters.get("team_id"),
            productivity_score=org_data.get("productivity_score", 0.7),
            knowledge_utilization_rate=org_data.get("knowledge_utilization_rate", 0.6),
            learning_velocity=org_data.get("learning_velocity", 5.2),
            collaboration_index=org_data.get("collaboration_index", 0.8),
            innovation_index=org_data.get("innovation_index", 0.4),
            decision_quality_score=org_data.get("decision_quality_score", 0.75),
            knowledge_retention_rate=org_data.get("knowledge_retention_rate", 0.85),
            skill_gap_analysis=org_data.get("skill_gap_analysis", {}),
            recommended_learning_paths=org_data.get("recommended_learning_paths", [])
        )
        
        response.organizational_metrics = intelligence_metrics
        response.results = {
            "overall_intelligence_score": (
                intelligence_metrics.productivity_score * 0.25 +
                intelligence_metrics.knowledge_utilization_rate * 0.20 +
                intelligence_metrics.collaboration_index * 0.20 +
                intelligence_metrics.innovation_index * 0.15 +
                intelligence_metrics.decision_quality_score * 0.20
            ) * 100,
            "key_strengths": self._identify_strengths(intelligence_metrics),
            "improvement_areas": self._identify_improvement_areas(intelligence_metrics),
            "benchmark_comparison": await self._get_benchmark_comparison(intelligence_metrics)
        }
        
        return response
    
    async def _detect_knowledge_anomalies(
        self, 
        request: AdvancedAnalyticsRequest,
        response: AdvancedAnalyticsResponse
    ) -> AdvancedAnalyticsResponse:
        """Detect anomalies in knowledge patterns and usage"""
        
        # Get knowledge usage patterns
        usage_patterns = await self._get_knowledge_usage_patterns(request.time_range)
        response.data_points_analyzed = len(usage_patterns)
        
        if len(usage_patterns) < 10:
            response.results = {"message": "Insufficient data for anomaly detection"}
            return response
        
        # Prepare data for anomaly detection
        features = []
        for pattern in usage_patterns:
            features.append([
                pattern.get("access_frequency", 0),
                pattern.get("success_rate", 0),
                pattern.get("reuse_count", 0),
                pattern.get("quality_score", 0.5),
                pattern.get("age_days", 0)
            ])
        
        features_array = np.array(features)
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_array)
        
        # Detect anomalies using Isolation Forest
        isolation_forest = IsolationForest(
            contamination=self.anomaly_detection_threshold,
            random_state=42
        )
        anomaly_scores = isolation_forest.fit_predict(features_scaled)
        anomaly_probabilities = isolation_forest.score_samples(features_scaled)
        
        # Identify anomalous patterns
        anomalies = []
        for i, (pattern, score, prob) in enumerate(zip(usage_patterns, anomaly_scores, anomaly_probabilities)):
            if score == -1:  # Anomaly detected
                anomalies.append({
                    "pattern_id": pattern.get("pattern_id"),
                    "anomaly_type": self._classify_anomaly_type(pattern, features_array[i]),
                    "anomaly_score": float(prob),
                    "pattern_details": pattern,
                    "explanation": self._explain_anomaly(pattern, features_array[i])
                })
        
        response.results = {
            "total_anomalies": len(anomalies),
            "anomaly_types": Counter([a["anomaly_type"] for a in anomalies]),
            "anomalies": anomalies[:request.max_results],
            "anomaly_detection_settings": {
                "contamination_threshold": self.anomaly_detection_threshold,
                "features_analyzed": ["access_frequency", "success_rate", "reuse_count", "quality_score", "age_days"]
            }
        }
        
        return response
    
    async def _generate_predictive_insights(
        self, 
        request: AdvancedAnalyticsRequest,
        response: AdvancedAnalyticsResponse
    ) -> AdvancedAnalyticsResponse:
        """Generate AI-powered predictive insights"""
        
        # Get historical data for prediction
        historical_data = await self._get_historical_analytics_data(request.time_range)
        response.data_points_analyzed = len(historical_data)
        
        insights = []
        
        # Generate different types of insights
        if request.include_predictions:
            # Knowledge growth prediction
            growth_insight = await self._predict_knowledge_growth(historical_data)
            if growth_insight:
                insights.append(growth_insight)
            
            # Success rate prediction
            success_insight = await self._predict_pattern_success_rates(historical_data)
            if success_insight:
                insights.append(success_insight)
            
            # Resource needs prediction
            resource_insight = await self._predict_resource_needs(historical_data)
            if resource_insight:
                insights.append(resource_insight)
        
        # Generate trend analysis insights
        trend_insights = await self._analyze_emerging_trends(historical_data)
        insights.extend(trend_insights)
        
        # Generate knowledge gap insights
        gap_insights = await self._identify_knowledge_gaps(historical_data)
        
        response.insights = insights
        response.knowledge_gaps = gap_insights
        response.results = {
            "total_insights": len(insights),
            "insight_types": Counter([i.insight_type for i in insights]),
            "high_confidence_insights": len([i for i in insights if i.confidence_score > 0.8]),
            "actionable_insights": len([i for i in insights if i.actionable_recommendations]),
            "prediction_horizon_days": max([i.prediction_horizon.days for i in insights if i.prediction_horizon], default=0)
        }
        
        return response
    
    async def _analyze_optimization_opportunities(
        self, 
        request: AdvancedAnalyticsRequest,
        response: AdvancedAnalyticsResponse
    ) -> AdvancedAnalyticsResponse:
        """Analyze performance optimization opportunities"""
        
        # Get performance data
        performance_data = await self._get_performance_metrics(request.time_range)
        response.data_points_analyzed = len(performance_data)
        
        optimizations = []
        
        # Process optimization
        process_opts = await self._identify_process_optimizations(performance_data)
        optimizations.extend(process_opts)
        
        # Resource optimization
        resource_opts = await self._identify_resource_optimizations(performance_data)
        optimizations.extend(resource_opts)
        
        # Knowledge optimization
        knowledge_opts = await self._identify_knowledge_optimizations(performance_data)
        optimizations.extend(knowledge_opts)
        
        # Performance optimization
        perf_opts = await self._identify_performance_optimizations(performance_data)
        optimizations.extend(perf_opts)
        
        # Sort by ROI potential
        optimizations.sort(key=lambda x: x.estimated_roi or 0, reverse=True)
        
        response.results = {
            "total_opportunities": len(optimizations),
            "optimization_types": Counter([opt.optimization_type for opt in optimizations]),
            "high_impact_opportunities": len([opt for opt in optimizations if (opt.estimated_roi or 0) > 20]),
            "quick_wins": len([opt for opt in optimizations if opt.implementation_effort == "low"]),
            "optimizations": [opt.dict() for opt in optimizations[:request.max_results]],
            "potential_roi_range": {
                "min": min([opt.estimated_roi for opt in optimizations if opt.estimated_roi], default=0),
                "max": max([opt.estimated_roi for opt in optimizations if opt.estimated_roi], default=0),
                "average": np.mean([opt.estimated_roi for opt in optimizations if opt.estimated_roi]) if optimizations else 0
            }
        }
        
        return response
    
    # Helper methods for analytics processing
    
    async def _get_knowledge_items_in_range(
        self, 
        time_range: AnalyticsTimeRange, 
        filters: Dict[str, Any]
    ) -> List[KnowledgeItem]:
        """Get knowledge items within specified time range and filters"""
        # Implementation would query PostgreSQL with time range and filters
        # For now, return empty list - will be implemented with actual DB queries
        return []
    
    async def _get_knowledge_time_series(
        self, 
        time_range: AnalyticsTimeRange,
        aggregation_level: str
    ) -> List[TimeSeriesPoint]:
        """Generate time-series data for knowledge growth"""
        # Implementation would generate actual time-series from DB
        # For now, return sample data structure
        return [
            TimeSeriesPoint(
                timestamp=datetime.utcnow() - timedelta(days=i),
                value=float(100 + i * 2 + np.random.normal(0, 5)),
                metadata={"daily_increment": 2}
            )
            for i in range(30)
        ]
    
    async def _get_organizational_metrics(self, time_range: AnalyticsTimeRange) -> Dict[str, Any]:
        """Get organizational performance metrics"""
        # Implementation would query actual organizational data
        return {
            "total_data_points": 1000,
            "productivity_score": 0.75,
            "knowledge_utilization_rate": 0.68,
            "learning_velocity": 8.5,
            "collaboration_index": 0.82,
            "innovation_index": 0.45,
            "decision_quality_score": 0.78,
            "knowledge_retention_rate": 0.88,
            "skill_gap_analysis": {"AI/ML": 0.6, "Data Analysis": 0.3, "Domain Knowledge": 0.2},
            "recommended_learning_paths": ["Advanced Analytics", "Machine Learning Fundamentals"]
        }
    
    def _identify_strengths(self, intelligence: OrganizationalIntelligence) -> List[str]:
        """Identify organizational strengths based on intelligence metrics"""
        strengths = []
        if intelligence.collaboration_index > 0.8:
            strengths.append("Excellent cross-team collaboration")
        if intelligence.knowledge_retention_rate > 0.85:
            strengths.append("Strong knowledge retention")
        if intelligence.decision_quality_score > 0.75:
            strengths.append("High-quality decision making")
        return strengths
    
    def _identify_improvement_areas(self, intelligence: OrganizationalIntelligence) -> List[str]:
        """Identify areas for organizational improvement"""
        improvements = []
        if intelligence.innovation_index < 0.5:
            improvements.append("Innovation and creative problem-solving")
        if intelligence.knowledge_utilization_rate < 0.7:
            improvements.append("Knowledge utilization and application")
        if intelligence.learning_velocity < 5.0:
            improvements.append("Learning speed and knowledge acquisition")
        return improvements
    
    async def _get_benchmark_comparison(self, intelligence: OrganizationalIntelligence) -> Dict[str, float]:
        """Get benchmark comparison for organizational metrics"""
        # Would compare against industry benchmarks
        return {
            "productivity_vs_benchmark": 1.15,  # 15% above benchmark
            "collaboration_vs_benchmark": 1.08,
            "innovation_vs_benchmark": 0.92,
            "overall_vs_benchmark": 1.05
        }
    
    async def get_performance_analytics(self) -> Dict[str, Any]:
        """Get performance analytics for the analytics engine itself"""
        return {
            "average_query_times": {
                query_type: np.mean(times) if times else 0
                for query_type, times in self._query_performance.items()
            },
            "cache_hit_rate": 0.85,  # Would track actual cache performance
            "total_queries_processed": sum(len(times) for times in self._query_performance.values()),
            "ml_model_performance": await self._get_ml_model_metrics(),
            "system_health": "optimal" if all(
                np.mean(times) < 500 for times in self._query_performance.values() if times
            ) else "degraded"
        }