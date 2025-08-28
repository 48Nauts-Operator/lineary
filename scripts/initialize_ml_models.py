#!/usr/bin/env python3
"""Initialize ML models with synthetic training data"""

import asyncio
import sys
import os
sys.path.append('/app')

from services.pattern_success_prediction_engine import PatternSuccessPredictionEngine
from core.database import DatabaseManager
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine

async def initialize_models():
    """Initialize ML models with synthetic data"""
    print("🤖 Initializing ML models with synthetic data...")
    
    try:
        # Initialize dependencies (would be properly injected in production)
        db_manager = DatabaseManager()
        vector_service = VectorService(db_manager)
        quality_scorer = AdvancedQualityScorer(db_manager, vector_service)
        intelligence_engine = PatternIntelligenceEngine(db_manager, vector_service, quality_scorer)
        
        # Initialize prediction engine
        prediction_engine = PatternSuccessPredictionEngine(
            db_manager=db_manager,
            vector_service=vector_service,
            quality_scorer=quality_scorer,
            intelligence_engine=intelligence_engine
        )
        
        # Force model training with synthetic data
        print("Training success prediction model...")
        await prediction_engine._train_success_model()
        
        print("Training ROI prediction model...")
        await prediction_engine._train_roi_model()
        
        print("Training timeline prediction model...")
        await prediction_engine._train_timeline_model()
        
        print("Training risk assessment model...")
        await prediction_engine._train_risk_model()
        
        print("✅ ML models initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize ML models: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(initialize_models())
