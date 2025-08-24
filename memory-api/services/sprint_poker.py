# ABOUTME: AI Sprint Poker Engine for Enhanced Task Management System
# ABOUTME: Provides intelligent task complexity estimation using ML and historical data analysis

import asyncio
import json
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import structlog
import re

from core.database import DatabaseManager

logger = structlog.get_logger(__name__)

class SprintPokerEngine:
    """
    AI-powered Sprint Poker estimation engine
    Uses historical data, complexity analysis, and ML models for accurate estimation
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Fibonacci sequence for story points (standard Sprint Poker)
        self.fibonacci_sequence = [1, 2, 3, 5, 8, 13, 21]
        
        # Complexity factor weights (can be tuned based on historical accuracy)
        self.complexity_weights = {
            "code_footprint_score": 0.25,
            "integration_complexity": 0.20,
            "testing_complexity": 0.15,
            "uncertainty_factor": 0.15,
            "technical_debt_impact": 0.15,
            "domain_familiarity": 0.10
        }
        
        # Technology complexity modifiers
        self.tech_complexity_modifiers = {
            "Python": 0.8,
            "JavaScript": 0.9,
            "TypeScript": 1.0,
            "React": 1.1,
            "FastAPI": 0.9,
            "PostgreSQL": 1.0,
            "Docker": 1.2,
            "Kubernetes": 1.4,
            "Machine Learning": 1.5,
            "AI": 1.6
        }
    
    async def analyze_complexity(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive complexity analysis for a task
        """
        try:
            title = task_data.get("title", "")
            description = task_data.get("description", "")
            task_type = task_data.get("task_type", "feature")
            
            # Analyze text complexity
            text_complexity = self._analyze_text_complexity(title, description)
            
            # Analyze domain complexity
            domain_complexity = await self._analyze_domain_complexity(task_data)
            
            # Analyze technical complexity
            tech_complexity = self._analyze_technical_complexity(title, description)
            
            # Calculate individual complexity factors
            complexity_factors = {
                "code_footprint_score": self._calculate_code_footprint_score(
                    title, description, task_type
                ),
                "integration_complexity": self._calculate_integration_complexity(
                    title, description, tech_complexity
                ),
                "testing_complexity": self._calculate_testing_complexity(
                    title, description, task_type
                ),
                "uncertainty_factor": self._calculate_uncertainty_factor(
                    title, description, text_complexity
                ),
                "technical_debt_impact": self._calculate_technical_debt_impact(
                    title, description, task_type
                ),
                "domain_familiarity": domain_complexity
            }
            
            # Calculate overall complexity using weighted sum
            overall_complexity_raw = sum(
                factor * self.complexity_weights[name]
                for name, factor in complexity_factors.items()
            )
            
            # Map to Fibonacci sequence (1-13 scale)
            overall_complexity = self._map_to_fibonacci(overall_complexity_raw)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                complexity_factors, title, description
            )
            
            # Generate analysis insights
            insights = self._generate_complexity_insights(
                complexity_factors, overall_complexity, risk_factors
            )
            
            logger.info(
                "Complexity analysis completed",
                task_id=task_data.get("id"),
                overall_complexity=overall_complexity,
                risk_count=len(risk_factors)
            )
            
            return {
                "overall_complexity": overall_complexity,
                "complexity_factors": complexity_factors,
                "risk_factors": risk_factors,
                "insights": insights,
                "confidence_score": self._calculate_analysis_confidence(
                    complexity_factors, text_complexity
                ),
                "analysis_metadata": {
                    "text_complexity": text_complexity,
                    "tech_complexity": tech_complexity,
                    "domain_complexity": domain_complexity,
                    "analyzed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(
                "Failed to analyze task complexity",
                task_id=task_data.get("id"),
                error=str(e)
            )
            # Return default complexity analysis
            return {
                "overall_complexity": 5,
                "complexity_factors": {
                    "code_footprint_score": 3,
                    "integration_complexity": 3,
                    "testing_complexity": 3,
                    "uncertainty_factor": 3,
                    "technical_debt_impact": 3,
                    "domain_familiarity": 3
                },
                "risk_factors": ["Analysis failed - manual review needed"],
                "insights": ["Automated analysis failed, manual estimation recommended"],
                "confidence_score": 0.3,
                "analysis_metadata": {
                    "error": str(e),
                    "analyzed_at": datetime.now().isoformat()
                }
            }
    
    async def estimate_story_points(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate story points based on complexity analysis
        """
        try:
            overall_complexity = complexity_analysis["overall_complexity"]
            complexity_factors = complexity_analysis["complexity_factors"]
            risk_factors = complexity_analysis["risk_factors"]
            
            # Base story points from Fibonacci sequence
            base_story_points = overall_complexity
            
            # Apply risk adjustments
            risk_multiplier = self._calculate_risk_multiplier(risk_factors)
            adjusted_story_points = base_story_points * risk_multiplier
            
            # Map back to Fibonacci sequence
            final_story_points = self._map_to_fibonacci(adjusted_story_points)
            
            # Calculate time estimates
            time_estimates = self._calculate_time_estimates(
                final_story_points, complexity_factors, risk_factors
            )
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                final_story_points, complexity_analysis["confidence_score"]
            )
            
            # Generate recommendations
            recommendations = self._generate_story_point_recommendations(
                final_story_points, complexity_factors, risk_factors
            )
            
            logger.info(
                "Story points estimated",
                overall_complexity=overall_complexity,
                story_points=final_story_points,
                estimated_hours=time_estimates["estimated_hours"]
            )
            
            return {
                "story_points": final_story_points,
                "base_complexity": base_story_points,
                "risk_adjustment": risk_multiplier,
                "estimated_hours": time_estimates["estimated_hours"],
                "time_estimates": time_estimates,
                "confidence_interval": confidence_interval,
                "recommendations": recommendations,
                "estimation_rationale": {
                    "base_factors": complexity_factors,
                    "risk_factors": risk_factors,
                    "adjustments_applied": risk_multiplier != 1.0
                }
            }
            
        except Exception as e:
            logger.error(
                "Failed to estimate story points",
                error=str(e)
            )
            return {
                "story_points": 5,
                "estimated_hours": 8,
                "confidence_interval": {"min_hours": 4, "max_hours": 16, "p90_hours": 12},
                "recommendations": ["Manual estimation recommended due to analysis error"],
                "error": str(e)
            }
    
    async def find_similar_tasks(
        self,
        task_data: Dict[str, Any],
        include_analysis: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar completed tasks for comparison and learning
        """
        try:
            title = task_data.get("title", "")
            description = task_data.get("description", "")
            task_type = task_data.get("task_type", "feature")
            project_id = task_data.get("project_id")
            
            # Get completed tasks with actual metrics
            async with self.db_manager.get_postgres_session() as session:
                query = """
                    SELECT et.id, et.title, et.description, et.task_type,
                           et.story_points, et.estimated_cost, et.actual_cost,
                           et.complexity_score, et.confidence_level,
                           te.time_estimates, te.actual_values,
                           et.created_at, et.completed_at
                    FROM enhanced_tasks et
                    LEFT JOIN task_estimates te ON et.id = te.task_id
                    WHERE et.status = 'completed' 
                      AND et.story_points IS NOT NULL
                      AND et.actual_cost IS NOT NULL
                      AND (et.project_id = $1 OR et.project_id != $1)  -- Include cross-project learning
                    ORDER BY et.completed_at DESC
                    LIMIT 100
                """
                
                result = await session.execute(query, project_id)
                completed_tasks = [dict(row._mapping) for row in result.fetchall()]
            
            # Calculate similarity scores
            similar_tasks = []
            for completed_task in completed_tasks:
                similarity_score = self._calculate_task_similarity(
                    task_data, completed_task
                )
                
                if similarity_score > 0.3:  # Minimum similarity threshold
                    similar_task = {
                        "task_id": completed_task["id"],
                        "title": completed_task["title"],
                        "task_type": completed_task["task_type"],
                        "similarity_score": similarity_score,
                        "story_points": completed_task["story_points"],
                        "estimated_cost": float(completed_task["estimated_cost"] or 0),
                        "actual_cost": float(completed_task["actual_cost"] or 0),
                        "complexity_score": completed_task["complexity_score"],
                        "comparison_factors": self._get_comparison_factors(
                            task_data, completed_task
                        )
                    }
                    
                    if include_analysis and completed_task["actual_values"]:
                        try:
                            actual_values = json.loads(completed_task["actual_values"])
                            similar_task["actual_metrics"] = actual_values
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    similar_tasks.append(similar_task)
            
            # Sort by similarity score and limit results
            similar_tasks.sort(key=lambda x: x["similarity_score"], reverse=True)
            similar_tasks = similar_tasks[:limit]
            
            logger.info(
                "Similar tasks found",
                task_id=task_data.get("id"),
                similar_count=len(similar_tasks),
                top_similarity=similar_tasks[0]["similarity_score"] if similar_tasks else 0
            )
            
            return similar_tasks
            
        except Exception as e:
            logger.error(
                "Failed to find similar tasks",
                task_id=task_data.get("id"),
                error=str(e)
            )
            return []
    
    async def calculate_confidence(
        self,
        task_data: Dict[str, Any],
        complexity_analysis: Dict[str, Any],
        similar_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate confidence metrics for the estimation
        """
        try:
            # Base confidence from complexity analysis
            analysis_confidence = complexity_analysis.get("confidence_score", 0.5)
            
            # Historical data confidence
            historical_confidence = self._calculate_historical_confidence(similar_tasks)
            
            # Domain expertise confidence
            domain_confidence = await self._calculate_domain_confidence(task_data)
            
            # Uncertainty factors
            uncertainty_score = complexity_analysis["complexity_factors"].get(
                "uncertainty_factor", 3
            ) / 5.0  # Normalize to 0-1
            
            # Combined confidence calculation
            weights = {
                "analysis": 0.4,
                "historical": 0.3,
                "domain": 0.2,
                "uncertainty": 0.1
            }
            
            overall_confidence = (
                analysis_confidence * weights["analysis"] +
                historical_confidence * weights["historical"] +
                domain_confidence * weights["domain"] +
                (1.0 - uncertainty_score) * weights["uncertainty"]
            )
            
            # Estimation reliability (how reliable are our estimates generally)
            estimation_reliability = await self._calculate_estimation_reliability()
            
            # Model accuracy (how accurate is our complexity model)
            model_accuracy = await self._calculate_model_accuracy()
            
            logger.info(
                "Confidence metrics calculated",
                task_id=task_data.get("id"),
                overall_confidence=overall_confidence,
                estimation_reliability=estimation_reliability
            )
            
            return {
                "overall_confidence": overall_confidence,
                "estimation_reliability": estimation_reliability,
                "model_accuracy": model_accuracy,
                "confidence_breakdown": {
                    "analysis_confidence": analysis_confidence,
                    "historical_confidence": historical_confidence,
                    "domain_confidence": domain_confidence,
                    "uncertainty_impact": uncertainty_score
                },
                "confidence_level": self._categorize_confidence(overall_confidence),
                "recommendations": self._generate_confidence_recommendations(
                    overall_confidence, historical_confidence, uncertainty_score
                )
            }
            
        except Exception as e:
            logger.error(
                "Failed to calculate confidence metrics",
                task_id=task_data.get("id"),
                error=str(e)
            )
            return {
                "overall_confidence": 0.5,
                "estimation_reliability": 0.5,
                "model_accuracy": 0.5,
                "confidence_level": "medium",
                "error": str(e)
            }
    
    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================
    
    def _analyze_text_complexity(self, title: str, description: str) -> Dict[str, Any]:
        """Analyze text complexity using various metrics"""
        combined_text = f"{title} {description or ''}"
        
        return {
            "word_count": len(combined_text.split()),
            "sentence_count": len(re.split(r'[.!?]+', combined_text)),
            "technical_terms": len(re.findall(r'\b(?:API|database|server|frontend|backend|authentication|authorization|integration|algorithm|optimization|performance|security|validation|configuration|deployment|migration|refactor|architecture)\b', combined_text.lower())),
            "uncertainty_indicators": len(re.findall(r'\b(?:maybe|perhaps|might|could|should|unclear|unknown|investigate|explore|research|figure out)\b', combined_text.lower())),
            "complexity_indicators": len(re.findall(r'\b(?:complex|complicated|advanced|sophisticated|challenging|difficult|tricky|intricate)\b', combined_text.lower()))
        }
    
    async def _analyze_domain_complexity(self, task_data: Dict[str, Any]) -> float:
        """Analyze domain-specific complexity based on historical data"""
        try:
            task_type = task_data.get("task_type", "feature")
            project_id = task_data.get("project_id")
            
            # Get average complexity for similar tasks in this domain
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(
                    """
                    SELECT AVG(complexity_score) as avg_complexity,
                           COUNT(*) as task_count
                    FROM enhanced_tasks
                    WHERE task_type = $1 AND project_id = $2 AND complexity_score IS NOT NULL
                    """,
                    task_type, project_id
                )
                
                row = result.fetchone()
                if row and row[1] > 0:  # task_count > 0
                    avg_complexity = float(row[0] or 3.0)
                    # Normalize to 1-5 scale
                    return min(5.0, max(1.0, avg_complexity / 13.0 * 5.0))
                else:
                    return 3.0  # Default medium complexity
                    
        except Exception:
            return 3.0  # Default on error
    
    def _analyze_technical_complexity(self, title: str, description: str) -> Dict[str, float]:
        """Analyze technical complexity based on mentioned technologies"""
        combined_text = f"{title} {description or ''}".lower()
        
        tech_scores = {}
        for tech, complexity_modifier in self.tech_complexity_modifiers.items():
            if tech.lower() in combined_text:
                tech_scores[tech] = complexity_modifier
        
        return tech_scores
    
    def _calculate_code_footprint_score(self, title: str, description: str, task_type: str) -> int:
        """Calculate expected code footprint (1-5 scale)"""
        combined_text = f"{title} {description or ''}".lower()
        
        # Base score by task type
        type_scores = {
            "feature": 3,
            "enhancement": 2,
            "bug": 2,
            "refactor": 4,
            "test": 2,
            "docs": 1
        }
        
        base_score = type_scores.get(task_type, 3)
        
        # Adjust based on scope indicators
        scope_keywords = {
            "small": -1, "minor": -1, "quick": -1, "simple": -1,
            "large": +2, "major": +2, "complex": +2, "comprehensive": +2,
            "system": +1, "architecture": +2, "framework": +2,
            "database": +1, "api": +1, "frontend": +1, "backend": +1
        }
        
        score_adjustment = 0
        for keyword, adjustment in scope_keywords.items():
            if keyword in combined_text:
                score_adjustment += adjustment
        
        return max(1, min(5, base_score + score_adjustment))
    
    def _calculate_integration_complexity(self, title: str, description: str, tech_complexity: Dict[str, float]) -> int:
        """Calculate integration complexity (1-5 scale)"""
        combined_text = f"{title} {description or ''}".lower()
        
        # Base score from number of technologies involved
        base_score = min(5, max(1, len(tech_complexity)))
        
        # Integration keywords
        integration_keywords = [
            "integrate", "connect", "sync", "api", "webhook", "microservice",
            "database", "external", "third-party", "service", "endpoint"
        ]
        
        integration_mentions = sum(1 for keyword in integration_keywords if keyword in combined_text)
        
        # Average technology complexity
        avg_tech_complexity = sum(tech_complexity.values()) / len(tech_complexity) if tech_complexity else 1.0
        
        # Calculate final score
        final_score = base_score + (integration_mentions * 0.5) + (avg_tech_complexity - 1.0)
        
        return max(1, min(5, round(final_score)))
    
    def _calculate_testing_complexity(self, title: str, description: str, task_type: str) -> int:
        """Calculate testing complexity (1-5 scale)"""
        combined_text = f"{title} {description or ''}".lower()
        
        # Base complexity by task type
        type_complexity = {
            "feature": 3,
            "enhancement": 2,
            "bug": 4,  # Bugs often need regression testing
            "refactor": 3,
            "test": 1,  # Test tasks have low testing complexity
            "docs": 1
        }
        
        base_score = type_complexity.get(task_type, 3)
        
        # Testing-related keywords
        testing_keywords = {
            "unit test": +1, "integration test": +2, "e2e": +3,
            "mock": +1, "validation": +1, "security": +2,
            "performance": +2, "load test": +3, "edge case": +1
        }
        
        adjustment = 0
        for keyword, value in testing_keywords.items():
            if keyword in combined_text:
                adjustment += value
        
        return max(1, min(5, base_score + min(adjustment, 2)))
    
    def _calculate_uncertainty_factor(self, title: str, description: str, text_complexity: Dict[str, Any]) -> int:
        """Calculate uncertainty factor (1-5 scale, higher = more uncertain)"""
        # Base uncertainty from text analysis
        uncertainty_indicators = text_complexity.get("uncertainty_indicators", 0)
        
        # Lack of description increases uncertainty
        description_penalty = 1 if not description or len(description.strip()) < 20 else 0
        
        # Vague language indicators
        vague_keywords = ["somehow", "something", "various", "multiple", "several", "different", "flexible", "configurable", "dynamic"]
        combined_text = f"{title} {description or ''}".lower()
        vague_count = sum(1 for keyword in vague_keywords if keyword in combined_text)
        
        total_uncertainty = uncertainty_indicators + description_penalty + vague_count
        
        return max(1, min(5, 2 + total_uncertainty))
    
    def _calculate_technical_debt_impact(self, title: str, description: str, task_type: str) -> int:
        """Calculate technical debt impact (1-5 scale)"""
        combined_text = f"{title} {description or ''}".lower()
        
        # Debt reduction keywords
        debt_reduction = ["refactor", "cleanup", "optimize", "improve", "modernize", "upgrade"]
        debt_creation = ["hack", "workaround", "temporary", "quick fix", "patch"]
        
        reduction_score = sum(1 for keyword in debt_reduction if keyword in combined_text)
        creation_score = sum(1 for keyword in debt_creation if keyword in combined_text)
        
        # Task types that typically affect technical debt
        if task_type == "refactor":
            return max(1, 3 - reduction_score + creation_score)
        elif task_type == "bug":
            return max(1, min(5, 2 + creation_score))
        else:
            return max(1, min(5, 3 + creation_score - reduction_score))
    
    def _map_to_fibonacci(self, raw_score: float) -> int:
        """Map a raw complexity score to the Fibonacci sequence"""
        # Normalize raw score to 0-1 range if needed
        if raw_score > 5:
            normalized = raw_score / 13.0  # Assuming max raw score of 13
        else:
            normalized = raw_score / 5.0
        
        # Map to Fibonacci index
        fib_index = min(len(self.fibonacci_sequence) - 1, int(normalized * len(self.fibonacci_sequence)))
        
        return self.fibonacci_sequence[fib_index]
    
    def _identify_risk_factors(self, complexity_factors: Dict[str, int], title: str, description: str) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        combined_text = f"{title} {description or ''}".lower()
        
        # High complexity factors
        if complexity_factors["uncertainty_factor"] >= 4:
            risks.append("High uncertainty - requirements may need clarification")
        
        if complexity_factors["integration_complexity"] >= 4:
            risks.append("Complex integration - potential for compatibility issues")
        
        if complexity_factors["technical_debt_impact"] >= 4:
            risks.append("High technical debt impact - may affect system stability")
        
        if complexity_factors["testing_complexity"] >= 4:
            risks.append("Complex testing requirements - additional QA time needed")
        
        # Keyword-based risks
        risk_keywords = {
            "deadline": "Time pressure may affect quality",
            "urgent": "Urgency may lead to shortcuts",
            "external": "External dependencies may cause delays",
            "new": "New technology or approach - learning curve expected",
            "migration": "Data migration risks - backup and rollback plan needed",
            "breaking": "Breaking changes - extensive testing required"
        }
        
        for keyword, risk_description in risk_keywords.items():
            if keyword in combined_text:
                risks.append(risk_description)
        
        return risks
    
    def _generate_complexity_insights(self, complexity_factors: Dict[str, int], overall_complexity: int, risk_factors: List[str]) -> List[str]:
        """Generate insights about the complexity analysis"""
        insights = []
        
        # Overall complexity insights
        if overall_complexity <= 3:
            insights.append("This task appears to be relatively straightforward")
        elif overall_complexity <= 8:
            insights.append("This task has moderate complexity and may require careful planning")
        else:
            insights.append("This is a complex task that should be broken down into smaller subtasks")
        
        # Factor-specific insights
        highest_factor = max(complexity_factors.items(), key=lambda x: x[1])
        if highest_factor[1] >= 4:
            factor_insights = {
                "code_footprint_score": "Large code changes expected - consider code review strategy",
                "integration_complexity": "Multiple system integrations - plan for compatibility testing",
                "testing_complexity": "Extensive testing required - allocate additional QA time",
                "uncertainty_factor": "High uncertainty - consider spike tasks for exploration",
                "technical_debt_impact": "Significant technical debt impact - plan for follow-up cleanup",
                "domain_familiarity": "Unfamiliar domain - may need research or expert consultation"
            }
            
            if highest_factor[0] in factor_insights:
                insights.append(factor_insights[highest_factor[0]])
        
        # Risk-based insights
        if len(risk_factors) > 3:
            insights.append("Multiple risk factors identified - consider risk mitigation strategies")
        
        return insights
    
    def _calculate_analysis_confidence(self, complexity_factors: Dict[str, int], text_complexity: Dict[str, Any]) -> float:
        """Calculate confidence in the complexity analysis"""
        # Base confidence from text quality
        description_quality = min(1.0, text_complexity.get("word_count", 0) / 50.0)
        
        # Uncertainty penalty
        uncertainty_penalty = complexity_factors.get("uncertainty_factor", 3) / 5.0
        
        # Technical term density (indicates well-defined requirements)
        tech_density = min(1.0, text_complexity.get("technical_terms", 0) / 5.0)
        
        confidence = (description_quality * 0.4 + tech_density * 0.3 + (1 - uncertainty_penalty) * 0.3)
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_risk_multiplier(self, risk_factors: List[str]) -> float:
        """Calculate risk multiplier for story points"""
        if not risk_factors:
            return 1.0
        
        # Each risk factor adds 10% complexity
        risk_multiplier = 1.0 + (len(risk_factors) * 0.1)
        
        # Cap at 50% increase
        return min(1.5, risk_multiplier)
    
    def _calculate_time_estimates(self, story_points: int, complexity_factors: Dict[str, int], risk_factors: List[str]) -> Dict[str, float]:
        """Calculate time estimates based on story points"""
        # Base hours per story point (configurable)
        base_hours_per_point = 2.0
        
        # Adjust based on complexity factors
        complexity_multiplier = sum(complexity_factors.values()) / (len(complexity_factors) * 3.0)
        
        # Risk adjustment
        risk_multiplier = 1.0 + (len(risk_factors) * 0.15)
        
        estimated_hours = story_points * base_hours_per_point * complexity_multiplier * risk_multiplier
        
        return {
            "estimated_hours": estimated_hours,
            "min_hours": estimated_hours * 0.7,
            "max_hours": estimated_hours * 1.5,
            "p90_hours": estimated_hours * 1.3
        }
    
    def _calculate_confidence_interval(self, story_points: int, confidence_score: float) -> Dict[str, float]:
        """Calculate confidence interval for estimates"""
        base_hours = story_points * 2.0
        
        # Wider interval for lower confidence
        uncertainty_factor = 1.0 - confidence_score
        
        return {
            "min_hours": base_hours * (1.0 - uncertainty_factor * 0.5),
            "max_hours": base_hours * (1.0 + uncertainty_factor * 0.7),
            "p90_hours": base_hours * (1.0 + uncertainty_factor * 0.4)
        }
    
    def _generate_story_point_recommendations(self, story_points: int, complexity_factors: Dict[str, int], risk_factors: List[str]) -> List[str]:
        """Generate recommendations based on story point estimation"""
        recommendations = []
        
        if story_points >= 8:
            recommendations.append("Consider breaking this task into smaller subtasks")
        
        if story_points >= 13:
            recommendations.append("This task is likely too large for a single sprint")
        
        if len(risk_factors) > 2:
            recommendations.append("Plan risk mitigation strategies before starting")
        
        highest_complexity = max(complexity_factors.values())
        if highest_complexity >= 4:
            recommendations.append("Schedule additional code review and testing time")
        
        return recommendations
    
    def _calculate_task_similarity(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> float:
        """Calculate similarity score between two tasks"""
        similarity_score = 0.0
        
        # Title similarity (basic keyword matching)
        title1_words = set(task1.get("title", "").lower().split())
        title2_words = set(task2.get("title", "").lower().split())
        if title1_words and title2_words:
            title_similarity = len(title1_words & title2_words) / len(title1_words | title2_words)
            similarity_score += title_similarity * 0.4
        
        # Task type match
        if task1.get("task_type") == task2.get("task_type"):
            similarity_score += 0.3
        
        # Complexity similarity
        complexity1 = task1.get("complexity_score", 5)
        complexity2 = task2.get("complexity_score", 5)
        if complexity1 and complexity2:
            complexity_similarity = 1.0 - abs(complexity1 - complexity2) / 13.0
            similarity_score += complexity_similarity * 0.3
        
        return similarity_score
    
    def _get_comparison_factors(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> List[str]:
        """Get factors that make tasks comparable"""
        factors = []
        
        if task1.get("task_type") == task2.get("task_type"):
            factors.append(f"Same task type: {task1.get('task_type')}")
        
        # Add more comparison logic here
        
        return factors
    
    def _calculate_historical_confidence(self, similar_tasks: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on historical data availability"""
        if not similar_tasks:
            return 0.3
        
        # More similar tasks = higher confidence
        task_count_factor = min(1.0, len(similar_tasks) / 5.0)
        
        # Higher similarity scores = higher confidence
        avg_similarity = sum(task["similarity_score"] for task in similar_tasks) / len(similar_tasks)
        
        return (task_count_factor * 0.6 + avg_similarity * 0.4)
    
    async def _calculate_domain_confidence(self, task_data: Dict[str, Any]) -> float:
        """Calculate confidence based on domain expertise"""
        try:
            project_id = task_data.get("project_id")
            task_type = task_data.get("task_type")
            
            async with self.db_manager.get_postgres_session() as session:
                # Count similar tasks completed in this project/domain
                result = await session.execute(
                    """
                    SELECT COUNT(*) as completed_count
                    FROM enhanced_tasks
                    WHERE project_id = $1 AND task_type = $2 AND status = 'completed'
                    """,
                    project_id, task_type
                )
                
                count = result.scalar() or 0
                
                # More experience = higher confidence
                return min(1.0, count / 10.0)
                
        except Exception:
            return 0.5
    
    async def _calculate_estimation_reliability(self) -> float:
        """Calculate how reliable our estimations are generally"""
        try:
            async with self.db_manager.get_postgres_session() as session:
                # Get estimation accuracy from completed tasks
                result = await session.execute(
                    """
                    SELECT AVG(accuracy_score) as avg_accuracy
                    FROM task_estimates te
                    JOIN enhanced_tasks et ON te.task_id = et.id
                    WHERE et.status = 'completed' AND te.accuracy_score IS NOT NULL
                    """
                )
                
                avg_accuracy = result.scalar()
                return avg_accuracy if avg_accuracy is not None else 0.75
                
        except Exception:
            return 0.75  # Default assumption
    
    async def _calculate_model_accuracy(self) -> float:
        """Calculate accuracy of our complexity model"""
        # This would analyze prediction vs actual performance
        # For now, return a default value
        return 0.8
    
    def _categorize_confidence(self, confidence_score: float) -> str:
        """Categorize confidence score into levels"""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "medium"
        elif confidence_score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def _generate_confidence_recommendations(self, overall_confidence: float, historical_confidence: float, uncertainty_score: float) -> List[str]:
        """Generate recommendations based on confidence levels"""
        recommendations = []
        
        if overall_confidence < 0.5:
            recommendations.append("Low confidence - consider manual review and adjustment")
        
        if historical_confidence < 0.4:
            recommendations.append("Limited historical data - estimates may be less accurate")
        
        if uncertainty_score > 0.7:
            recommendations.append("High uncertainty - consider breaking down requirements further")
        
        return recommendations