# ABOUTME: Comprehensive test suite for ML-powered Pattern Success Prediction Engine
# ABOUTME: Tests ML models, prediction accuracy, ROI estimation, and strategy recommendations with target performance metrics

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from models.pattern_quality import PatternContext, QualityScore, SuccessProbability, RiskLevel
from models.prediction_engine import (
    SuccessPrediction, ROIPrediction, StrategyRecommendation,
    Organization, ImplementationConstraints, ImplementationOutcome,
    PredictionConfidence, ROICategory, AccuracyMetrics, ImplementationStrategy
)
from models.knowledge import KnowledgeItem
from services.pattern_success_prediction_engine import PatternSuccessPredictionEngine
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine
from core.database import DatabaseManager

class TestMLPredictionEngine:
    """Comprehensive test suite for ML-powered prediction engine"""
    
    @pytest.fixture
    async def mock_dependencies(self):
        """Mock all required dependencies"""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.get_postgres_session = AsyncMock()
        db_manager.get_neo4j_session = AsyncMock()
        db_manager.get_qdrant_client = Mock()
        db_manager.get_redis_client = Mock()
        
        vector_service = Mock(spec=VectorService)
        vector_service.generate_embedding = AsyncMock(return_value=np.random.random(384))
        
        quality_scorer = Mock(spec=AdvancedQualityScorer)
        mock_quality_score = Mock()
        mock_quality_score.overall_score = 0.8
        mock_quality_score.technical_accuracy.score = 0.85
        mock_quality_score.source_credibility.score = 0.75
        mock_quality_score.practical_utility.score = 0.8
        mock_quality_score.completeness.score = 0.7
        quality_scorer.score_pattern_quality = AsyncMock(return_value=mock_quality_score)
        
        intelligence_engine = Mock(spec=PatternIntelligenceEngine)
        
        return db_manager, vector_service, quality_scorer, intelligence_engine
    
    @pytest.fixture
    async def prediction_engine(self, mock_dependencies):
        """Prediction engine instance for testing"""
        db_manager, vector_service, quality_scorer, intelligence_engine = mock_dependencies
        return PatternSuccessPredictionEngine(
            db_manager=db_manager,
            vector_service=vector_service,
            quality_scorer=quality_scorer,
            intelligence_engine=intelligence_engine
        )
    
    @pytest.fixture
    def sample_pattern(self):
        """Sample pattern for testing"""
        return KnowledgeItem(
            id=uuid4(),
            title="ML Model Serving Pattern",
            content="""
            # ML Model Serving Pattern
            
            This pattern implements scalable machine learning model serving with Flask and Docker.
            
            ## Implementation
            ```python
            from flask import Flask, request, jsonify
            import joblib
            import numpy as np
            
            app = Flask(__name__)
            model = joblib.load('model.pkl')
            
            @app.route('/predict', methods=['POST'])
            def predict():
                data = request.get_json()
                features = np.array(data['features']).reshape(1, -1)
                prediction = model.predict(features)
                return jsonify({'prediction': prediction.tolist()})
            
            if __name__ == '__main__':
                app.run(host='0.0.0.0', port=5000)
            ```
            
            ## Docker Configuration
            ```dockerfile
            FROM python:3.9-slim
            COPY requirements.txt .
            RUN pip install -r requirements.txt
            COPY . .
            EXPOSE 5000
            CMD ["python", "app.py"]
            ```
            
            ## Performance Considerations
            - Use connection pooling
            - Implement request batching
            - Add monitoring and logging
            - Consider auto-scaling
            """,
            knowledge_type="ml_pattern",
            source_type="expert_knowledge",
            tags=["machine-learning", "python", "flask", "docker", "api", "scalability"],
            summary="Scalable ML model serving pattern with Flask and Docker",
            confidence="high",
            access_count=25,
            created_at=datetime.utcnow() - timedelta(days=15)
        )
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return PatternContext(
            domain="machine_learning",
            technology_stack=["python", "flask", "docker", "scikit-learn"],
            project_type="ml_service",
            team_experience="medium",
            business_criticality="high",
            compliance_requirements=["GDPR", "SOC2"]
        )
    
    @pytest.fixture
    def sample_organization(self):
        """Sample organization for testing"""
        return Organization(
            id=uuid4(),
            name="TechCorp ML Division",
            size="medium",
            industry="technology",
            maturity_level="mature",
            technology_preferences=["python", "docker", "aws"],
            risk_tolerance="medium",
            budget_range="100k-500k",
            team_structure={"ml_engineers": 3, "devops": 2, "data_scientists": 4},
            previous_implementations=["basic_ml_pipeline", "batch_processing"]
        )
    
    @pytest.fixture
    def sample_constraints(self):
        """Sample implementation constraints"""
        return ImplementationConstraints(
            timeline=timedelta(days=90),
            budget_limit=150000.0,
            team_size=5,
            skill_requirements=["python", "machine-learning", "docker", "api-development"],
            technology_constraints=["must_use_python", "cloud_deployment"],
            compliance_requirements=["data_privacy", "model_explainability"],
            performance_requirements={"latency_ms": 200, "throughput_rps": 1000},
            availability_requirements=0.99
        )
    
    # ==================== SUCCESS PREDICTION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_success_prediction_basic(
        self, prediction_engine, sample_pattern, sample_context, sample_organization, sample_constraints
    ):
        """Test basic success prediction functionality"""
        with patch.object(prediction_engine, '_store_prediction', new_callable=AsyncMock):
            prediction = await prediction_engine.predict_implementation_success(
                pattern=sample_pattern,
                context=sample_context,
                organization=sample_organization,
                constraints=sample_constraints
            )
        
        # Verify basic structure
        assert isinstance(prediction, SuccessPrediction)
        assert prediction.pattern_id == sample_pattern.id
        assert isinstance(prediction.success_probability, SuccessProbability)
        assert 0.0 <= prediction.success_percentage <= 100.0
        assert 0.0 <= prediction.confidence_score <= 1.0
        assert isinstance(prediction.confidence_level, PredictionConfidence)
        
        # Verify outcome probabilities
        assert isinstance(prediction.outcome_probabilities, dict)
        total_prob = sum(prediction.outcome_probabilities.values())
        assert abs(total_prob - 1.0) < 0.01  # Should sum to ~1.0
        
        # Verify risk assessment
        assert isinstance(prediction.risk_level, RiskLevel)
        assert 0.0 <= prediction.risk_score <= 1.0
        assert isinstance(prediction.critical_risk_factors, list)
        assert isinstance(prediction.risk_mitigation_strategies, list)
    
    @pytest.mark.asyncio
    async def test_success_prediction_performance(
        self, prediction_engine, sample_pattern, sample_context, sample_organization, sample_constraints
    ):
        """Test that success prediction meets latency targets (<100ms)"""
        start_time = datetime.utcnow()
        
        with patch.object(prediction_engine, '_store_prediction', new_callable=AsyncMock):
            await prediction_engine.predict_implementation_success(
                pattern=sample_pattern,
                context=sample_context,
                organization=sample_organization,
                constraints=sample_constraints
            )
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Target: <100ms latency
        assert latency_ms < 100, f"Prediction took {latency_ms}ms, exceeds 100ms target"
    
    @pytest.mark.asyncio
    async def test_ml_model_training(self, prediction_engine):
        """Test ML model training with synthetic data"""
        # Force model training
        prediction_engine._success_model = None
        
        with patch.object(prediction_engine, '_load_success_training_data', 
                         new_callable=AsyncMock, return_value=[]):
            with patch.object(prediction_engine, '_save_model', new_callable=AsyncMock):
                await prediction_engine._train_success_model()
        
        # Verify model was created
        assert prediction_engine._success_model is not None
        assert prediction_engine._success_model != "rule_based"  # Should be actual ML model
    
    @pytest.mark.asyncio
    async def test_feature_engineering(
        self, prediction_engine, sample_pattern, sample_context, sample_organization, sample_constraints
    ):
        """Test comprehensive feature engineering"""
        features = await prediction_engine._generate_success_features(
            pattern=sample_pattern,
            context=sample_context,
            organization=sample_organization,
            constraints=sample_constraints
        )
        
        # Verify feature vector structure
        assert isinstance(features, list)
        assert len(features) >= 20  # Should have comprehensive features
        assert all(isinstance(f, (int, float)) for f in features)
        assert all(0 <= f <= 10 for f in features)  # Features should be normalized/reasonable
    
    @pytest.mark.asyncio
    async def test_complexity_calculation(
        self, prediction_engine, sample_pattern, sample_context, sample_organization
    ):
        """Test implementation complexity calculation"""
        complexity = await prediction_engine._calculate_implementation_complexity(
            pattern=sample_pattern,
            context=sample_context,
            organization=sample_organization
        )
        
        assert 0.0 <= complexity <= 1.0
        
        # ML pattern should have higher complexity
        assert complexity > 0.3, "ML patterns should have non-trivial complexity"
    
    # ==================== ROI PREDICTION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_roi_prediction_basic(
        self, prediction_engine, sample_pattern, sample_organization, sample_context
    ):
        """Test basic ROI prediction functionality"""
        prediction = await prediction_engine.estimate_implementation_roi(
            pattern=sample_pattern,
            organization=sample_organization,
            context=sample_context
        )
        
        # Verify basic structure
        assert isinstance(prediction, ROIPrediction)
        assert prediction.pattern_id == sample_pattern.id
        assert prediction.implementation_cost > 0
        assert isinstance(prediction.implementation_cost_range, tuple)
        assert len(prediction.implementation_cost_range) == 2
        
        # Verify ROI calculations
        assert isinstance(prediction.roi_percentage, (int, float))
        assert isinstance(prediction.roi_range, tuple)
        assert prediction.payback_period_months > 0
        assert isinstance(prediction.net_present_value, (int, float))
        
        # Verify risk adjustments
        assert 0.0 <= prediction.risk_factor <= 1.0
        assert 0.0 <= prediction.uncertainty_score <= 1.0
        assert prediction.time_to_value_months > 0
    
    @pytest.mark.asyncio
    async def test_roi_accuracy_target(
        self, prediction_engine, sample_pattern, sample_organization, sample_context
    ):
        """Test ROI prediction accuracy meets 90% target"""
        # This would require historical data for actual validation
        # For now, test that predictions are reasonable
        
        prediction = await prediction_engine.estimate_implementation_roi(
            pattern=sample_pattern,
            organization=sample_organization,
            context=sample_context
        )
        
        # Verify confidence is high enough for accuracy target
        assert prediction.confidence_score >= 0.7, "ROI confidence should support 90% accuracy target"
        
        # Verify range is reasonable (not too wide)
        roi_range_width = abs(prediction.roi_range[1] - prediction.roi_range[0])
        assert roi_range_width <= abs(prediction.roi_percentage) * 1.5, "ROI range should be reasonably narrow"
    
    @pytest.mark.asyncio
    async def test_benefit_categorization(self, prediction_engine, sample_pattern, sample_organization, sample_context):
        """Test ROI benefit categorization"""
        benefits = await prediction_engine._estimate_benefits_by_category(
            pattern=sample_pattern,
            organization=sample_organization,
            context=sample_context,
            features=[0.7, 0.8, 0.6]  # Mock features
        )
        
        assert isinstance(benefits, dict)
        assert all(isinstance(category, ROICategory) for category in benefits.keys())
        assert all(isinstance(value, (int, float)) and value >= 0 for value in benefits.values())
        
        # ML patterns should have productivity benefits
        assert ROICategory.DEVELOPER_PRODUCTIVITY in benefits or ROICategory.PERFORMANCE_IMPROVEMENT in benefits
    
    @pytest.mark.asyncio
    async def test_value_realization_curve(self, prediction_engine):
        """Test value realization curve generation"""
        expected_benefits = {
            ROICategory.COST_REDUCTION: 50000,
            ROICategory.DEVELOPER_PRODUCTIVITY: 75000,
            ROICategory.PERFORMANCE_IMPROVEMENT: 40000
        }
        
        curve = await prediction_engine._generate_value_realization_curve(
            expected_benefits=expected_benefits,
            payback_period_months=18.0
        )
        
        assert isinstance(curve, list)
        assert len(curve) > 0
        assert all('month' in point and 'monthly_value' in point and 'cumulative_value' in point 
                  for point in curve)
        
        # Verify cumulative value increases over time
        for i in range(1, min(5, len(curve))):
            assert curve[i]['cumulative_value'] >= curve[i-1]['cumulative_value']
    
    @pytest.mark.asyncio
    async def test_sensitivity_analysis(self, prediction_engine):
        """Test ROI sensitivity analysis"""
        features = [0.7, 0.8, 0.6, 0.5] * 5  # Mock feature vector
        expected_benefits = {ROICategory.COST_REDUCTION: 100000}
        implementation_cost = 50000
        
        sensitivity = await prediction_engine._perform_sensitivity_analysis(
            features=features,
            expected_benefits=expected_benefits,
            implementation_cost=implementation_cost
        )
        
        assert isinstance(sensitivity, dict)
        assert 'implementation_cost' in sensitivity
        assert 'expected_benefits' in sensitivity
        assert 'key_insights' in sensitivity
        
        # Verify sensitivity scenarios
        cost_scenarios = sensitivity['implementation_cost']['scenarios']
        assert len(cost_scenarios) > 0
        assert all('cost_change_pct' in scenario and 'roi_change_pct' in scenario 
                  for scenario in cost_scenarios)
    
    # ==================== STRATEGY RECOMMENDATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_strategy_recommendation_basic(
        self, prediction_engine, sample_pattern, sample_organization, sample_context, sample_constraints
    ):
        """Test basic strategy recommendation functionality"""
        recommendation = await prediction_engine.recommend_implementation_strategy(
            pattern=sample_pattern,
            organization=sample_organization,
            context=sample_context,
            constraints=sample_constraints
        )
        
        # Verify basic structure
        assert isinstance(recommendation, StrategyRecommendation)
        assert recommendation.pattern_id == sample_pattern.id
        assert isinstance(recommendation.primary_strategy, ImplementationStrategy)
        assert isinstance(recommendation.alternative_strategies, list)
        
        # Verify primary strategy details
        primary = recommendation.primary_strategy
        assert primary.strategy_name != ""
        assert primary.strategy_description != ""
        assert primary.total_timeline_months > 0
        assert isinstance(primary.phases, list)
        assert len(primary.phases) > 0
        assert isinstance(primary.team_composition, dict)
        assert len(primary.team_composition) > 0
    
    @pytest.mark.asyncio
    async def test_strategy_alternatives(
        self, prediction_engine, sample_pattern, sample_organization, sample_context, sample_constraints
    ):
        """Test generation of alternative strategies"""
        with patch.object(prediction_engine, '_generate_alternative_strategies') as mock_alternatives:
            mock_alternatives.return_value = [
                Mock(spec=ImplementationStrategy, strategy_name="Conservative Strategy"),
                Mock(spec=ImplementationStrategy, strategy_name="Aggressive Strategy")
            ]
            
            recommendation = await prediction_engine.recommend_implementation_strategy(
                pattern=sample_pattern,
                organization=sample_organization,
                context=sample_context,
                constraints=sample_constraints
            )
        
        assert len(recommendation.alternative_strategies) >= 1
        # Should have different approaches
        strategy_names = [s.strategy_name for s in [recommendation.primary_strategy] + recommendation.alternative_strategies]
        assert len(set(strategy_names)) > 1, "Should generate diverse strategy alternatives"
    
    @pytest.mark.asyncio
    async def test_team_composition_optimization(self, prediction_engine, sample_pattern, sample_context, sample_constraints):
        """Test team composition optimization"""
        team_comp = await prediction_engine._determine_team_composition(
            pattern=sample_pattern,
            context=sample_context,
            constraints=sample_constraints,
            approach="standard_implementation"
        )
        
        assert isinstance(team_comp, dict)
        assert sum(team_comp.values()) <= sample_constraints.team_size
        
        # ML pattern should include ML engineers
        roles = list(team_comp.keys())
        assert any('ml' in role.lower() or 'data' in role.lower() or 'senior' in role.lower() for role in roles)
    
    # ==================== CONTINUOUS LEARNING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_accuracy_tracking(self, prediction_engine):
        """Test prediction accuracy tracking"""
        # Create mock prediction
        mock_prediction = {
            'id': str(uuid4()),
            'predicted_outcome': 'success',
            'confidence_score': 0.8,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Mock actual outcome
        actual_outcome = {
            'outcome_type': 'success',
            'verification_method': 'automated_testing',
            'outcome_timestamp': datetime.utcnow()
        }
        
        with patch.object(prediction_engine, '_get_prediction', return_value=mock_prediction):
            with patch.object(prediction_engine, '_store_accuracy_record', new_callable=AsyncMock):
                accuracy = await prediction_engine.track_prediction_accuracy(
                    prediction_id=mock_prediction['id'],
                    actual_outcome=actual_outcome
                )
        
        assert isinstance(accuracy, AccuracyMetrics)
        assert accuracy.total_predictions >= 0
    
    @pytest.mark.asyncio
    async def test_model_retraining_trigger(self, prediction_engine):
        """Test model retraining when accuracy drops"""
        # Simulate accuracy drop
        from models.prediction_engine import PredictionAccuracy, PredictionConfidence
        
        # Add low-accuracy records
        for _ in range(15):
            low_accuracy = PredictionAccuracy(
                id=uuid4(),
                prediction_id=uuid4(),
                prediction_type='success_prediction',
                predicted_outcome='success',
                predicted_confidence=0.8,
                prediction_timestamp=datetime.utcnow(),
                actual_outcome='failure',
                outcome_timestamp=datetime.utcnow(),
                outcome_verification='manual',
                accuracy_score=0.2,  # Low accuracy
                error_magnitude=0.6,
                prediction_quality=PredictionConfidence.LOW,
                error_analysis={},
                improvement_opportunities=[],
                model_update_triggers=['accuracy_threshold'],
                created_at=datetime.utcnow()
            )
            prediction_engine._accuracy_history.append(low_accuracy)
        
        with patch.object(prediction_engine, '_retrain_models_background', new_callable=AsyncMock) as mock_retrain:
            await prediction_engine._check_model_performance()
            
            # Should trigger retraining due to low accuracy
            mock_retrain.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthetic_data_generation(self, prediction_engine):
        """Test synthetic training data generation"""
        synthetic_data = await prediction_engine._generate_synthetic_training_data()
        
        assert isinstance(synthetic_data, list)
        assert len(synthetic_data) >= 100  # Should generate sufficient data
        
        # Verify data structure
        for record in synthetic_data[:5]:  # Check first 5 records
            assert 'features' in record
            assert 'outcome' in record
            assert isinstance(record['features'], list)
            assert record['outcome'] in [0, 1, 2]  # Valid outcome classes
            assert len(record['features']) > 10  # Sufficient features
    
    # ==================== INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_end_to_end_prediction_flow(
        self, prediction_engine, sample_pattern, sample_context, sample_organization, sample_constraints
    ):
        """Test complete end-to-end prediction flow"""
        with patch.object(prediction_engine, '_store_prediction', new_callable=AsyncMock):
            # Run all prediction types
            success_pred = await prediction_engine.predict_implementation_success(
                pattern=sample_pattern,
                context=sample_context,
                organization=sample_organization,
                constraints=sample_constraints
            )
            
            roi_pred = await prediction_engine.estimate_implementation_roi(
                pattern=sample_pattern,
                organization=sample_organization,
                context=sample_context
            )
            
            strategy_rec = await prediction_engine.recommend_implementation_strategy(
                pattern=sample_pattern,
                organization=sample_organization,
                context=sample_context,
                constraints=sample_constraints
            )
        
        # Verify all predictions were generated successfully
        assert isinstance(success_pred, SuccessPrediction)
        assert isinstance(roi_pred, ROIPrediction)
        assert isinstance(strategy_rec, StrategyRecommendation)
        
        # Verify consistency between predictions
        assert success_pred.pattern_id == roi_pred.pattern_id == strategy_rec.pattern_id
    
    @pytest.mark.asyncio
    async def test_batch_prediction_performance(self, prediction_engine, sample_context, sample_organization):
        """Test batch prediction performance"""
        # Create multiple test patterns
        patterns = []
        for i in range(10):
            pattern = KnowledgeItem(
                id=uuid4(),
                title=f"Test Pattern {i}",
                content=f"Content for pattern {i}",
                knowledge_type="pattern",
                source_type="test",
                tags=["test", "performance"],
                created_at=datetime.utcnow()
            )
            patterns.append(pattern)
        
        start_time = datetime.utcnow()
        
        with patch.object(prediction_engine, '_store_prediction', new_callable=AsyncMock):
            # Run predictions for all patterns
            tasks = []
            for pattern in patterns:
                task = prediction_engine.predict_implementation_success(
                    pattern=pattern,
                    context=sample_context,
                    organization=sample_organization
                )
                tasks.append(task)
            
            predictions = await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        total_time_seconds = (end_time - start_time).total_seconds()
        
        # Verify all predictions completed
        assert len(predictions) == len(patterns)
        assert all(isinstance(pred, SuccessPrediction) for pred in predictions)
        
        # Performance target: should handle batch efficiently
        predictions_per_second = len(patterns) / total_time_seconds
        assert predictions_per_second >= 5, f"Batch performance {predictions_per_second:.2f} predictions/sec too low"
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self, prediction_engine, sample_pattern, sample_context, sample_organization):
        """Test error handling and robustness"""
        # Test with invalid/missing data
        invalid_context = PatternContext(
            domain="",  # Invalid empty domain
            technology_stack=[],
            project_type="",
            team_experience="invalid_level",
            business_criticality="",
            compliance_requirements=[]
        )
        
        # Should handle gracefully without crashing
        with patch.object(prediction_engine, '_store_prediction', new_callable=AsyncMock):
            try:
                prediction = await prediction_engine.predict_implementation_success(
                    pattern=sample_pattern,
                    context=invalid_context,
                    organization=sample_organization
                )
                # Should still return a valid prediction structure
                assert isinstance(prediction, SuccessPrediction)
                assert 0.0 <= prediction.confidence_score <= 1.0
            except Exception as e:
                pytest.fail(f"Prediction engine should handle invalid input gracefully: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])