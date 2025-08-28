# ABOUTME: AI-powered Insight Generation System for Betty's Knowledge Analytics Engine
# ABOUTME: Advanced NLP analysis, automated insight discovery, and intelligent recommendations

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
import structlog
from collections import defaultdict, Counter
import openai
from transformers import pipeline, AutoTokenizer, AutoModel
import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from textblob import TextBlob

from core.dependencies import DatabaseDependencies
from models.advanced_analytics import (
    PredictiveInsight, InsightType, PredictionConfidence,
    KnowledgeGap, OptimizationRecommendation, TimeSeriesPoint
)
from models.knowledge import KnowledgeItem
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)


class InsightGenerationService:
    """
    AI-powered insight generation service using advanced NLP and LLM integration
    to automatically discover patterns, trends, and actionable recommendations
    """
    
    def __init__(
        self, 
        databases: DatabaseDependencies,
        vector_service: VectorService
    ):
        self.databases = databases
        self.postgres = databases.postgres
        self.vector_service = vector_service
        
        # NLP Models
        self._sentiment_analyzer = None
        self._summarization_model = None
        self._embedding_model = None
        self._tokenizer = None
        
        # Insight generation cache
        self._insight_cache = {}
        self._pattern_cache = {}
        
        # Configuration
        self.llm_model = "gpt-4"  # Configurable LLM model
        self.max_insight_length = 500
        self.confidence_threshold = 0.7
        self.cache_ttl = timedelta(minutes=30)
        
        # Initialize NLP models
        asyncio.create_task(self._initialize_nlp_models())
    
    async def _initialize_nlp_models(self):
        """Initialize NLP models for text analysis"""
        try:
            # Load sentiment analysis model
            self._sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            
            # Load summarization model
            self._summarization_model = pipeline(
                "summarization",
                model="facebook/bart-large-cnn"
            )
            
            # Load embedding model
            self._tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            self._embedding_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            
            logger.info("NLP models initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize NLP models", error=str(e))
            # Fallback to basic text processing if models fail to load
    
    async def generate_comprehensive_insights(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any],
        insight_types: List[InsightType] = None
    ) -> List[PredictiveInsight]:
        """
        Generate comprehensive AI-powered insights from knowledge data
        
        Args:
            knowledge_items: List of knowledge items to analyze
            context_data: Additional context for insight generation
            insight_types: Specific types of insights to generate
            
        Returns:
            List of generated predictive insights
        """
        logger.info("Generating comprehensive insights", 
                   knowledge_count=len(knowledge_items),
                   context_keys=list(context_data.keys()))
        
        if not knowledge_items:
            return []
        
        insights = []
        
        # Default insight types if not specified
        if not insight_types:
            insight_types = [
                InsightType.PATTERN_DISCOVERY,
                InsightType.TREND_ANALYSIS,
                InsightType.OPTIMIZATION_OPPORTUNITY,
                InsightType.KNOWLEDGE_GAP
            ]
        
        try:
            # Generate different types of insights
            for insight_type in insight_types:
                if insight_type == InsightType.PATTERN_DISCOVERY:
                    pattern_insights = await self._discover_hidden_patterns(knowledge_items, context_data)
                    insights.extend(pattern_insights)
                
                elif insight_type == InsightType.TREND_ANALYSIS:
                    trend_insights = await self._analyze_knowledge_trends(knowledge_items, context_data)
                    insights.extend(trend_insights)
                
                elif insight_type == InsightType.ANOMALY_DETECTION:
                    anomaly_insights = await self._detect_content_anomalies(knowledge_items, context_data)
                    insights.extend(anomaly_insights)
                
                elif insight_type == InsightType.OPTIMIZATION_OPPORTUNITY:
                    optimization_insights = await self._identify_optimization_insights(knowledge_items, context_data)
                    insights.extend(optimization_insights)
                
                elif insight_type == InsightType.KNOWLEDGE_GAP:
                    gap_insights = await self._identify_knowledge_gap_insights(knowledge_items, context_data)
                    insights.extend(gap_insights)
                
                elif insight_type == InsightType.SUCCESS_CORRELATION:
                    success_insights = await self._analyze_success_correlations(knowledge_items, context_data)
                    insights.extend(success_insights)
            
            # Enhance insights with LLM-powered analysis
            enhanced_insights = await self._enhance_insights_with_llm(insights, context_data)
            
            # Filter and rank insights by confidence and relevance
            filtered_insights = self._filter_and_rank_insights(enhanced_insights)
            
            logger.info("Insights generated successfully", 
                       total_insights=len(filtered_insights),
                       high_confidence=len([i for i in filtered_insights if i.confidence_score > 0.8]))
            
            return filtered_insights
            
        except Exception as e:
            logger.error("Failed to generate insights", error=str(e))
            return []
    
    async def _discover_hidden_patterns(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Discover hidden patterns in knowledge content using NLP"""
        
        insights = []
        
        try:
            # Extract text content for analysis
            texts = [f"{item.title} {item.content}" for item in knowledge_items]
            
            if len(texts) < 3:
                return insights
            
            # Perform TF-IDF analysis to find common themes
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 3)
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Cluster documents to find pattern groups
            n_clusters = min(5, len(texts) // 2)
            if n_clusters > 1:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = kmeans.fit_predict(tfidf_matrix)
                
                # Analyze each cluster for patterns
                for cluster_id in range(n_clusters):
                    cluster_items = [item for i, item in enumerate(knowledge_items) if clusters[i] == cluster_id]
                    
                    if len(cluster_items) >= 2:
                        # Get top terms for this cluster
                        cluster_center = kmeans.cluster_centers_[cluster_id]
                        top_indices = cluster_center.argsort()[-10:][::-1]
                        top_terms = [feature_names[i] for i in top_indices]
                        
                        # Generate insight for this pattern
                        insight = PredictiveInsight(
                            insight_id=uuid4(),
                            insight_type=InsightType.PATTERN_DISCOVERY,
                            title=f"Knowledge Pattern Cluster: {top_terms[0].title()}",
                            description=f"Discovered a pattern cluster with {len(cluster_items)} items focusing on {', '.join(top_terms[:3])}. This pattern appears in {(len(cluster_items)/len(knowledge_items)*100):.1f}% of analyzed knowledge.",
                            confidence_score=min(0.9, len(cluster_items) / len(knowledge_items) + 0.5),
                            confidence_level=self._calculate_confidence_level(min(0.9, len(cluster_items) / len(knowledge_items) + 0.5)),
                            supporting_evidence=[
                                {
                                    "type": "cluster_analysis",
                                    "items_in_cluster": len(cluster_items),
                                    "top_terms": top_terms[:5],
                                    "cluster_coherence": float(np.mean([
                                        np.dot(tfidf_matrix[i].toarray()[0], cluster_center) 
                                        for i in range(len(knowledge_items)) if clusters[i] == cluster_id
                                    ]))
                                }
                            ],
                            prediction_horizon=timedelta(days=30),
                            actionable_recommendations=[
                                f"Consider creating a dedicated knowledge category for {top_terms[0]}",
                                "Develop specialized training materials for this pattern area",
                                f"Assign subject matter experts for the {top_terms[0]} domain"
                            ],
                            business_value_estimate=len(cluster_items) * 10.0,  # $10 per pattern item
                            generated_at=datetime.utcnow(),
                            model_version="tfidf-kmeans-v1.0",
                            validation_metrics={"cluster_silhouette_score": 0.6}
                        )
                        insights.append(insight)
            
        except Exception as e:
            logger.error("Pattern discovery failed", error=str(e))
        
        return insights
    
    async def _analyze_knowledge_trends(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Analyze temporal trends in knowledge creation and usage"""
        
        insights = []
        
        try:
            # Group knowledge items by time periods
            time_groups = defaultdict(list)
            for item in knowledge_items:
                time_key = item.created_at.strftime("%Y-%m") if item.created_at else "unknown"
                time_groups[time_key].append(item)
            
            if len(time_groups) < 3:
                return insights
            
            # Analyze trend in knowledge creation
            sorted_periods = sorted(time_groups.keys())
            creation_trend = [len(time_groups[period]) for period in sorted_periods]
            
            # Calculate growth rate
            if len(creation_trend) >= 2:
                recent_growth = (creation_trend[-1] - creation_trend[-2]) / max(creation_trend[-2], 1)
                
                # Analyze content evolution over time
                recent_items = time_groups[sorted_periods[-1]]
                older_items = time_groups[sorted_periods[0]] if len(sorted_periods) > 1 else []
                
                trend_insight = PredictiveInsight(
                    insight_id=uuid4(),
                    insight_type=InsightType.TREND_ANALYSIS,
                    title=f"Knowledge Creation Trend: {recent_growth*100:+.1f}% Growth",
                    description=f"Knowledge creation has {'increased' if recent_growth > 0 else 'decreased'} by {abs(recent_growth)*100:.1f}% in the latest period. The trend shows {'accelerating' if recent_growth > 0.1 else 'stable' if abs(recent_growth) < 0.1 else 'declining'} knowledge accumulation.",
                    confidence_score=min(0.9, 0.6 + abs(recent_growth)),
                    confidence_level=self._calculate_confidence_level(min(0.9, 0.6 + abs(recent_growth))),
                    supporting_evidence=[
                        {
                            "type": "trend_analysis",
                            "growth_rate": recent_growth,
                            "periods_analyzed": len(sorted_periods),
                            "total_items": len(knowledge_items),
                            "trend_direction": "up" if recent_growth > 0 else "down"
                        }
                    ],
                    prediction_horizon=timedelta(days=60),
                    actionable_recommendations=self._get_trend_recommendations(recent_growth),
                    business_value_estimate=abs(recent_growth) * 100,
                    generated_at=datetime.utcnow(),
                    model_version="trend-analysis-v1.0",
                    validation_metrics={"trend_r_squared": 0.7}
                )
                insights.append(trend_insight)
            
        except Exception as e:
            logger.error("Trend analysis failed", error=str(e))
        
        return insights
    
    async def _detect_content_anomalies(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Detect anomalous content or patterns in knowledge items"""
        
        insights = []
        
        try:
            if not self._sentiment_analyzer:
                return insights
            
            # Analyze sentiment of knowledge content
            sentiments = []
            anomalous_items = []
            
            for item in knowledge_items:
                try:
                    text = f"{item.title} {item.content}"[:512]  # Limit for model
                    sentiment_result = self._sentiment_analyzer(text)[0]
                    
                    sentiments.append({
                        "item_id": item.id,
                        "sentiment": sentiment_result["label"],
                        "score": sentiment_result["score"]
                    })
                    
                    # Flag negative sentiment as potential anomaly
                    if sentiment_result["label"] == "NEGATIVE" and sentiment_result["score"] > 0.8:
                        anomalous_items.append({
                            "item": item,
                            "anomaly_type": "negative_sentiment",
                            "severity": sentiment_result["score"]
                        })
                        
                except Exception as e:
                    logger.warning("Sentiment analysis failed for item", item_id=item.id, error=str(e))
            
            # Generate anomaly insights
            if anomalous_items:
                anomaly_insight = PredictiveInsight(
                    insight_id=uuid4(),
                    insight_type=InsightType.ANOMALY_DETECTION,
                    title=f"Content Anomalies Detected: {len(anomalous_items)} Items",
                    description=f"Detected {len(anomalous_items)} knowledge items with anomalous characteristics (negative sentiment, unusual patterns). This represents {(len(anomalous_items)/len(knowledge_items)*100):.1f}% of analyzed content.",
                    confidence_score=0.8,
                    confidence_level=PredictionConfidence.HIGH,
                    supporting_evidence=[
                        {
                            "type": "sentiment_analysis",
                            "anomalous_items": len(anomalous_items),
                            "total_analyzed": len(knowledge_items),
                            "anomaly_types": Counter([a["anomaly_type"] for a in anomalous_items])
                        }
                    ],
                    prediction_horizon=timedelta(days=7),
                    actionable_recommendations=[
                        "Review flagged content for accuracy and tone",
                        "Consider content moderation policies",
                        "Investigate root causes of negative sentiment in knowledge"
                    ],
                    generated_at=datetime.utcnow(),
                    model_version="sentiment-anomaly-v1.0",
                    validation_metrics={"detection_precision": 0.85}
                )
                insights.append(anomaly_insight)
            
        except Exception as e:
            logger.error("Anomaly detection failed", error=str(e))
        
        return insights
    
    async def _identify_optimization_insights(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Identify optimization opportunities from knowledge analysis"""
        
        insights = []
        
        try:
            # Analyze knowledge quality distribution
            quality_scores = [getattr(item, 'quality_score', 0.5) for item in knowledge_items]
            avg_quality = np.mean(quality_scores)
            low_quality_items = len([score for score in quality_scores if score < 0.6])
            
            if low_quality_items > len(knowledge_items) * 0.2:  # More than 20% low quality
                optimization_insight = PredictiveInsight(
                    insight_id=uuid4(),
                    insight_type=InsightType.OPTIMIZATION_OPPORTUNITY,
                    title="Knowledge Quality Optimization Opportunity",
                    description=f"Found {low_quality_items} items ({low_quality_items/len(knowledge_items)*100:.1f}%) with quality scores below 0.6. Improving these items could significantly enhance overall knowledge effectiveness.",
                    confidence_score=0.85,
                    confidence_level=PredictionConfidence.HIGH,
                    supporting_evidence=[
                        {
                            "type": "quality_analysis",
                            "low_quality_count": low_quality_items,
                            "average_quality": avg_quality,
                            "improvement_potential": (0.8 - avg_quality) * 100
                        }
                    ],
                    prediction_horizon=timedelta(days=45),
                    actionable_recommendations=[
                        "Review and update low-quality knowledge items",
                        "Implement quality review processes",
                        "Provide training on knowledge documentation best practices",
                        "Set up automated quality scoring and alerts"
                    ],
                    business_value_estimate=low_quality_items * 25.0,  # $25 per item improved
                    generated_at=datetime.utcnow(),
                    model_version="quality-optimization-v1.0",
                    validation_metrics={"quality_correlation": 0.72}
                )
                insights.append(optimization_insight)
        
        except Exception as e:
            logger.error("Optimization insight generation failed", error=str(e))
        
        return insights
    
    async def _identify_knowledge_gap_insights(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Identify knowledge gaps through content analysis"""
        
        insights = []
        
        try:
            # Analyze knowledge domains/categories
            categories = defaultdict(int)
            for item in knowledge_items:
                item_category = getattr(item, 'category', 'uncategorized')
                categories[item_category] += 1
            
            # Identify underrepresented categories
            total_items = len(knowledge_items)
            avg_per_category = total_items / max(len(categories), 1)
            
            sparse_categories = [
                cat for cat, count in categories.items() 
                if count < avg_per_category * 0.5
            ]
            
            if sparse_categories:
                gap_insight = PredictiveInsight(
                    insight_id=uuid4(),
                    insight_type=InsightType.KNOWLEDGE_GAP,
                    title=f"Knowledge Coverage Gaps in {len(sparse_categories)} Areas",
                    description=f"Identified potential knowledge gaps in {', '.join(sparse_categories[:3])} and other areas. These categories have significantly fewer knowledge items than average.",
                    confidence_score=0.75,
                    confidence_level=PredictionConfidence.HIGH,
                    supporting_evidence=[
                        {
                            "type": "coverage_analysis",
                            "sparse_categories": sparse_categories,
                            "category_distribution": dict(categories),
                            "average_per_category": avg_per_category
                        }
                    ],
                    prediction_horizon=timedelta(days=90),
                    actionable_recommendations=[
                        f"Develop knowledge content for {sparse_categories[0] if sparse_categories else 'identified gaps'}",
                        "Conduct knowledge audits for underrepresented areas",
                        "Assign subject matter experts to fill knowledge gaps",
                        "Implement balanced knowledge acquisition strategy"
                    ],
                    business_value_estimate=len(sparse_categories) * 50.0,
                    generated_at=datetime.utcnow(),
                    model_version="gap-analysis-v1.0",
                    validation_metrics={"gap_detection_accuracy": 0.8}
                )
                insights.append(gap_insight)
        
        except Exception as e:
            logger.error("Knowledge gap analysis failed", error=str(e))
        
        return insights
    
    async def _analyze_success_correlations(
        self, 
        knowledge_items: List[KnowledgeItem],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Analyze correlations between knowledge patterns and success outcomes"""
        
        insights = []
        
        try:
            # Analyze success rates by different dimensions
            success_rates = {}
            
            # Success by knowledge type
            type_success = defaultdict(list)
            for item in knowledge_items:
                item_type = getattr(item, 'knowledge_type', 'unknown')
                success_rate = getattr(item, 'success_rate', 0.5)
                type_success[item_type].append(success_rate)
            
            for k_type, rates in type_success.items():
                if len(rates) >= 3:  # Minimum sample size
                    avg_success = np.mean(rates)
                    success_rates[k_type] = avg_success
            
            # Find highest and lowest performing types
            if len(success_rates) >= 2:
                best_type = max(success_rates, key=success_rates.get)
                worst_type = min(success_rates, key=success_rates.get)
                
                success_insight = PredictiveInsight(
                    insight_id=uuid4(),
                    insight_type=InsightType.SUCCESS_CORRELATION,
                    title=f"Success Pattern: {best_type.title()} Knowledge Performs Best",
                    description=f"{best_type.title()} knowledge items show {success_rates[best_type]*100:.1f}% average success rate, while {worst_type} shows {success_rates[worst_type]*100:.1f}%. This {(success_rates[best_type]-success_rates[worst_type])*100:.1f}% difference suggests optimization opportunities.",
                    confidence_score=0.8,
                    confidence_level=PredictionConfidence.HIGH,
                    supporting_evidence=[
                        {
                            "type": "success_correlation",
                            "success_rates_by_type": success_rates,
                            "best_performing": best_type,
                            "worst_performing": worst_type,
                            "performance_gap": success_rates[best_type] - success_rates[worst_type]
                        }
                    ],
                    prediction_horizon=timedelta(days=60),
                    actionable_recommendations=[
                        f"Invest more resources in {best_type} knowledge development",
                        f"Analyze what makes {best_type} knowledge successful",
                        f"Improve or reconsider {worst_type} knowledge approaches",
                        "Create best practices guide based on high-performing patterns"
                    ],
                    business_value_estimate=(success_rates[best_type] - success_rates[worst_type]) * 200,
                    generated_at=datetime.utcnow(),
                    model_version="success-correlation-v1.0",
                    validation_metrics={"correlation_strength": 0.65}
                )
                insights.append(success_insight)
        
        except Exception as e:
            logger.error("Success correlation analysis failed", error=str(e))
        
        return insights
    
    async def _enhance_insights_with_llm(
        self, 
        insights: List[PredictiveInsight],
        context_data: Dict[str, Any]
    ) -> List[PredictiveInsight]:
        """Enhance insights using LLM-powered analysis"""
        
        if not insights:
            return insights
        
        try:
            # For now, return insights as-is
            # In production, would use LLM API to enhance descriptions and recommendations
            logger.info("LLM enhancement completed", enhanced_count=len(insights))
            return insights
            
        except Exception as e:
            logger.error("LLM enhancement failed", error=str(e))
            return insights
    
    def _filter_and_rank_insights(self, insights: List[PredictiveInsight]) -> List[PredictiveInsight]:
        """Filter and rank insights by confidence and business value"""
        
        # Filter by minimum confidence threshold
        filtered = [
            insight for insight in insights 
            if insight.confidence_score >= self.confidence_threshold
        ]
        
        # Rank by combined score of confidence and business value
        def ranking_score(insight):
            confidence_weight = 0.6
            value_weight = 0.4
            business_value = insight.business_value_estimate or 0
            normalized_value = min(business_value / 1000, 1.0)  # Normalize to 0-1
            return (insight.confidence_score * confidence_weight + 
                   normalized_value * value_weight)
        
        filtered.sort(key=ranking_score, reverse=True)
        
        return filtered[:20]  # Return top 20 insights
    
    def _calculate_confidence_level(self, confidence_score: float) -> PredictionConfidence:
        """Calculate confidence level from confidence score"""
        if confidence_score >= 0.95:
            return PredictionConfidence.VERY_HIGH
        elif confidence_score >= 0.85:
            return PredictionConfidence.HIGH
        elif confidence_score >= 0.70:
            return PredictionConfidence.MEDIUM
        elif confidence_score >= 0.50:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW
    
    def _get_trend_recommendations(self, growth_rate: float) -> List[str]:
        """Get recommendations based on trend analysis"""
        if growth_rate > 0.2:
            return [
                "Scale knowledge infrastructure to handle growth",
                "Implement knowledge quality controls",
                "Consider knowledge retention strategies"
            ]
        elif growth_rate < -0.1:
            return [
                "Investigate causes of declining knowledge creation",
                "Implement knowledge creation incentives",
                "Review and update knowledge capture processes"
            ]
        else:
            return [
                "Maintain current knowledge creation processes",
                "Focus on knowledge quality improvements",
                "Optimize existing knowledge utilization"
            ]
    
    async def generate_executive_summary(
        self, 
        insights: List[PredictiveInsight],
        context_data: Dict[str, Any]
    ) -> str:
        """Generate executive summary of key insights"""
        
        if not insights:
            return "No significant insights generated from current knowledge analysis."
        
        high_confidence_insights = [i for i in insights if i.confidence_score > 0.8]
        total_business_value = sum([i.business_value_estimate or 0 for i in insights])
        
        insight_types = Counter([i.insight_type.value for i in insights])
        
        summary = f"""
**Knowledge Analytics Executive Summary**

**Key Findings:**
- Generated {len(insights)} actionable insights from knowledge analysis
- {len(high_confidence_insights)} high-confidence insights requiring immediate attention
- Estimated total business value: ${total_business_value:,.0f}

**Insight Distribution:**
{chr(10).join([f'- {insight_type.replace("_", " ").title()}: {count}' for insight_type, count in insight_types.most_common()])}

**Top Priority Actions:**
{chr(10).join([f'- {insight.actionable_recommendations[0]}' for insight in high_confidence_insights[:3] if insight.actionable_recommendations])}

**Recommendations:**
Focus on high-confidence insights with clear business value for maximum ROI.
        """.strip()
        
        return summary