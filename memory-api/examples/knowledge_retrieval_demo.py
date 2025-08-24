# ABOUTME: Comprehensive demonstration of BETTY Knowledge Retrieval System
# ABOUTME: Shows unlimited context awareness, similarity search, pattern matching, and cross-project intelligence

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import httpx

class KnowledgeRetrievalDemo:
    """Demonstration of BETTY's unlimited context awareness capabilities"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.user_id = "demo-user-12345"
        
    async def demo_complete_workflow(self):
        """Demonstrate complete knowledge retrieval workflow"""
        print("🧠 BETTY Knowledge Retrieval System Demo")
        print("=" * 60)
        
        try:
            # 1. Context Loading for New Session
            await self.demo_context_loading()
            
            # 2. Similarity Search Across Projects
            await self.demo_similarity_search()
            
            # 3. Pattern Matching
            await self.demo_pattern_matching()
            
            # 4. Technology Evolution
            await self.demo_technology_evolution()
            
            # 5. Cross-Project Recommendations
            await self.demo_cross_project_recommendations()
            
            # 6. Cache Intelligence
            await self.demo_cache_intelligence()
            
            # 7. System Statistics
            await self.demo_system_statistics()
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        finally:
            await self.client.aclose()
    
    async def demo_context_loading(self):
        """Demonstrate context loading for unlimited awareness"""
        print("\n🔍 1. Context Loading - Unlimited Context Awareness")
        print("-" * 50)
        
        context_request = {
            "user_id": self.user_id,
            "project_id": "137docs",
            "current_context": {
                "working_on": "Implementing user authentication with JWT tokens",
                "technologies_involved": ["FastAPI", "JWT", "PostgreSQL", "Redis"],
                "files_open": [
                    "/backend/auth/jwt_handler.py",
                    "/backend/middleware/auth.py",
                    "/backend/models/user.py"
                ],
                "user_message": "How should I implement secure JWT authentication with refresh tokens and rate limiting?",
                "problem_type": "authentication",
                "error_symptoms": []
            },
            "context_depth": "comprehensive",
            "include_cross_project": True,
            "max_items": 25,
            "similarity_threshold": 0.7
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/knowledge/retrieve/context",
                json=context_request,
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                context = data["context"]
                metadata = data["metadata"]
                
                print(f"✅ Context loaded successfully!")
                print(f"📊 Total knowledge items: {metadata['total_knowledge_items']:,}")
                print(f"🎯 Relevant items returned: {metadata['items_returned']}")
                print(f"⚡ Search time: {metadata['search_time_ms']:.2f}ms")
                
                # Show relevant knowledge
                if context.get("relevant_knowledge"):
                    print(f"\n🧠 Relevant Knowledge ({len(context['relevant_knowledge'])} items):")
                    for i, item in enumerate(context["relevant_knowledge"][:3], 1):
                        print(f"  {i}. {item['title']} (Score: {item['relevance_score']:.3f})")
                        print(f"     Project: {item['project']} | Type: {item['knowledge_type']}")
                        if item.get("key_insights"):
                            print(f"     💡 Key Insights: {', '.join(item['key_insights'][:2])}")
                
                # Show similar patterns
                if context.get("similar_patterns"):
                    print(f"\n🔄 Similar Patterns ({len(context['similar_patterns'])} found):")
                    for pattern in context["similar_patterns"][:2]:
                        print(f"  • {pattern['pattern']} (Used {pattern['usage_count']} times, {pattern['success_rate']:.1%} success)")
                        print(f"    Projects: {', '.join(pattern['projects_used'])}")
                
                # Show cross-project insights
                if context.get("cross_project_insights"):
                    print(f"\n🌐 Cross-Project Insights ({len(context['cross_project_insights'])} found):")
                    for insight in context["cross_project_insights"][:2]:
                        print(f"  • {insight['project']}: {insight['insight'][:80]}...")
                        print(f"    Applicability: {insight['applicability_score']:.3f}")
                
            else:
                print(f"❌ Context loading failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Context loading error: {e}")
    
    async def demo_similarity_search(self):
        """Demonstrate similarity search across all projects"""
        print("\n🔍 2. Similarity Search - Cross-Project Problem Solving")
        print("-" * 50)
        
        similarity_request = {
            "user_id": self.user_id,
            "query": {
                "text": "PostgreSQL connection pool exhaustion causing timeouts under high load",
                "context": {
                    "problem_type": "database_performance",
                    "technologies": ["PostgreSQL", "SQLAlchemy", "FastAPI"],
                    "error_symptoms": ["connection timeouts", "pool exhausted", "high response times"],
                    "domain": "web_application"
                }
            },
            "search_scope": {
                "projects": ["137docs", "nautBrain", "all"],
                "knowledge_types": ["problem_solution", "code_change", "insight"],
                "time_range": "last_12_months"
            },
            "similarity_threshold": 0.6,
            "max_results": 15
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/knowledge/retrieve/similar",
                json=similarity_request,
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                similar_items = data["similar_items"]
                query_analysis = data["query_analysis"]
                search_metadata = data["search_metadata"]
                
                print(f"✅ Found {len(similar_items)} similar problems!")
                print(f"⚡ Search time: {search_metadata['search_time_ms']:.2f}ms")
                print(f"🎯 Similarity threshold: {search_metadata['similarity_threshold']}")
                
                if similar_items:
                    print(f"\n🔍 Most Similar Problems:")
                    for i, item in enumerate(similar_items[:3], 1):
                        print(f"  {i}. {item['title']}")
                        print(f"     Similarity: {item['similarity_score']:.3f} | Reusability: {item['reusability_score']:.3f}")
                        print(f"     Project: {item['project']} | Technologies: {', '.join(item.get('technologies_used', []))}")
                        
                        if item.get("solution"):
                            print(f"     💡 Solution: {item['solution'][:100]}...")
                        
                        if item.get("outcome"):
                            print(f"     ✅ Outcome: {item['outcome']}")
                        
                        if item.get("code_changes"):
                            print(f"     🔧 Code Changes: {len(item['code_changes'])} files modified")
                        
                        print()
                
                # Show query analysis
                print(f"🔍 Query Analysis:")
                print(f"  Original: {query_analysis['original_query']}")
                print(f"  Enhanced: {query_analysis['enhanced_query']}")
                print(f"  Technologies detected: {', '.join(query_analysis.get('technologies_detected', []))}")
                
            else:
                print(f"❌ Similarity search failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Similarity search error: {e}")
    
    async def demo_pattern_matching(self):
        """Demonstrate reusable pattern discovery"""
        print("\n🏗️ 3. Pattern Matching - Reusable Architecture Patterns")
        print("-" * 50)
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/knowledge/retrieve/patterns",
                params={
                    "pattern_type": "architectural",
                    "min_success_rate": 0.85,
                    "min_usage_count": 3,
                    "technologies": ["FastAPI", "PostgreSQL", "Redis"]
                },
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                patterns = data["patterns"]
                pattern_statistics = data["pattern_statistics"]
                
                print(f"✅ Found {len(patterns)} reusable patterns!")
                print(f"📊 Total patterns analyzed: {pattern_statistics.get('total_patterns_found', 0)}")
                print(f"🎯 Meeting criteria: {pattern_statistics.get('patterns_meeting_criteria', 0)}")
                print(f"📈 Average success rate: {pattern_statistics.get('avg_success_rate', 0):.1%}")
                
                if patterns:
                    print(f"\n🏗️ Top Reusable Patterns:")
                    for i, pattern in enumerate(patterns[:3], 1):
                        print(f"  {i}. {pattern['pattern_name']}")
                        print(f"     Usage: {pattern['usage_count']} times | Success: {pattern['success_rate']:.1%}")
                        print(f"     Projects: {', '.join(pattern['projects'])}")
                        print(f"     Description: {pattern['description']}")
                        
                        if pattern.get("components"):
                            print(f"     🔧 Components:")
                            for comp in pattern["components"][:2]:
                                print(f"       • {comp['component']}: {comp['purpose']}")
                        
                        if pattern.get("best_practices"):
                            print(f"     ✅ Best Practices:")
                            for practice in pattern["best_practices"][:2]:
                                print(f"       • {practice}")
                        
                        if pattern.get("common_pitfalls"):
                            print(f"     ⚠️ Common Pitfalls:")
                            for pitfall in pattern["common_pitfalls"][:2]:
                                print(f"       • {pitfall}")
                        
                        print()
                        
                # Show most used technologies
                if pattern_statistics.get("most_used_technologies"):
                    print(f"🔥 Most Used Technologies: {', '.join(pattern_statistics['most_used_technologies'][:5])}")
                
            else:
                print(f"❌ Pattern matching failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Pattern matching error: {e}")
    
    async def demo_technology_evolution(self):
        """Demonstrate technology evolution tracking"""
        print("\n📈 4. Technology Evolution - Learning from Past Decisions")
        print("-" * 50)
        
        technology = "FastAPI"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/knowledge/retrieve/technology/{technology}/evolution",
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                evolution = data["evolution"]
                recommendations = data["recommendations"]
                overall_success_rate = data["overall_success_rate"]
                
                print(f"✅ Technology evolution for {technology}")
                print(f"📊 Overall success rate: {overall_success_rate:.1%}")
                print(f"🏗️ Used in {len(evolution)} projects")
                print(f"💡 {len(recommendations)} recommendations generated")
                
                if evolution:
                    print(f"\n📈 Evolution Timeline:")
                    for i, usage in enumerate(evolution[:3], 1):
                        print(f"  {i}. Project: {usage['project']}")
                        print(f"     First used: {usage['first_used'][:10]}")
                        print(f"     Current usage: {usage['current_usage']}")
                        
                        if usage.get("patterns_adopted"):
                            print(f"     🏗️ Patterns: {', '.join(usage['patterns_adopted'][:3])}")
                        
                        if usage.get("lessons_learned"):
                            print(f"     💡 Lessons: {', '.join(usage['lessons_learned'][:2])}")
                        
                        if usage.get("improvements_over_time"):
                            print(f"     📈 Improvements: {', '.join(usage['improvements_over_time'][:2])}")
                        
                        print()
                
                if recommendations:
                    print(f"💡 Recommendations:")
                    for rec in recommendations[:3]:
                        print(f"  • {rec}")
                
            else:
                print(f"❌ Technology evolution failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Technology evolution error: {e}")
    
    async def demo_cross_project_recommendations(self):
        """Demonstrate cross-project recommendations"""
        print("\n🌐 5. Cross-Project Recommendations - Intelligence from All Projects")
        print("-" * 50)
        
        recommendation_request = {
            "user_id": self.user_id,
            "current_project": "new-saas-platform",
            "working_on": "Setting up scalable authentication and authorization system",
            "technologies_considering": ["FastAPI", "JWT", "PostgreSQL", "Redis", "Docker"],
            "constraints": ["must handle 10k concurrent users", "GDPR compliant", "multi-tenant"],
            "preferences": {
                "architecture_style": "microservices",
                "database_preference": "SQL",
                "deployment_preference": "containerized"
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/knowledge/retrieve/recommendations",
                json=recommendation_request,
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data["recommendations"]
                analysis_summary = data["analysis_summary"]
                confidence_score = data["confidence_score"]
                
                print(f"✅ Generated {len(recommendations)} recommendations!")
                print(f"🎯 Overall confidence: {confidence_score:.1%}")
                print(f"📋 Analysis: {analysis_summary}")
                
                if recommendations:
                    print(f"\n🎯 Top Recommendations:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f"  {i}. {rec['title']} ({rec['type'].replace('_', ' ').title()})")
                        print(f"     Confidence: {rec['confidence']:.1%} | Success Probability: {rec['success_probability']:.1%}")
                        print(f"     Reasoning: {rec['reasoning']}")
                        
                        if rec.get("applicable_knowledge"):
                            print(f"     📚 Based on {len(rec['applicable_knowledge'])} similar cases:")
                            for knowledge in rec["applicable_knowledge"][:2]:
                                print(f"       • {knowledge['source_project']}: {knowledge['title']}")
                                print(f"         Outcome: {knowledge.get('outcome', 'N/A')}")
                        
                        if rec.get("implementation_guidance"):
                            print(f"     🛠️ Implementation Steps:")
                            for step in rec["implementation_guidance"][:3]:
                                print(f"       • {step}")
                        
                        if rec.get("estimated_time_savings"):
                            print(f"     ⏱️ Estimated time savings: {rec['estimated_time_savings']}")
                        
                        if rec.get("risk_factors"):
                            print(f"     ⚠️ Risk factors: {', '.join(rec['risk_factors'][:2])}")
                        
                        print()
                
            else:
                print(f"❌ Recommendations failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Recommendations error: {e}")
    
    async def demo_cache_intelligence(self):
        """Demonstrate intelligent caching capabilities"""
        print("\n⚡ 6. Cache Intelligence - Smart Performance Optimization")
        print("-" * 50)
        
        try:
            # Get cache statistics
            stats_response = await self.client.get(
                f"{self.base_url}/api/knowledge/retrieve/stats",
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()["data"]
                retrieval_stats = stats_data["retrieval_system"]
                
                print("📊 Cache & Retrieval Statistics:")
                print(f"  📚 Total knowledge items: {retrieval_stats['total_knowledge_items']:,}")
                print(f"  🏗️ Total projects: {retrieval_stats['total_projects']}")
                print(f"  👥 Total users: {retrieval_stats['total_users']}")
                print(f"  📈 Average access count: {retrieval_stats['avg_access_count']:.1f}")
                print(f"  📅 Items added last week: {retrieval_stats['items_last_week']}")
                print(f"  📆 Items added last month: {retrieval_stats['items_last_month']}")
                
                # Show knowledge by type
                if stats_data.get("knowledge_by_type"):
                    print(f"\n📊 Knowledge by Type:")
                    for kb_type in stats_data["knowledge_by_type"][:5]:
                        print(f"  • {kb_type['type']}: {kb_type['count']} items (avg access: {kb_type['avg_access']:.1f})")
            
            # Clear cache demonstration
            print(f"\n🧹 Cache Management:")
            clear_response = await self.client.post(
                f"{self.base_url}/api/knowledge/retrieve/cache/clear",
                params={"cache_type": "context"},
                headers={"Authorization": f"Bearer demo-token"}
            )
            
            if clear_response.status_code == 200:
                clear_data = clear_response.json()
                print(f"✅ {clear_data['message']}")
                print(f"🎯 Cache pattern: {clear_data['cache_pattern']}")
            
        except Exception as e:
            print(f"❌ Cache intelligence error: {e}")
    
    async def demo_system_statistics(self):
        """Show comprehensive system statistics"""
        print("\n📈 7. System Health & Performance")
        print("-" * 50)
        
        try:
            # Health check
            health_response = await self.client.get(
                f"{self.base_url}/api/knowledge/retrieve/health"
            )
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                
                print(f"🏥 System Health: {health_data['status'].upper()}")
                print(f"⏰ Last checked: {health_data['timestamp']}")
                
                print(f"\n🔧 Component Status:")
                for component, status in health_data["components"].items():
                    status_emoji = "✅" if status == "operational" else "⚠️"
                    print(f"  {status_emoji} {component}: {status}")
                
                print(f"\n🚀 Capabilities:")
                for capability, enabled in health_data["capabilities"].items():
                    capability_emoji = "✅" if enabled else "❌"
                    capability_name = capability.replace("_", " ").title()
                    print(f"  {capability_emoji} {capability_name}")
            
        except Exception as e:
            print(f"❌ System health error: {e}")
    
    def print_demo_summary(self):
        """Print demo summary and key features"""
        print("\n" + "=" * 60)
        print("🎉 BETTY Knowledge Retrieval System Demo Complete!")
        print("=" * 60)
        
        print("\n🧠 Key Capabilities Demonstrated:")
        print("  ✅ Unlimited Context Awareness - Load relevant knowledge from ALL past work")
        print("  ✅ Cross-Project Intelligence - Learn from patterns across all projects")
        print("  ✅ Semantic Similarity Search - Find similar problems and solutions")
        print("  ✅ Pattern Recognition - Identify reusable architectural patterns")
        print("  ✅ Technology Evolution - Track technology usage and success over time")
        print("  ✅ Intelligent Recommendations - AI-powered suggestions based on history")
        print("  ✅ Smart Caching - Predictive caching for optimal performance")
        print("  ✅ Real-time Analytics - Comprehensive system monitoring")
        
        print("\n🚀 Benefits for Claude:")
        print("  • Never forget valuable knowledge from past conversations")
        print("  • Instantly access solutions from similar problems across all projects")
        print("  • Recommend proven patterns and approaches")
        print("  • Learn from technology choices and their outcomes")
        print("  • Provide context-aware, intelligent responses")
        print("  • Continuously improve recommendations based on success patterns")
        
        print("\n💡 This transforms Claude from having limited memory to unlimited context awareness!")
        print("   Claude can now remember and apply knowledge from EVERY past interaction.")

async def main():
    """Run the complete knowledge retrieval demo"""
    demo = KnowledgeRetrievalDemo()
    
    print("🚀 Starting BETTY Knowledge Retrieval System Demo...")
    print("This demo shows how Claude gets unlimited context awareness from all past work.")
    print("\nNote: This demo requires the BETTY Memory API to be running on localhost:8000")
    print("To start the API: cd memory-api && uvicorn main:app --host 0.0.0.0 --port 8000")
    
    # Wait for user to confirm API is running
    input("\nPress Enter when the API is running to continue with the demo...")
    
    await demo.demo_complete_workflow()
    demo.print_demo_summary()
    
    print(f"\n📚 API Documentation: http://localhost:8000/docs")
    print(f"🔍 API Health: http://localhost:8000/api/knowledge/retrieve/health")

if __name__ == "__main__":
    asyncio.run(main())