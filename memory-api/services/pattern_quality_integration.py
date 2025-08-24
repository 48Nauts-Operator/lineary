# ABOUTME: Integration service for Pattern Quality Scoring with existing BETTY systems
# ABOUTME: Connects quality scoring with Memory Correctness, Agent Learning, and Security Framework

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import structlog

from core.database import DatabaseManager
from models.pattern_quality import QualityScore, PatternContext, SuccessPrediction
from models.knowledge import KnowledgeItem
from models.memory_correctness import MemoryCorrectnessCheck, CorrectnessLevel
from services.memory_correctness_service import MemoryCorrectnessService
from services.agent_learning_engine import AgentLearningEngine
from core.security_framework import SecurityFramework
from services.pattern_quality_service import AdvancedQualityScorer

logger = structlog.get_logger(__name__)

class PatternQualityIntegrationService:
    """
    Integration service that connects Pattern Quality Scoring with existing BETTY systems
    to create a unified intelligence platform
    """
    
    def __init__(
        self, 
        db_manager: DatabaseManager,
        quality_scorer: AdvancedQualityScorer,
        memory_correctness_service: MemoryCorrectnessService,
        agent_learning_engine: AgentLearningEngine,
        security_framework: SecurityFramework
    ):
        self.db_manager = db_manager
        self.quality_scorer = quality_scorer
        self.memory_correctness = memory_correctness_service
        self.agent_learning = agent_learning_engine
        self.security = security_framework
        
        # Integration metrics
        self._integration_stats = {
            "memory_correctness_checks": 0,
            "agent_learning_updates": 0,
            "security_validations": 0,
            "quality_improvements": 0
        }
    
    async def integrated_pattern_analysis(
        self, 
        pattern: KnowledgeItem, 
        context: PatternContext,
        include_memory_check: bool = True,
        include_agent_learning: bool = True,
        include_security_validation: bool = True
    ) -> Dict[str, Any]:
        """
        Perform integrated pattern analysis using all BETTY intelligence systems
        
        Args:
            pattern: Pattern to analyze
            context: Analysis context
            include_memory_check: Include memory correctness validation
            include_agent_learning: Update agent learning systems
            include_security_validation: Include security framework validation
            
        Returns:
            Comprehensive analysis results from all systems
        """
        logger.info("Starting integrated pattern analysis", 
                   pattern_id=str(pattern.id),
                   context_domain=context.domain)
        
        analysis_results = {
            "pattern_id": pattern.id,
            "analysis_timestamp": datetime.utcnow(),
            "quality_score": None,
            "memory_correctness": None,
            "security_validation": None,
            "agent_insights": None,
            "integration_score": 0.0,
            "recommendations": []
        }
        
        try:
            # 1. Core quality scoring
            quality_score = await self.quality_scorer.score_pattern_quality(pattern, context)
            analysis_results["quality_score"] = quality_score
            
            # 2. Memory correctness validation
            if include_memory_check:
                memory_check = await self._validate_memory_correctness(pattern, quality_score)
                analysis_results["memory_correctness"] = memory_check
                self._integration_stats["memory_correctness_checks"] += 1
            
            # 3. Security framework validation  
            if include_security_validation:
                security_result = await self._validate_security_compliance(pattern, context)
                analysis_results["security_validation"] = security_result
                self._integration_stats["security_validations"] += 1
            
            # 4. Agent learning system integration
            if include_agent_learning:
                agent_insights = await self._update_agent_learning(pattern, quality_score, context)
                analysis_results["agent_insights"] = agent_insights
                self._integration_stats["agent_learning_updates"] += 1
            
            # 5. Calculate integration score
            analysis_results["integration_score"] = await self._calculate_integration_score(
                analysis_results
            )
            
            # 6. Generate integrated recommendations
            analysis_results["recommendations"] = await self._generate_integrated_recommendations(
                analysis_results, pattern, context
            )
            
            # 7. Store integration results
            await self._store_integration_results(analysis_results)
            
            logger.info("Integrated pattern analysis completed",
                       pattern_id=str(pattern.id),
                       integration_score=analysis_results["integration_score"],
                       recommendations_count=len(analysis_results["recommendations"]))
            
            return analysis_results
            
        except Exception as e:
            logger.error("Failed integrated pattern analysis", 
                        pattern_id=str(pattern.id), 
                        error=str(e))
            raise
    
    async def _validate_memory_correctness(
        self, 
        pattern: KnowledgeItem, 
        quality_score: QualityScore
    ) -> Dict[str, Any]:
        """
        Validate pattern against memory correctness system
        
        Checks if the pattern maintains consistency with existing knowledge
        and identifies potential conflicts or redundancies
        """
        try:
            # Create memory correctness check
            check_data = {
                "content": pattern.content,
                "title": pattern.title,
                "knowledge_type": pattern.knowledge_type.value if hasattr(pattern, 'knowledge_type') else 'pattern',
                "tags": pattern.tags,
                "metadata": {
                    "quality_score": quality_score.overall_score,
                    "pattern_id": str(pattern.id),
                    "source_credibility": quality_score.source_credibility.score
                }
            }
            
            # Run memory correctness validation
            correctness_result = await self.memory_correctness.validate_knowledge_item(
                check_data, pattern.session_id if hasattr(pattern, 'session_id') else None
            )
            
            # Enhance with pattern-specific checks
            pattern_consistency = await self._check_pattern_consistency(pattern, quality_score)
            
            return {
                "correctness_level": correctness_result.get("correctness_level", "unknown"),
                "confidence_score": correctness_result.get("confidence_score", 0.5),
                "consistency_issues": correctness_result.get("issues", []),
                "pattern_consistency": pattern_consistency,
                "memory_conflicts": correctness_result.get("conflicts", []),
                "redundancy_score": correctness_result.get("redundancy_score", 0.0),
                "validation_timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Memory correctness validation failed", 
                        pattern_id=str(pattern.id), 
                        error=str(e))
            return {
                "correctness_level": "error",
                "error": str(e),
                "validation_timestamp": datetime.utcnow()
            }
    
    async def _validate_security_compliance(
        self, 
        pattern: KnowledgeItem, 
        context: PatternContext
    ) -> Dict[str, Any]:
        """
        Validate pattern using security framework
        
        Comprehensive security analysis including vulnerability detection,
        compliance checking, and security best practice validation
        """
        try:
            # Prepare security analysis request
            security_data = {
                "content": pattern.content,
                "context": context.dict(),
                "metadata": {
                    "pattern_id": str(pattern.id),
                    "title": pattern.title,
                    "tags": pattern.tags
                }
            }
            
            # Run security framework analysis
            security_result = await self.security.analyze_pattern_security(
                pattern.content, 
                security_data
            )
            
            # Enhanced security checks specific to patterns
            vulnerability_scan = await self._scan_for_vulnerabilities(pattern)
            compliance_check = await self._check_compliance_requirements(pattern, context)
            
            return {
                "security_score": security_result.get("security_score", 0.5),
                "vulnerability_count": security_result.get("vulnerability_count", 0),
                "high_risk_issues": security_result.get("high_risk_issues", []),
                "compliance_status": compliance_check,
                "owasp_compliance": security_result.get("owasp_compliance", {}),
                "security_recommendations": security_result.get("recommendations", []),
                "vulnerability_details": vulnerability_scan,
                "validation_timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Security validation failed", 
                        pattern_id=str(pattern.id), 
                        error=str(e))
            return {
                "security_score": 0.0,
                "error": str(e),
                "validation_timestamp": datetime.utcnow()
            }
    
    async def _update_agent_learning(
        self, 
        pattern: KnowledgeItem, 
        quality_score: QualityScore,
        context: PatternContext
    ) -> Dict[str, Any]:
        """
        Update agent learning system with pattern analysis results
        
        Feeds pattern quality insights back into the agent learning engine
        to improve future recommendations and decision-making
        """
        try:
            # Prepare learning data
            learning_data = {
                "pattern_id": str(pattern.id),
                "quality_metrics": {
                    "overall_score": quality_score.overall_score,
                    "technical_accuracy": quality_score.technical_accuracy.score,
                    "source_credibility": quality_score.source_credibility.score,
                    "practical_utility": quality_score.practical_utility.score,
                    "completeness": quality_score.completeness.score
                },
                "success_prediction": {
                    "probability": quality_score.success_probability.value,
                    "percentage": quality_score.success_percentage,
                    "risk_level": quality_score.risk_level.value
                },
                "context": context.dict(),
                "timestamp": datetime.utcnow()
            }
            
            # Update agent learning models
            learning_result = await self.agent_learning.update_pattern_insights(
                learning_data, pattern
            )
            
            # Generate agent insights
            insights = await self._generate_agent_insights(pattern, quality_score, learning_result)
            
            return {
                "learning_update_success": learning_result.get("success", False),
                "model_improvements": learning_result.get("improvements", []),
                "pattern_insights": insights,
                "recommendation_adjustments": learning_result.get("adjustments", []),
                "learning_confidence": learning_result.get("confidence", 0.5),
                "update_timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Agent learning update failed", 
                        pattern_id=str(pattern.id), 
                        error=str(e))
            return {
                "learning_update_success": False,
                "error": str(e),
                "update_timestamp": datetime.utcnow()
            }
    
    async def _calculate_integration_score(self, analysis_results: Dict[str, Any]) -> float:
        """
        Calculate overall integration score based on all system results
        
        Combines quality score, memory correctness, security validation,
        and agent insights into a unified integration score
        """
        try:
            scores = []
            weights = []
            
            # Quality score (40% weight)
            if analysis_results.get("quality_score"):
                scores.append(analysis_results["quality_score"].overall_score)
                weights.append(0.40)
            
            # Memory correctness (25% weight)
            if analysis_results.get("memory_correctness"):
                memory_score = self._normalize_memory_correctness_score(
                    analysis_results["memory_correctness"]
                )
                scores.append(memory_score)
                weights.append(0.25)
            
            # Security validation (25% weight)  
            if analysis_results.get("security_validation"):
                security_score = analysis_results["security_validation"].get("security_score", 0.5)
                scores.append(security_score)
                weights.append(0.25)
            
            # Agent insights (10% weight)
            if analysis_results.get("agent_insights"):
                agent_score = analysis_results["agent_insights"].get("learning_confidence", 0.5)
                scores.append(agent_score)
                weights.append(0.10)
            
            # Calculate weighted average
            if scores:
                total_weight = sum(weights)
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                return weighted_sum / total_weight
            
            return 0.0
            
        except Exception as e:
            logger.error("Failed to calculate integration score", error=str(e))
            return 0.0
    
    async def _generate_integrated_recommendations(
        self, 
        analysis_results: Dict[str, Any],
        pattern: KnowledgeItem,
        context: PatternContext
    ) -> List[Dict[str, Any]]:
        """
        Generate integrated recommendations based on all system analyses
        """
        recommendations = []
        
        try:
            # Quality-based recommendations
            quality_score = analysis_results.get("quality_score")
            if quality_score:
                if quality_score.overall_score < 0.6:
                    recommendations.append({
                        "type": "quality_improvement",
                        "priority": "high",
                        "message": "Pattern quality score is below threshold. Consider improving technical accuracy and documentation.",
                        "specific_areas": self._identify_weak_quality_dimensions(quality_score)
                    })
            
            # Memory correctness recommendations
            memory_check = analysis_results.get("memory_correctness")
            if memory_check and memory_check.get("consistency_issues"):
                recommendations.append({
                    "type": "memory_correctness",
                    "priority": "medium",
                    "message": "Pattern has memory consistency issues that should be addressed.",
                    "issues": memory_check["consistency_issues"]
                })
            
            # Security recommendations
            security_result = analysis_results.get("security_validation")
            if security_result and security_result.get("high_risk_issues"):
                recommendations.append({
                    "type": "security_risk",
                    "priority": "critical",
                    "message": "Pattern contains high-risk security issues that must be resolved.",
                    "issues": security_result["high_risk_issues"],
                    "recommendations": security_result.get("security_recommendations", [])
                })
            
            # Integration-specific recommendations
            integration_score = analysis_results.get("integration_score", 0.0)
            if integration_score < 0.7:
                recommendations.append({
                    "type": "integration_improvement",
                    "priority": "medium", 
                    "message": "Pattern integration score suggests improvement opportunities across multiple dimensions.",
                    "focus_areas": self._identify_integration_improvement_areas(analysis_results)
                })
            
        except Exception as e:
            logger.error("Failed to generate integrated recommendations", error=str(e))
        
        return recommendations
    
    async def _store_integration_results(self, analysis_results: Dict[str, Any]) -> None:
        """Store integration analysis results in database"""
        try:
            async with self.db_manager.get_postgres_session() as session:
                # Store in integration_analyses table (would need schema)
                query = """
                INSERT INTO integration_analyses (
                    pattern_id, analysis_timestamp, quality_score_id, 
                    integration_score, memory_correctness_result,
                    security_validation_result, agent_insights,
                    recommendations, metadata
                ) VALUES (
                    :pattern_id, :timestamp, :quality_score_id,
                    :integration_score, :memory_result, :security_result,
                    :agent_insights, :recommendations, :metadata
                )
                """
                
                await session.execute(query, {
                    'pattern_id': analysis_results["pattern_id"],
                    'timestamp': analysis_results["analysis_timestamp"],
                    'quality_score_id': analysis_results.get("quality_score", {}).get("id"),
                    'integration_score': analysis_results["integration_score"],
                    'memory_result': str(analysis_results.get("memory_correctness", {})),
                    'security_result': str(analysis_results.get("security_validation", {})),
                    'agent_insights': str(analysis_results.get("agent_insights", {})),
                    'recommendations': str(analysis_results["recommendations"]),
                    'metadata': str({"stats": self._integration_stats})
                })
                
        except Exception as e:
            logger.error("Failed to store integration results", error=str(e))
    
    # Helper methods
    async def _check_pattern_consistency(self, pattern: KnowledgeItem, quality_score: QualityScore) -> Dict[str, Any]:
        """Check pattern consistency with existing knowledge base"""
        # Placeholder implementation
        return {
            "consistency_score": 0.8,
            "conflicts": [],
            "redundancies": []
        }
    
    async def _scan_for_vulnerabilities(self, pattern: KnowledgeItem) -> List[Dict[str, Any]]:
        """Scan pattern for security vulnerabilities"""
        # Placeholder implementation
        return []
    
    async def _check_compliance_requirements(self, pattern: KnowledgeItem, context: PatternContext) -> Dict[str, Any]:
        """Check pattern against compliance requirements"""
        # Placeholder implementation
        return {"compliant": True, "violations": []}
    
    async def _generate_agent_insights(self, pattern: KnowledgeItem, quality_score: QualityScore, learning_result: Dict) -> List[str]:
        """Generate insights from agent learning system"""
        insights = []
        
        if quality_score.overall_score > 0.8:
            insights.append("High-quality pattern suitable for recommendation to similar contexts")
        
        if quality_score.success_probability.value in ['high', 'very_high']:
            insights.append("Pattern shows high success probability based on historical data")
        
        return insights
    
    def _normalize_memory_correctness_score(self, memory_result: Dict[str, Any]) -> float:
        """Normalize memory correctness result to 0-1 score"""
        correctness_level = memory_result.get("correctness_level", "unknown")
        
        score_map = {
            "high": 0.9,
            "medium": 0.7, 
            "low": 0.4,
            "error": 0.1,
            "unknown": 0.5
        }
        
        base_score = score_map.get(correctness_level, 0.5)
        
        # Adjust based on confidence
        confidence = memory_result.get("confidence_score", 0.5)
        return base_score * confidence
    
    def _identify_weak_quality_dimensions(self, quality_score: QualityScore) -> List[str]:
        """Identify quality dimensions that need improvement"""
        weak_areas = []
        
        if quality_score.technical_accuracy.score < 0.6:
            weak_areas.append("technical_accuracy")
        if quality_score.source_credibility.score < 0.6:
            weak_areas.append("source_credibility")
        if quality_score.practical_utility.score < 0.6:
            weak_areas.append("practical_utility")
        if quality_score.completeness.score < 0.6:
            weak_areas.append("completeness")
        
        return weak_areas
    
    def _identify_integration_improvement_areas(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Identify areas where integration can be improved"""
        improvement_areas = []
        
        if analysis_results.get("memory_correctness", {}).get("consistency_issues"):
            improvement_areas.append("memory_consistency")
        
        if analysis_results.get("security_validation", {}).get("security_score", 1.0) < 0.7:
            improvement_areas.append("security_compliance")
        
        quality_score = analysis_results.get("quality_score")
        if quality_score and quality_score.overall_score < 0.7:
            improvement_areas.append("overall_quality")
        
        return improvement_areas
    
    async def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration service statistics"""
        return {
            "integration_stats": self._integration_stats.copy(),
            "active_integrations": len([
                service for service in [
                    self.memory_correctness,
                    self.agent_learning, 
                    self.security
                ] if service is not None
            ]),
            "last_updated": datetime.utcnow()
        }