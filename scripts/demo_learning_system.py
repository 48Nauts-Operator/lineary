#!/usr/bin/env python3
# ABOUTME: Demonstration script for Agent Learning Feedback Loop system
# ABOUTME: Shows the machine learning capabilities for intelligent agent routing

import asyncio
import asyncpg
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import uuid4, UUID

# Add the parent directory to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'memory-api'))

from services.agent_learning_engine import AgentLearningEngine, TaskOutcome, TaskComplexity
from services.context_aware_router import TaskContext, ContextAwareAgentRouter
from services.intelligent_routing_service import IntelligentRoutingService
from core.database import DatabaseManager
from core.config import get_settings

async def create_demo_agents(db_manager):
    """Create demo agents for the learning demonstration"""
    print("🤖 Creating demo agents...")
    
    agents_data = [
        {
            'name': 'CodeExpert_Agent',
            'type': 'code_specialist',
            'capabilities': ['code_analysis', 'debugging', 'code_generation'],
            'specialization': 'coding tasks'
        },
        {
            'name': 'SecurityGuard_Agent', 
            'type': 'security_specialist',
            'capabilities': ['security_audit', 'vulnerability_scan', 'penetration_testing'],
            'specialization': 'security tasks'
        },
        {
            'name': 'GeneralHelper_Agent',
            'type': 'generalist',
            'capabilities': ['general_assistance', 'research', 'documentation'],
            'specialization': 'general tasks'
        },
        {
            'name': 'DataWizard_Agent',
            'type': 'data_specialist', 
            'capabilities': ['data_analysis', 'machine_learning', 'statistics'],
            'specialization': 'data tasks'
        },
        {
            'name': 'FastResponse_Agent',
            'type': 'speed_specialist',
            'capabilities': ['quick_response', 'simple_tasks', 'basic_queries'],
            'specialization': 'simple tasks'
        }
    ]
    
    created_agents = []
    
    async with db_manager.postgres.acquire() as conn:
        # Create agents table if it doesn't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL UNIQUE,
                type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create capabilities table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                category VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create agent_capabilities table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_capabilities (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                capability_id UUID NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
                priority INTEGER DEFAULT 1,
                proficiency_level FLOAT DEFAULT 0.8,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(agent_id, capability_id)
            )
        """)
        
        for agent_data in agents_data:
            # Insert agent
            agent_id = await conn.fetchval("""
                INSERT INTO agents (name, type, metadata) 
                VALUES ($1, $2, $3) 
                ON CONFLICT (name) DO UPDATE SET 
                    type = $2, metadata = $3, updated_at = NOW()
                RETURNING id
            """, agent_data['name'], agent_data['type'], json.dumps({
                'specialization': agent_data['specialization'],
                'demo_agent': True
            }))
            
            created_agents.append({'id': agent_id, **agent_data})
            
            # Insert capabilities and link to agent
            for capability in agent_data['capabilities']:
                # Insert capability
                capability_id = await conn.fetchval("""
                    INSERT INTO capabilities (name, category) 
                    VALUES ($1, $2) 
                    ON CONFLICT (name) DO UPDATE SET category = $2
                    RETURNING id
                """, capability, agent_data['type'])
                
                # Link agent to capability
                await conn.execute("""
                    INSERT INTO agent_capabilities (agent_id, capability_id, priority) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (agent_id, capability_id) DO UPDATE SET priority = $3
                """, agent_id, capability_id, random.randint(1, 5))
    
    print(f"✅ Created {len(created_agents)} demo agents")
    return created_agents

async def simulate_task_outcomes(learning_engine, agents, num_tasks=50):
    """Simulate realistic task outcomes with agent performance patterns"""
    print(f"📊 Simulating {num_tasks} task outcomes...")
    
    task_types = ['code_analysis', 'security_audit', 'data_analysis', 'debugging', 'documentation']
    complexities = [TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]
    
    # Define agent performance patterns (realistic specialization)
    agent_performance = {
        'CodeExpert_Agent': {
            'code_analysis': 0.95, 'debugging': 0.90, 'code_generation': 0.88,
            'security_audit': 0.60, 'data_analysis': 0.65, 'documentation': 0.70
        },
        'SecurityGuard_Agent': {
            'security_audit': 0.92, 'vulnerability_scan': 0.89,
            'code_analysis': 0.55, 'data_analysis': 0.50, 'debugging': 0.60
        },
        'DataWizard_Agent': {
            'data_analysis': 0.94, 'machine_learning': 0.91, 'statistics': 0.88,
            'code_analysis': 0.70, 'security_audit': 0.45, 'debugging': 0.65
        },
        'GeneralHelper_Agent': {
            'documentation': 0.85, 'research': 0.80, 'general_assistance': 0.82,
            'code_analysis': 0.60, 'security_audit': 0.55, 'data_analysis': 0.58
        },
        'FastResponse_Agent': {
            'simple_tasks': 0.90, 'quick_response': 0.95, 'basic_queries': 0.88,
            'code_analysis': 0.50, 'security_audit': 0.40, 'data_analysis': 0.45
        }
    }
    
    outcomes = []
    
    for i in range(num_tasks):
        # Select random task
        task_type = random.choice(task_types)
        complexity = random.choice(complexities)
        agent = random.choice(agents)
        agent_name = agent['name']
        
        # Get base success rate for this agent-task combination
        base_success_rate = agent_performance.get(agent_name, {}).get(task_type, 0.6)
        
        # Adjust for complexity
        complexity_modifier = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MODERATE: 0.0,
            TaskComplexity.COMPLEX: -0.15,
            TaskComplexity.CRITICAL: -0.25
        }
        
        adjusted_success_rate = min(1.0, max(0.0, base_success_rate + complexity_modifier[complexity]))
        
        # Determine success and generate metrics
        success = random.random() < adjusted_success_rate
        success_score = adjusted_success_rate + random.uniform(-0.1, 0.1)
        success_score = min(1.0, max(0.0, success_score))
        
        # Generate completion time (faster agents are faster, complex tasks take longer)
        base_time = {
            TaskComplexity.SIMPLE: random.uniform(1, 5),
            TaskComplexity.MODERATE: random.uniform(5, 15),
            TaskComplexity.COMPLEX: random.uniform(15, 45),
            TaskComplexity.CRITICAL: random.uniform(30, 120)
        }[complexity]
        
        # Agent speed modifiers
        if 'Fast' in agent_name:
            base_time *= 0.7
        elif 'Expert' in agent_name or 'Wizard' in agent_name:
            base_time *= 0.85
        
        completion_time = base_time * random.uniform(0.8, 1.2)
        
        # Quality metrics
        quality_metrics = {
            'accuracy': success_score,
            'efficiency': min(1.0, 1.0 - (completion_time - base_time) / base_time),
            'completeness': random.uniform(0.7, 1.0) if success else random.uniform(0.3, 0.7)
        }
        
        # User satisfaction (correlated with success)
        user_satisfaction = None
        if random.random() < 0.7:  # 70% chance of user feedback
            user_satisfaction = success_score * 4 + random.uniform(0, 1)
            user_satisfaction = min(5.0, max(1.0, user_satisfaction))
        
        # Error count
        error_count = 0 if success else random.randint(1, 3)
        
        # Create outcome
        outcome = TaskOutcome(
            routing_id=f"demo_{i}_{int(time.time())}",
            agent_id=UUID(agent['id']),
            task_type=task_type,
            complexity=complexity,
            success_score=success_score,
            completion_time=completion_time,
            quality_metrics=quality_metrics,
            user_satisfaction=user_satisfaction,
            error_count=error_count,
            retry_attempts=0,
            cost_actual=random.uniform(5, 50),
            timestamp=datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))  # Random time in last 24h
        )
        
        # Track outcome in learning engine
        await learning_engine.track_task_outcome(outcome.routing_id, outcome)
        outcomes.append(outcome)
        
        if (i + 1) % 10 == 0:
            print(f"  📈 Processed {i + 1}/{num_tasks} task outcomes...")
    
    print(f"✅ Completed simulation of {num_tasks} task outcomes")
    return outcomes

async def demonstrate_specialization_detection(learning_engine):
    """Demonstrate agent specialization detection"""
    print("\n🧠 Analyzing agent specializations...")
    
    specializations = await learning_engine.analyze_agent_specializations()
    
    print("📋 Discovered Agent Specializations:")
    for agent_id, specs in specializations.items():
        print(f"  🤖 Agent {agent_id[-8:]}:")
        for spec in specs:
            print(f"    • {spec}")
    
    return specializations

async def demonstrate_routing_optimization(learning_engine):
    """Demonstrate routing optimization"""
    print("\n⚡ Running routing optimization...")
    
    try:
        optimization = await learning_engine.optimize_routing_weights()
        
        print("📊 Routing Optimization Results:")
        print(f"  • Optimization ID: {optimization.optimization_id}")
        print(f"  • Performance Improvement: {optimization.performance_improvement:.2f}%")
        print(f"  • Confidence Interval: [{optimization.confidence_interval[0]:.2f}%, {optimization.confidence_interval[1]:.2f}%]")
        print(f"  • Method: {optimization.optimization_method}")
        print(f"  • Applied At: {optimization.applied_at}")
        
        return optimization
    except Exception as e:
        print(f"  ⚠️  Optimization requires more data: {str(e)}")
        return None

async def demonstrate_success_prediction(learning_engine, agents):
    """Demonstrate success prediction for different agent-task combinations"""
    print("\n🔮 Testing success prediction system...")
    
    test_tasks = [
        TaskContext(task_type='code_analysis', complexity=TaskComplexity.MODERATE),
        TaskContext(task_type='security_audit', complexity=TaskComplexity.COMPLEX),
        TaskContext(task_type='data_analysis', complexity=TaskComplexity.SIMPLE),
    ]
    
    for task in test_tasks:
        print(f"\n  📋 Task: {task.task_type} ({task.complexity.value})")
        
        for agent in agents[:3]:  # Test with first 3 agents
            try:
                prediction = await learning_engine.predict_task_success_probability(
                    task, UUID(agent['id']))
                
                print(f"    🤖 {agent['name']}:")
                print(f"      • Predicted Success: {prediction.predicted_success_rate:.2%}")
                print(f"      • Confidence: [{prediction.confidence_interval[0]:.2%}, {prediction.confidence_interval[1]:.2%}]")
                if prediction.risk_factors:
                    print(f"      • Risk Factors: {', '.join(prediction.risk_factors)}")
                
            except Exception as e:
                print(f"    🤖 {agent['name']}: Prediction failed ({str(e)})")

async def demonstrate_intelligent_routing(intelligent_router, agents):
    """Demonstrate the full intelligent routing system"""
    print("\n🚀 Testing Intelligent Routing System...")
    
    test_tasks = [
        TaskContext(
            task_type='code_analysis', 
            complexity=TaskComplexity.MODERATE,
            priority=7,
            required_capabilities=['code_analysis']
        ),
        TaskContext(
            task_type='security_audit', 
            complexity=TaskComplexity.COMPLEX,
            priority=9,
            required_capabilities=['security_audit'],
            sensitive_data=True
        )
    ]
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n  🎯 Test Case {i}: {task.task_type} ({task.complexity.value})")
        print(f"     Priority: {task.priority}/10, Sensitive: {task.sensitive_data}")
        
        try:
            result = await intelligent_router.route_task_with_learning(task)
            
            if result.routing_result.success:
                selection = result.routing_result.agent_selection
                print(f"    ✅ Selected Agent: {selection.agent_name}")
                print(f"    📊 Confidence: {selection.confidence_score:.2%}")
                print(f"    🔮 Predicted Success: {result.success_prediction.predicted_success_rate:.2%}" if result.success_prediction else "    🔮 No prediction available")
                print(f"    ⚡ Optimization Applied: {result.optimization_confidence > 0.0}")
                print(f"    📝 Explanation: {result.routing_explanation}")
                
                if result.alternative_agents:
                    print(f"    🔄 Alternatives Available: {len(result.alternative_agents)}")
                    for alt in result.alternative_agents[:2]:
                        print(f"      • {alt.get('agent_id', 'Unknown')[-8:]} ({alt.get('type', 'unknown')})")
            else:
                print(f"    ❌ Routing Failed: {result.routing_result.error_message}")
                
        except Exception as e:
            print(f"    💥 Intelligent routing error: {str(e)}")

async def demonstrate_learning_analytics(learning_engine):
    """Demonstrate learning analytics and insights"""
    print("\n📈 Learning System Analytics...")
    
    try:
        analytics = await learning_engine.get_learning_analytics()
        
        print("📊 System Statistics:")
        print(f"  • Total Outcomes Processed: {analytics['learning_metrics']['total_outcomes_processed']}")
        print(f"  • Specializations Discovered: {analytics['learning_metrics']['specializations_discovered']}")
        print(f"  • Optimizations Applied: {analytics['learning_metrics']['optimizations_applied']}")
        
        print("\n📋 Active Specializations:")
        for spec in analytics['active_specializations'][:5]:
            print(f"  • {spec['specialization_type']}: {spec['agent_count']} agents, "
                  f"{spec['avg_confidence']:.2%} avg confidence")
        
        print("\n⚡ Recent Performance Trends:")
        for trend in analytics['recent_performance_trends'][-5:]:
            print(f"  • {trend['hour']}: {trend['avg_success']:.2%} success rate "
                  f"({trend['outcome_count']} tasks)")
        
        if analytics['prediction_accuracy_trends']:
            recent_accuracy = analytics['prediction_accuracy_trends'][-1]
            print(f"\n🎯 Prediction Accuracy: {recent_accuracy['avg_accuracy']:.2%}")
        
    except Exception as e:
        print(f"  ⚠️  Analytics error: {str(e)}")

async def run_comprehensive_demo():
    """Run comprehensive demonstration of the Agent Learning Feedback Loop"""
    print("🌟 BETTY Agent Learning Feedback Loop - Comprehensive Demo")
    print("=" * 60)
    
    # Initialize database connection
    settings = get_settings()
    db_manager = DatabaseManager(settings)
    await db_manager.initialize()
    
    try:
        # Initialize learning engine
        learning_engine = AgentLearningEngine(db_manager)
        await learning_engine.initialize()
        
        # Initialize intelligent routing
        intelligent_router = IntelligentRoutingService(db_manager)
        await intelligent_router.initialize()
        
        # Step 1: Create demo agents
        agents = await create_demo_agents(db_manager)
        
        # Step 2: Simulate realistic task outcomes
        await simulate_task_outcomes(learning_engine, agents, num_tasks=75)
        
        # Step 3: Demonstrate specialization detection
        await demonstrate_specialization_detection(learning_engine)
        
        # Step 4: Demonstrate routing optimization  
        await demonstrate_routing_optimization(learning_engine)
        
        # Step 5: Demonstrate success prediction
        await demonstrate_success_prediction(learning_engine, agents)
        
        # Step 6: Demonstrate intelligent routing
        await demonstrate_intelligent_routing(intelligent_router, agents)
        
        # Step 7: Show learning analytics
        await demonstrate_learning_analytics(learning_engine)
        
        print("\n🎉 Demo completed successfully!")
        print("\nThe Agent Learning Feedback Loop demonstrates:")
        print("✅ Continuous learning from task outcomes")
        print("✅ Agent specialization detection") 
        print("✅ Routing optimization with machine learning")
        print("✅ Success probability prediction")
        print("✅ Intelligent routing with ML enhancements")
        print("✅ Performance analytics and insights")
        print("\nThe system will continue learning and improving with each task!")
        
    except Exception as e:
        print(f"💥 Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if 'learning_engine' in locals():
            await learning_engine.cleanup()
        if 'intelligent_router' in locals():
            await intelligent_router.cleanup()
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(run_comprehensive_demo())