# ABOUTME: Knowledge Graph Analytics Service for Betty's Advanced Analytics Engine
# ABOUTME: Deep relationship analysis using Neo4j with advanced graph algorithms and network analysis

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
import structlog
from collections import defaultdict, Counter
import networkx as nx
from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import ServiceUnavailable, TransientError

from core.dependencies import DatabaseDependencies
from models.advanced_analytics import (
    PatternCorrelation, TimeSeriesPoint, PredictiveInsight,
    InsightType, PredictionConfidence
)
from models.knowledge import KnowledgeItem

logger = structlog.get_logger(__name__)


class GraphAnalyticsService:
    """
    Advanced Knowledge Graph Analytics Service providing deep relationship analysis,
    network centrality metrics, community detection, and graph-based insights
    """
    
    def __init__(self, databases: DatabaseDependencies):
        self.databases = databases
        self.neo4j = databases.neo4j
        
        # NetworkX graph for complex analysis
        self._knowledge_graph = nx.MultiDiGraph()
        self._last_graph_update = None
        self._graph_cache = {}
        
        # Graph analysis parameters
        self.centrality_algorithms = {
            'betweenness': nx.betweenness_centrality,
            'closeness': nx.closeness_centrality,
            'eigenvector': nx.eigenvector_centrality,
            'pagerank': nx.pagerank
        }
        
        # Community detection parameters
        self.community_resolution = 1.0
        self.min_community_size = 3
        
        # Performance optimization
        self.cache_ttl = timedelta(minutes=30)
        self.max_graph_size = 10000  # Limit for performance
    
    async def analyze_knowledge_network_structure(
        self, 
        project_filter: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Analyze the overall structure and topology of the knowledge network
        
        Args:
            project_filter: Specific project to analyze (None for all)
            time_range: Time range to filter knowledge items
            
        Returns:
            Comprehensive network structure analysis
        """
        logger.info("Analyzing knowledge network structure", 
                   project_filter=project_filter)
        
        try:
            # Build/update knowledge graph
            await self._build_knowledge_graph(project_filter, time_range)
            
            if self._knowledge_graph.number_of_nodes() == 0:
                return {"error": "No knowledge items found for analysis"}
            
            # Basic network metrics
            num_nodes = self._knowledge_graph.number_of_nodes()
            num_edges = self._knowledge_graph.number_of_edges()
            density = nx.density(self._knowledge_graph)
            
            # Convert to undirected for some metrics
            undirected_graph = self._knowledge_graph.to_undirected()
            
            # Connectivity analysis
            is_connected = nx.is_connected(undirected_graph)
            num_components = nx.number_connected_components(undirected_graph)
            largest_component_size = len(max(nx.connected_components(undirected_graph), key=len)) if num_components > 0 else 0
            
            # Centrality analysis
            centrality_metrics = await self._calculate_centrality_metrics(undirected_graph)
            
            # Clustering analysis
            clustering_coefficient = nx.average_clustering(undirected_graph)
            transitivity = nx.transitivity(undirected_graph)
            
            # Path analysis
            if is_connected and num_nodes > 1:
                avg_path_length = nx.average_shortest_path_length(undirected_graph)
                diameter = nx.diameter(undirected_graph)
            else:
                avg_path_length = float('inf')
                diameter = float('inf')
            
            # Degree distribution analysis
            degrees = [d for n, d in undirected_graph.degree()]
            degree_stats = {
                'mean': np.mean(degrees) if degrees else 0,
                'std': np.std(degrees) if degrees else 0,
                'max': max(degrees) if degrees else 0,
                'min': min(degrees) if degrees else 0
            }
            
            # Identify hub nodes (high degree centrality)
            hub_nodes = await self._identify_hub_nodes(centrality_metrics)
            
            # Community detection
            communities = await self._detect_communities(undirected_graph)
            
            # Network evolution analysis
            evolution_metrics = await self._analyze_network_evolution(time_range)
            
            analysis_result = {
                "network_overview": {
                    "total_nodes": num_nodes,
                    "total_edges": num_edges,
                    "network_density": float(density),
                    "is_connected": is_connected,
                    "connected_components": num_components,
                    "largest_component_size": largest_component_size,
                    "largest_component_ratio": largest_component_size / num_nodes if num_nodes > 0 else 0
                },
                "structural_metrics": {
                    "average_clustering_coefficient": float(clustering_coefficient),
                    "transitivity": float(transitivity),
                    "average_path_length": float(avg_path_length) if avg_path_length != float('inf') else None,
                    "network_diameter": diameter if diameter != float('inf') else None,
                    "degree_statistics": {k: float(v) for k, v in degree_stats.items()}
                },
                "centrality_analysis": centrality_metrics,
                "hub_nodes": hub_nodes,
                "community_structure": {
                    "total_communities": len(communities),
                    "communities": communities,
                    "modularity": await self._calculate_modularity(undirected_graph, communities)
                },
                "network_evolution": evolution_metrics,
                "network_health_score": self._calculate_network_health_score({
                    "density": density,
                    "clustering": clustering_coefficient,
                    "connectivity": largest_component_ratio,
                    "avg_path_length": avg_path_length if avg_path_length != float('inf') else 10
                }),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Network structure analysis completed", 
                       nodes=num_nodes, 
                       edges=num_edges,
                       communities=len(communities))
            
            return analysis_result
            
        except Exception as e:
            logger.error("Network structure analysis failed", error=str(e))
            raise
    
    async def discover_knowledge_pathways(
        self, 
        start_concept: str,
        end_concept: str,
        max_path_length: int = 5
    ) -> Dict[str, Any]:
        """
        Discover pathways between knowledge concepts using graph traversal
        
        Args:
            start_concept: Starting knowledge concept
            end_concept: Target knowledge concept  
            max_path_length: Maximum path length to search
            
        Returns:
            Knowledge pathways and relationship chains
        """
        logger.info("Discovering knowledge pathways", 
                   start=start_concept, 
                   end=end_concept,
                   max_length=max_path_length)
        
        try:
            # Ensure graph is updated
            await self._build_knowledge_graph()
            
            # Find nodes matching concepts
            start_nodes = await self._find_concept_nodes(start_concept)
            end_nodes = await self._find_concept_nodes(end_concept)
            
            if not start_nodes or not end_nodes:
                return {
                    "error": "Could not find nodes for specified concepts",
                    "start_nodes_found": len(start_nodes),
                    "end_nodes_found": len(end_nodes)
                }
            
            # Find all paths between start and end concepts
            all_paths = []
            path_strengths = []
            
            for start_node in start_nodes[:5]:  # Limit to top 5 for performance
                for end_node in end_nodes[:5]:
                    try:
                        # Find shortest paths
                        if nx.has_path(self._knowledge_graph, start_node, end_node):
                            paths = list(nx.all_shortest_paths(
                                self._knowledge_graph, 
                                start_node, 
                                end_node,
                                cutoff=max_path_length
                            ))
                            
                            for path in paths[:10]:  # Limit paths per node pair
                                # Calculate path strength based on edge weights
                                path_strength = self._calculate_path_strength(path)
                                path_info = await self._enrich_path_information(path)
                                
                                all_paths.append({
                                    "path": path,
                                    "path_info": path_info,
                                    "length": len(path) - 1,
                                    "strength": path_strength
                                })
                                path_strengths.append(path_strength)
                                
                    except nx.NetworkXNoPath:
                        continue
                    except Exception as path_error:
                        logger.warning("Path finding error", 
                                     start=start_node, 
                                     end=end_node,
                                     error=str(path_error))
            
            # Sort paths by strength and relevance
            all_paths.sort(key=lambda x: x["strength"], reverse=True)
            
            # Identify key intermediate concepts
            intermediate_concepts = self._identify_key_intermediates(all_paths)
            
            # Generate pathway insights
            pathway_insights = await self._generate_pathway_insights(
                all_paths, start_concept, end_concept
            )
            
            result = {
                "pathway_analysis": {
                    "start_concept": start_concept,
                    "end_concept": end_concept,
                    "total_pathways_found": len(all_paths),
                    "strongest_pathways": all_paths[:10],  # Top 10 strongest paths
                    "average_path_length": np.mean([p["length"] for p in all_paths]) if all_paths else 0,
                    "average_path_strength": np.mean(path_strengths) if path_strengths else 0
                },
                "key_intermediates": intermediate_concepts,
                "pathway_insights": pathway_insights,
                "relationship_patterns": await self._analyze_relationship_patterns(all_paths),
                "recommendations": self._generate_pathway_recommendations(all_paths, pathway_insights)
            }
            
            logger.info("Knowledge pathways discovered", 
                       total_paths=len(all_paths),
                       avg_length=result["pathway_analysis"]["average_path_length"])
            
            return result
            
        except Exception as e:
            logger.error("Knowledge pathway discovery failed", error=str(e))
            raise
    
    async def analyze_knowledge_influence_propagation(
        self, 
        seed_concepts: List[str],
        propagation_steps: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze how knowledge and influence propagate through the network
        
        Args:
            seed_concepts: Initial concepts to start propagation from
            propagation_steps: Number of steps to propagate
            
        Returns:
            Influence propagation analysis and impact metrics
        """
        logger.info("Analyzing knowledge influence propagation", 
                   seeds=len(seed_concepts),
                   steps=propagation_steps)
        
        try:
            await self._build_knowledge_graph()
            
            # Find seed nodes
            seed_nodes = []
            for concept in seed_concepts:
                nodes = await self._find_concept_nodes(concept)
                seed_nodes.extend(nodes[:3])  # Top 3 nodes per concept
            
            if not seed_nodes:
                return {"error": "No seed nodes found for specified concepts"}
            
            # Simulate influence propagation
            influence_scores = {node: 0.0 for node in self._knowledge_graph.nodes()}
            
            # Initialize seed nodes with full influence
            for seed_node in seed_nodes:
                influence_scores[seed_node] = 1.0
            
            # Propagate influence through the network
            propagation_history = []
            
            for step in range(propagation_steps):
                new_influence_scores = influence_scores.copy()
                step_changes = {}
                
                for node in self._knowledge_graph.nodes():
                    if influence_scores[node] > 0:
                        # Propagate to neighbors
                        neighbors = list(self._knowledge_graph.neighbors(node))
                        if neighbors:
                            influence_per_neighbor = influence_scores[node] * 0.7 / len(neighbors)
                            
                            for neighbor in neighbors:
                                # Get edge weight for influence calculation
                                edge_data = self._knowledge_graph.get_edge_data(node, neighbor, default={})
                                edge_weight = edge_data.get('weight', 0.5)
                                
                                influence_increase = influence_per_neighbor * edge_weight
                                new_influence_scores[neighbor] = min(1.0, 
                                    new_influence_scores[neighbor] + influence_increase)
                                
                                if neighbor not in step_changes:
                                    step_changes[neighbor] = 0
                                step_changes[neighbor] += influence_increase
                
                # Record step
                propagation_history.append({
                    "step": step + 1,
                    "total_influenced_nodes": len([s for s in new_influence_scores.values() if s > 0.1]),
                    "average_influence": np.mean(list(new_influence_scores.values())),
                    "top_influenced": sorted([
                        {"node": node, "influence": score} 
                        for node, score in new_influence_scores.items()
                    ], key=lambda x: x["influence"], reverse=True)[:10]
                })
                
                influence_scores = new_influence_scores
            
            # Identify most influenced nodes
            most_influenced = sorted([
                {"node": node, "influence_score": score, "node_info": await self._get_node_info(node)}
                for node, score in influence_scores.items()
                if score > 0.1
            ], key=lambda x: x["influence_score"], reverse=True)
            
            # Calculate propagation metrics
            total_influenced = len(most_influenced)
            propagation_reach = total_influenced / len(self._knowledge_graph.nodes()) if self._knowledge_graph.nodes() else 0
            
            # Identify influence clusters
            influence_clusters = self._identify_influence_clusters(influence_scores)
            
            # Generate propagation insights
            propagation_insights = self._generate_propagation_insights(
                seed_concepts, most_influenced, propagation_history
            )
            
            result = {
                "propagation_summary": {
                    "seed_concepts": seed_concepts,
                    "propagation_steps": propagation_steps,
                    "total_influenced_nodes": total_influenced,
                    "propagation_reach_percentage": float(propagation_reach * 100),
                    "average_final_influence": float(np.mean(list(influence_scores.values())))
                },
                "propagation_history": propagation_history,
                "most_influenced_concepts": most_influenced[:20],
                "influence_clusters": influence_clusters,
                "propagation_insights": propagation_insights,
                "network_effects": {
                    "amplification_factor": total_influenced / len(seed_nodes) if seed_nodes else 0,
                    "cascade_efficiency": propagation_reach / propagation_steps if propagation_steps > 0 else 0,
                    "influence_concentration": self._calculate_influence_concentration(influence_scores)
                }
            }
            
            logger.info("Influence propagation analysis completed", 
                       influenced_nodes=total_influenced,
                       reach_percentage=propagation_reach * 100)
            
            return result
            
        except Exception as e:
            logger.error("Influence propagation analysis failed", error=str(e))
            raise
    
    async def detect_knowledge_communities(
        self, 
        algorithm: str = "louvain",
        min_community_size: int = 3
    ) -> Dict[str, Any]:
        """
        Detect communities/clusters in the knowledge network
        
        Args:
            algorithm: Community detection algorithm to use
            min_community_size: Minimum size for a community
            
        Returns:
            Detected communities with analysis
        """
        logger.info("Detecting knowledge communities", 
                   algorithm=algorithm,
                   min_size=min_community_size)
        
        try:
            await self._build_knowledge_graph()
            
            if self._knowledge_graph.number_of_nodes() < min_community_size:
                return {"error": "Insufficient nodes for community detection"}
            
            # Convert to undirected for community detection
            undirected_graph = self._knowledge_graph.to_undirected()
            
            # Apply community detection algorithm
            if algorithm == "louvain":
                import community as community_louvain
                communities_dict = community_louvain.best_partition(undirected_graph)
            else:
                # Fallback to connected components
                communities_raw = list(nx.connected_components(undirected_graph))
                communities_dict = {}
                for i, community in enumerate(communities_raw):
                    for node in community:
                        communities_dict[node] = i
            
            # Group nodes by community
            communities = defaultdict(list)
            for node, community_id in communities_dict.items():
                communities[community_id].append(node)
            
            # Filter by minimum size
            filtered_communities = {
                comm_id: nodes for comm_id, nodes in communities.items()
                if len(nodes) >= min_community_size
            }
            
            # Analyze each community
            community_analysis = []
            for comm_id, nodes in filtered_communities.items():
                subgraph = undirected_graph.subgraph(nodes)
                
                # Calculate community metrics
                community_info = {
                    "community_id": comm_id,
                    "size": len(nodes),
                    "density": nx.density(subgraph),
                    "clustering_coefficient": nx.average_clustering(subgraph),
                    "internal_edges": subgraph.number_of_edges(),
                    "external_edges": self._count_external_edges(nodes, undirected_graph),
                    "central_nodes": await self._find_community_central_nodes(subgraph, nodes),
                    "dominant_themes": await self._identify_community_themes(nodes),
                    "creation_period": await self._analyze_community_timeline(nodes)
                }
                
                # Calculate community cohesion
                community_info["cohesion_score"] = self._calculate_community_cohesion(community_info)
                
                community_analysis.append(community_info)
            
            # Sort communities by size and cohesion
            community_analysis.sort(key=lambda x: (x["size"], x["cohesion_score"]), reverse=True)
            
            # Calculate overall modularity
            if algorithm == "louvain":
                modularity = community_louvain.modularity(communities_dict, undirected_graph)
            else:
                modularity = self._calculate_basic_modularity(filtered_communities, undirected_graph)
            
            # Generate community insights
            community_insights = await self._generate_community_insights(community_analysis)
            
            result = {
                "community_detection_summary": {
                    "algorithm_used": algorithm,
                    "total_communities_found": len(filtered_communities),
                    "total_nodes_in_communities": sum(len(nodes) for nodes in filtered_communities.values()),
                    "coverage_percentage": (sum(len(nodes) for nodes in filtered_communities.values()) / 
                                          self._knowledge_graph.number_of_nodes()) * 100,
                    "modularity_score": float(modularity),
                    "average_community_size": np.mean([len(nodes) for nodes in filtered_communities.values()])
                },
                "communities": community_analysis,
                "community_relationships": await self._analyze_inter_community_relationships(
                    filtered_communities, undirected_graph
                ),
                "community_insights": community_insights,
                "recommendations": self._generate_community_recommendations(community_analysis)
            }
            
            logger.info("Community detection completed", 
                       communities=len(filtered_communities),
                       modularity=modularity)
            
            return result
            
        except Exception as e:
            logger.error("Community detection failed", error=str(e))
            raise
    
    # Helper Methods
    
    async def _build_knowledge_graph(
        self, 
        project_filter: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ):
        """Build NetworkX graph from Neo4j knowledge data"""
        try:
            # Check if graph needs updating
            if (self._last_graph_update and 
                datetime.utcnow() - self._last_graph_update < self.cache_ttl and
                not project_filter):  # Don't use cache for filtered queries
                return
            
            self._knowledge_graph.clear()
            
            # Query Neo4j for knowledge items and relationships
            cypher_query = """
            MATCH (n:KnowledgeItem)
            OPTIONAL MATCH (n)-[r]->(m:KnowledgeItem)
            RETURN n, r, m
            LIMIT $limit
            """
            
            params = {"limit": self.max_graph_size}
            
            # Execute query (mock implementation for now)
            # In actual implementation, would query Neo4j database
            
            # Mock graph construction for demonstration
            await self._build_mock_knowledge_graph()
            
            self._last_graph_update = datetime.utcnow()
            
            logger.info("Knowledge graph built", 
                       nodes=self._knowledge_graph.number_of_nodes(),
                       edges=self._knowledge_graph.number_of_edges())
            
        except Exception as e:
            logger.error("Failed to build knowledge graph", error=str(e))
            raise
    
    async def _build_mock_knowledge_graph(self):
        """Build a mock knowledge graph for demonstration"""
        # Create sample nodes and relationships
        concepts = [
            "machine_learning", "data_science", "python", "algorithms", "statistics",
            "neural_networks", "deep_learning", "classification", "regression", "clustering",
            "feature_engineering", "model_validation", "hyperparameter_tuning", "deployment",
            "monitoring", "data_preprocessing", "visualization", "pandas", "scikit_learn", "tensorflow"
        ]
        
        # Add nodes
        for i, concept in enumerate(concepts):
            self._knowledge_graph.add_node(f"node_{i}", 
                                         concept=concept,
                                         created_at=datetime.utcnow() - timedelta(days=np.random.randint(0, 365)),
                                         quality_score=np.random.uniform(0.3, 1.0))
        
        # Add realistic relationships
        relationships = [
            (0, 1, 0.9),   # machine_learning -> data_science
            (1, 2, 0.8),   # data_science -> python
            (0, 3, 0.85),  # machine_learning -> algorithms
            (3, 4, 0.7),   # algorithms -> statistics
            (0, 5, 0.9),   # machine_learning -> neural_networks
            (5, 6, 0.95),  # neural_networks -> deep_learning
            (0, 7, 0.8),   # machine_learning -> classification
            (0, 8, 0.8),   # machine_learning -> regression
            (0, 9, 0.75),  # machine_learning -> clustering
            (1, 10, 0.85), # data_science -> feature_engineering
            (0, 11, 0.9),  # machine_learning -> model_validation
            (11, 12, 0.8), # model_validation -> hyperparameter_tuning
            (0, 13, 0.7),  # machine_learning -> deployment
            (13, 14, 0.8), # deployment -> monitoring
            (1, 15, 0.9),  # data_science -> data_preprocessing
            (1, 16, 0.8),  # data_science -> visualization
            (2, 17, 0.9),  # python -> pandas
            (2, 18, 0.85), # python -> scikit_learn
            (6, 19, 0.9),  # deep_learning -> tensorflow
        ]
        
        for source_idx, target_idx, weight in relationships:
            self._knowledge_graph.add_edge(
                f"node_{source_idx}", 
                f"node_{target_idx}",
                weight=weight,
                relationship_type="relates_to",
                strength=weight
            )
    
    async def _calculate_centrality_metrics(self, graph) -> Dict[str, Dict[str, float]]:
        """Calculate various centrality metrics for the graph"""
        centrality_results = {}
        
        try:
            # Calculate different centrality measures
            for name, algorithm in self.centrality_algorithms.items():
                try:
                    if name == 'eigenvector':
                        # Eigenvector centrality can be sensitive to disconnected graphs
                        if nx.is_connected(graph):
                            centrality_results[name] = algorithm(graph, max_iter=1000)
                        else:
                            centrality_results[name] = {node: 0.0 for node in graph.nodes()}
                    elif name == 'pagerank':
                        centrality_results[name] = algorithm(graph, alpha=0.85, max_iter=1000)
                    else:
                        centrality_results[name] = algorithm(graph)
                except Exception as centrality_error:
                    logger.warning(f"Centrality calculation failed for {name}", error=str(centrality_error))
                    centrality_results[name] = {node: 0.0 for node in graph.nodes()}
            
            # Summarize centrality metrics
            centrality_summary = {}
            for metric_name, values in centrality_results.items():
                if values:
                    centrality_summary[metric_name] = {
                        "mean": float(np.mean(list(values.values()))),
                        "std": float(np.std(list(values.values()))),
                        "max": float(max(values.values())),
                        "top_nodes": sorted([
                            {"node": node, "score": score} 
                            for node, score in values.items()
                        ], key=lambda x: x["score"], reverse=True)[:5]
                    }
            
            return centrality_summary
            
        except Exception as e:
            logger.error("Centrality calculation failed", error=str(e))
            return {}
    
    def _calculate_network_health_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall network health score based on multiple metrics"""
        try:
            # Weights for different aspects of network health
            weights = {
                "density": 0.2,        # Not too sparse, not too dense
                "clustering": 0.3,     # Good local connectivity
                "connectivity": 0.3,   # Well-connected network
                "avg_path_length": 0.2 # Efficient information flow
            }
            
            # Normalize metrics to 0-1 scale
            normalized_metrics = {}
            
            # Density: optimal around 0.1-0.3 for knowledge networks
            density = metrics.get("density", 0)
            if 0.1 <= density <= 0.3:
                normalized_metrics["density"] = 1.0
            else:
                normalized_metrics["density"] = max(0, 1 - abs(density - 0.2) / 0.2)
            
            # Clustering: higher is better
            normalized_metrics["clustering"] = min(1.0, metrics.get("clustering", 0))
            
            # Connectivity: higher ratio of largest component is better
            normalized_metrics["connectivity"] = min(1.0, metrics.get("connectivity", 0))
            
            # Average path length: shorter is better (normalize around optimal value of 3-6)
            avg_path_length = metrics.get("avg_path_length", 10)
            if 3 <= avg_path_length <= 6:
                normalized_metrics["avg_path_length"] = 1.0
            else:
                normalized_metrics["avg_path_length"] = max(0, 1 - abs(avg_path_length - 4.5) / 4.5)
            
            # Calculate weighted score
            health_score = sum(
                normalized_metrics[metric] * weights[metric]
                for metric in weights.keys()
            )
            
            return float(health_score)
            
        except Exception as e:
            logger.error("Network health score calculation failed", error=str(e))
            return 0.5  # Default moderate health score
    
    async def _find_concept_nodes(self, concept: str) -> List[str]:
        """Find nodes related to a specific concept"""
        matching_nodes = []
        
        for node, data in self._knowledge_graph.nodes(data=True):
            node_concept = data.get('concept', '').lower()
            if concept.lower() in node_concept or node_concept in concept.lower():
                matching_nodes.append(node)
        
        return matching_nodes[:10]  # Limit results
    
    def _calculate_path_strength(self, path: List[str]) -> float:
        """Calculate the strength of a path based on edge weights"""
        if len(path) < 2:
            return 0.0
        
        total_strength = 1.0
        for i in range(len(path) - 1):
            edge_data = self._knowledge_graph.get_edge_data(path[i], path[i + 1], default={})
            edge_weight = edge_data.get('weight', 0.5)
            total_strength *= edge_weight
        
        return total_strength
    
    async def _get_node_info(self, node: str) -> Dict[str, Any]:
        """Get detailed information about a node"""
        node_data = self._knowledge_graph.nodes.get(node, {})
        return {
            "concept": node_data.get('concept', 'unknown'),
            "created_at": node_data.get('created_at', datetime.utcnow()).isoformat(),
            "quality_score": node_data.get('quality_score', 0.5),
            "degree": self._knowledge_graph.degree(node) if node in self._knowledge_graph else 0
        }
    
    def _generate_pathway_recommendations(
        self, 
        pathways: List[Dict[str, Any]], 
        insights: List[str]
    ) -> List[str]:
        """Generate recommendations based on pathway analysis"""
        recommendations = []
        
        if not pathways:
            recommendations.append("No pathways found - consider creating connecting knowledge items")
            return recommendations
        
        # Analyze pathway characteristics
        avg_length = np.mean([p["length"] for p in pathways]) if pathways else 0
        strong_paths = [p for p in pathways if p["strength"] > 0.7]
        
        if avg_length > 4:
            recommendations.append("Pathways are long - consider creating direct connections")
        
        if len(strong_paths) < len(pathways) * 0.3:
            recommendations.append("Many weak pathways - strengthen key relationships")
        
        if len(pathways) == 1:
            recommendations.append("Single pathway found - create alternative routes for resilience")
        
        recommendations.append("Identify and strengthen critical intermediate concepts")
        
        return recommendations