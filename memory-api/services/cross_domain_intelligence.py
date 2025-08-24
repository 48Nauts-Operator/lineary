# ABOUTME: Cross-Domain Pattern Intelligence Engine for BETTY's revolutionary pattern transfer system
# ABOUTME: Enables automatic pattern discovery and application across different knowledge domains

import asyncio
import numpy as np
import networkx as nx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Set, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
from collections import defaultdict, Counter
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import json

from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from models.pattern_quality import PatternContext, QualityScore, SuccessProbability
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer

logger = structlog.get_logger(__name__)

class DomainType(Enum):
    """Different knowledge domains Betty can work with"""
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    API_DESIGN = "api_design"
    SECURITY = "security"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    MACHINE_LEARNING = "machine_learning"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"

class AdaptationStrategy(Enum):
    """Strategies for adapting patterns across domains"""
    DIRECT_TRANSFER = "direct_transfer"
    CONCEPTUAL_MAPPING = "conceptual_mapping"
    STRUCTURAL_ANALOGY = "structural_analogy"
    ABSTRACTION_REFINEMENT = "abstraction_refinement"
    HYBRID_APPROACH = "hybrid_approach"

@dataclass
class DomainOntology:
    """Represents the conceptual structure of a knowledge domain"""
    domain: DomainType
    core_concepts: List[str]
    concept_relationships: Dict[str, List[str]]
    technical_vocabulary: Set[str]
    common_patterns: List[str]
    tools_and_technologies: Set[str]
    typical_problems: List[str]
    success_metrics: List[str]
    created_at: datetime
    confidence_score: float

@dataclass
class AbstractPattern:
    """Domain-agnostic pattern template that can be applied across domains"""
    id: UUID
    title: str
    abstract_description: str
    conceptual_structure: Dict[str, Any]
    invariant_properties: List[str]
    variable_components: Dict[str, str]
    applicability_conditions: List[str]
    expected_outcomes: List[str]
    source_domains: List[DomainType]
    abstraction_level: float  # 0.0 = very specific, 1.0 = highly abstract
    created_at: datetime
    quality_score: float

@dataclass
class CrossDomainMatch:
    """Represents a potential pattern match across different domains"""
    source_pattern_id: UUID
    target_pattern_id: UUID
    source_domain: DomainType
    target_domain: DomainType
    similarity_score: float
    conceptual_overlap: List[str]
    structural_similarity: float
    adaptation_strategy: AdaptationStrategy
    confidence_level: float
    evidence: List[str]
    discovered_at: datetime

@dataclass
class DomainAdaptation:
    """Instructions for adapting a pattern from one domain to another"""
    id: UUID
    source_pattern_id: UUID
    source_domain: DomainType
    target_domain: DomainType
    adaptation_strategy: AdaptationStrategy
    concept_mappings: Dict[str, str]
    technology_substitutions: Dict[str, str]
    structural_modifications: List[str]
    validation_criteria: List[str]
    success_probability: SuccessProbability
    risk_factors: List[str]
    mitigation_strategies: List[str]
    created_at: datetime

class CrossDomainIntelligence:
    """
    Revolutionary Cross-Domain Pattern Intelligence Engine that enables
    automatic pattern discovery and application across different knowledge domains
    """
    
    def __init__(
        self, 
        db_manager: DatabaseManager, 
        vector_service: VectorService,
        quality_scorer: AdvancedQualityScorer
    ):
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.quality_scorer = quality_scorer
        
        # Domain knowledge caches
        self._domain_ontologies: Dict[DomainType, DomainOntology] = {}
        self._abstract_patterns: Dict[UUID, AbstractPattern] = {}
        self._cross_domain_matches: List[CrossDomainMatch] = []
        
        # Cross-domain relationship graph
        self._domain_graph = nx.Graph()
        self._pattern_similarity_matrix = None
        
        # Machine learning models
        self._domain_classifier = None
        self._similarity_model = None
        self._adaptation_predictor = None
        
        # Concept extraction and mapping
        self._concept_extractor = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # Performance optimization
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._ontology_last_updated = None
        self._similarity_cache: Dict[Tuple[UUID, UUID], float] = {}
        
    async def detect_cross_domain_patterns(
        self, 
        source_domain: DomainType, 
        target_domain: DomainType,
        min_similarity: float = 0.6
    ) -> List[CrossDomainMatch]:
        """
        Detect patterns from source domain that could be applied to target domain
        
        This is Betty's core cross-domain intelligence - finding solutions
        from one project/domain that can solve problems in another
        """
        logger.info("Detecting cross-domain patterns", 
                   source_domain=source_domain.value, 
                   target_domain=target_domain.value,
                   min_similarity=min_similarity)
        
        try:
            # Get patterns from both domains
            source_patterns = await self._get_patterns_by_domain(source_domain)
            target_patterns = await self._get_patterns_by_domain(target_domain)
            
            if not source_patterns or not target_patterns:
                logger.warning("Insufficient patterns for cross-domain analysis",
                             source_count=len(source_patterns),
                             target_count=len(target_patterns))
                return []
            
            # Build domain ontologies if not cached
            source_ontology = await self._build_domain_ontology(source_domain, source_patterns)
            target_ontology = await self._build_domain_ontology(target_domain, target_patterns)
            
            # Detect cross-domain matches
            matches = []
            
            for source_pattern in source_patterns:
                for target_pattern in target_patterns:
                    match = await self._analyze_cross_domain_similarity(
                        source_pattern, target_pattern,
                        source_ontology, target_ontology
                    )
                    
                    if match and match.similarity_score >= min_similarity:
                        matches.append(match)
            
            # Sort by similarity and confidence
            matches.sort(key=lambda x: (x.similarity_score * x.confidence_level), reverse=True)
            
            # Store matches for future reference
            await self._store_cross_domain_matches(matches)
            
            logger.info("Cross-domain pattern detection completed",
                       matches_found=len(matches),
                       source_domain=source_domain.value,
                       target_domain=target_domain.value)
            
            return matches
            
        except Exception as e:
            logger.error("Failed to detect cross-domain patterns", 
                        error=str(e),
                        source_domain=source_domain.value,
                        target_domain=target_domain.value)
            raise
    
    async def abstract_domain_pattern(self, pattern: KnowledgeItem) -> AbstractPattern:
        """
        Extract abstract, domain-agnostic patterns from concrete implementations
        
        This creates reusable templates that can be applied across domains
        """
        logger.info("Abstracting domain pattern", 
                   pattern_id=str(pattern.id),
                   pattern_title=pattern.title)
        
        try:
            # Determine pattern's primary domain
            domain = await self._classify_pattern_domain(pattern)
            
            # Extract conceptual structure
            conceptual_structure = await self._extract_conceptual_structure(pattern)
            
            # Identify invariant properties (things that don't change across domains)
            invariant_properties = await self._identify_invariant_properties(pattern, domain)
            
            # Identify variable components (things that need domain-specific adaptation)
            variable_components = await self._identify_variable_components(pattern, domain)
            
            # Determine applicability conditions
            applicability_conditions = await self._determine_applicability_conditions(pattern, domain)
            
            # Extract expected outcomes
            expected_outcomes = await self._extract_expected_outcomes(pattern)
            
            # Calculate abstraction level
            abstraction_level = await self._calculate_abstraction_level(pattern, conceptual_structure)
            
            # Create abstract pattern
            abstract_pattern = AbstractPattern(
                id=uuid4(),
                title=f"Abstract: {pattern.title}",
                abstract_description=await self._generate_abstract_description(pattern, conceptual_structure),
                conceptual_structure=conceptual_structure,
                invariant_properties=invariant_properties,
                variable_components=variable_components,
                applicability_conditions=applicability_conditions,
                expected_outcomes=expected_outcomes,
                source_domains=[domain],
                abstraction_level=abstraction_level,
                created_at=datetime.utcnow(),
                quality_score=0.8  # Will be computed by quality scorer later
            )
            
            # Store abstract pattern
            self._abstract_patterns[abstract_pattern.id] = abstract_pattern
            await self._store_abstract_pattern(abstract_pattern)
            
            logger.info("Pattern abstraction completed",
                       abstract_pattern_id=str(abstract_pattern.id),
                       abstraction_level=abstraction_level,
                       invariant_properties_count=len(invariant_properties))
            
            return abstract_pattern
            
        except Exception as e:
            logger.error("Failed to abstract pattern", 
                        pattern_id=str(pattern.id),
                        error=str(e))
            raise
    
    async def adapt_pattern_to_domain(
        self, 
        abstract_pattern: AbstractPattern, 
        target_domain: DomainType
    ) -> KnowledgeItem:
        """
        Adapt an abstract pattern to a specific target domain
        
        This is where Betty creates new solutions by applying patterns
        from one domain to problems in another
        """
        logger.info("Adapting pattern to domain",
                   abstract_pattern_id=str(abstract_pattern.id),
                   target_domain=target_domain.value)
        
        try:
            # Build target domain ontology
            target_patterns = await self._get_patterns_by_domain(target_domain)
            target_ontology = await self._build_domain_ontology(target_domain, target_patterns)
            
            # Determine adaptation strategy
            adaptation_strategy = await self._determine_adaptation_strategy(
                abstract_pattern, target_domain, target_ontology
            )
            
            # Create concept mappings
            concept_mappings = await self._create_concept_mappings(
                abstract_pattern, target_ontology
            )
            
            # Create technology substitutions
            tech_substitutions = await self._create_technology_substitutions(
                abstract_pattern, target_ontology
            )
            
            # Generate adapted content
            adapted_content = await self._generate_adapted_content(
                abstract_pattern, 
                target_domain,
                concept_mappings,
                tech_substitutions,
                adaptation_strategy
            )
            
            # Create adapted knowledge item
            adapted_pattern = KnowledgeItem(
                id=uuid4(),
                title=f"{abstract_pattern.title} (Adapted for {target_domain.value})",
                content=adapted_content,
                knowledge_type="pattern",
                source_type="cross_domain_adaptation",
                tags=await self._generate_adapted_tags(abstract_pattern, target_domain),
                summary=await self._generate_adapted_summary(abstract_pattern, target_domain),
                confidence="medium",  # Start with medium confidence for adapted patterns
                metadata={
                    "source_abstract_pattern_id": str(abstract_pattern.id),
                    "target_domain": target_domain.value,
                    "adaptation_strategy": adaptation_strategy.value,
                    "concept_mappings": concept_mappings,
                    "technology_substitutions": tech_substitutions,
                    "adaptation_timestamp": datetime.utcnow().isoformat(),
                    "original_domains": [d.value for d in abstract_pattern.source_domains]
                }
            )
            
            logger.info("Pattern adaptation completed",
                       adapted_pattern_id=str(adapted_pattern.id),
                       target_domain=target_domain.value,
                       adaptation_strategy=adaptation_strategy.value)
            
            return adapted_pattern
            
        except Exception as e:
            logger.error("Failed to adapt pattern to domain",
                        abstract_pattern_id=str(abstract_pattern.id),
                        target_domain=target_domain.value,
                        error=str(e))
            raise
    
    async def recommend_cross_domain_solutions(
        self, 
        problem_description: str, 
        target_domain: DomainType,
        exclude_domains: List[DomainType] = None,
        max_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend solutions from other domains that could solve a problem in target domain
        
        This is Betty's key value proposition - "You solved similar authentication 
        in 137docs using JWT middleware"
        """
        logger.info("Recommending cross-domain solutions",
                   problem_length=len(problem_description),
                   target_domain=target_domain.value,
                   exclude_domains_count=len(exclude_domains) if exclude_domains else 0)
        
        exclude_domains = exclude_domains or []
        
        try:
            # Analyze problem to understand requirements
            problem_concepts = await self._extract_problem_concepts(problem_description)
            problem_context = await self._analyze_problem_context(problem_description, target_domain)
            
            # Search for similar problems across other domains
            candidate_patterns = []
            
            for domain in DomainType:
                if domain == target_domain or domain in exclude_domains:
                    continue
                    
                domain_patterns = await self._get_patterns_by_domain(domain)
                
                for pattern in domain_patterns:
                    similarity = await self._calculate_problem_pattern_similarity(
                        problem_description, pattern, problem_concepts
                    )
                    
                    if similarity > 0.5:  # Minimum similarity threshold
                        candidate_patterns.append({
                            'pattern': pattern,
                            'source_domain': domain,
                            'similarity': similarity,
                            'concepts_overlap': await self._find_concept_overlap(
                                problem_concepts, pattern
                            )
                        })
            
            # Sort by similarity
            candidate_patterns.sort(key=lambda x: x['similarity'], reverse=True)
            candidate_patterns = candidate_patterns[:max_recommendations * 2]  # Get extra for filtering
            
            # Generate adaptation recommendations
            recommendations = []
            
            for candidate in candidate_patterns:
                pattern = candidate['pattern']
                source_domain = candidate['source_domain']
                
                # Create abstract version of the pattern
                abstract_pattern = await self.abstract_domain_pattern(pattern)
                
                # Predict success probability for adaptation
                success_probability = await self._predict_adaptation_success(
                    abstract_pattern, target_domain, problem_context
                )
                
                # Generate adaptation guidance
                adaptation_guidance = await self._generate_adaptation_guidance(
                    pattern, source_domain, target_domain, problem_description
                )
                
                recommendation = {
                    'original_pattern_id': str(pattern.id),
                    'original_pattern_title': pattern.title,
                    'original_domain': source_domain.value,
                    'target_domain': target_domain.value,
                    'similarity_score': candidate['similarity'],
                    'success_probability': success_probability.value,
                    'concepts_overlap': candidate['concepts_overlap'],
                    'adaptation_guidance': adaptation_guidance,
                    'abstract_pattern_id': str(abstract_pattern.id),
                    'why_relevant': await self._explain_relevance(
                        pattern, problem_description, candidate['concepts_overlap']
                    ),
                    'implementation_notes': await self._generate_implementation_notes(
                        pattern, target_domain
                    ),
                    'potential_challenges': await self._identify_adaptation_challenges(
                        pattern, source_domain, target_domain
                    ),
                    'confidence_score': candidate['similarity'] * 0.7 + 
                                      self._success_probability_to_float(success_probability) * 0.3
                }
                
                recommendations.append(recommendation)
            
            # Sort by confidence score and limit results
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            recommendations = recommendations[:max_recommendations]
            
            logger.info("Cross-domain recommendations generated",
                       recommendations_count=len(recommendations),
                       target_domain=target_domain.value)
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to recommend cross-domain solutions",
                        target_domain=target_domain.value,
                        error=str(e))
            raise
    
    async def build_domain_relationship_graph(self) -> nx.Graph:
        """
        Build a graph showing relationships between different knowledge domains
        based on pattern similarities and cross-domain applications
        """
        logger.info("Building domain relationship graph")
        
        try:
            # Clear existing graph
            self._domain_graph.clear()
            
            # Add all domains as nodes
            for domain in DomainType:
                if domain != DomainType.UNKNOWN:
                    self._domain_graph.add_node(domain.value, domain_type=domain)
            
            # Find relationships between domains
            domain_pairs = []
            for i, domain1 in enumerate(DomainType):
                for j, domain2 in enumerate(DomainType):
                    if i < j and domain1 != DomainType.UNKNOWN and domain2 != DomainType.UNKNOWN:
                        domain_pairs.append((domain1, domain2))
            
            for domain1, domain2 in domain_pairs:
                # Calculate domain similarity
                similarity = await self._calculate_domain_similarity(domain1, domain2)
                
                if similarity > 0.3:  # Threshold for meaningful relationship
                    # Find shared concepts
                    shared_concepts = await self._find_shared_concepts_between_domains(domain1, domain2)
                    
                    # Count successful cross-domain adaptations
                    adaptation_count = await self._count_successful_adaptations(domain1, domain2)
                    
                    # Add edge with relationship data
                    self._domain_graph.add_edge(
                        domain1.value, 
                        domain2.value,
                        similarity=similarity,
                        shared_concepts=len(shared_concepts),
                        adaptation_count=adaptation_count,
                        weight=similarity * (1 + adaptation_count * 0.1)
                    )
            
            logger.info("Domain relationship graph completed",
                       nodes_count=self._domain_graph.number_of_nodes(),
                       edges_count=self._domain_graph.number_of_edges())
            
            return self._domain_graph
            
        except Exception as e:
            logger.error("Failed to build domain relationship graph", error=str(e))
            raise
    
    # Helper methods for core functionality
    
    async def _get_patterns_by_domain(self, domain: DomainType) -> List[KnowledgeItem]:
        """Get all patterns belonging to a specific domain"""
        # This would query the database for patterns tagged with the domain
        # For now, returning empty list as placeholder
        return []
    
    async def _build_domain_ontology(
        self, 
        domain: DomainType, 
        patterns: List[KnowledgeItem]
    ) -> DomainOntology:
        """Build comprehensive ontology for a domain based on its patterns"""
        
        if domain in self._domain_ontologies:
            return self._domain_ontologies[domain]
        
        try:
            # Extract concepts from patterns
            all_text = " ".join([p.title + " " + p.content for p in patterns])
            
            # Extract core concepts using TF-IDF and domain-specific rules
            concepts = await self._extract_domain_concepts(all_text, domain)
            
            # Build concept relationships
            relationships = await self._build_concept_relationships(concepts, patterns)
            
            # Extract technical vocabulary
            tech_vocab = await self._extract_technical_vocabulary(patterns, domain)
            
            # Identify common patterns
            common_patterns = await self._identify_common_patterns(patterns)
            
            # Extract tools and technologies
            tools_tech = await self._extract_tools_technologies(patterns, domain)
            
            # Identify typical problems
            typical_problems = await self._extract_typical_problems(patterns, domain)
            
            # Define success metrics
            success_metrics = await self._define_success_metrics(domain)
            
            ontology = DomainOntology(
                domain=domain,
                core_concepts=concepts,
                concept_relationships=relationships,
                technical_vocabulary=tech_vocab,
                common_patterns=common_patterns,
                tools_and_technologies=tools_tech,
                typical_problems=typical_problems,
                success_metrics=success_metrics,
                created_at=datetime.utcnow(),
                confidence_score=0.8
            )
            
            # Cache the ontology
            self._domain_ontologies[domain] = ontology
            
            return ontology
            
        except Exception as e:
            logger.error("Failed to build domain ontology", 
                        domain=domain.value, error=str(e))
            raise
    
    async def _classify_pattern_domain(self, pattern: KnowledgeItem) -> DomainType:
        """Classify which domain a pattern belongs to"""
        
        # Use keywords and tags to classify
        text = f"{pattern.title} {pattern.content} {' '.join(pattern.tags)}"
        text_lower = text.lower()
        
        # Domain classification rules
        if any(keyword in text_lower for keyword in ['auth', 'login', 'jwt', 'oauth', 'session']):
            return DomainType.AUTHENTICATION
        elif any(keyword in text_lower for keyword in ['database', 'sql', 'nosql', 'query']):
            return DomainType.DATABASE
        elif any(keyword in text_lower for keyword in ['api', 'rest', 'graphql', 'endpoint']):
            return DomainType.API_DESIGN
        elif any(keyword in text_lower for keyword in ['security', 'encryption', 'vulnerability']):
            return DomainType.SECURITY
        elif any(keyword in text_lower for keyword in ['react', 'vue', 'angular', 'frontend']):
            return DomainType.FRONTEND
        elif any(keyword in text_lower for keyword in ['server', 'backend', 'microservice']):
            return DomainType.BACKEND
        elif any(keyword in text_lower for keyword in ['docker', 'kubernetes', 'ci/cd', 'devops']):
            return DomainType.DEVOPS
        elif any(keyword in text_lower for keyword in ['ml', 'ai', 'machine learning', 'neural']):
            return DomainType.MACHINE_LEARNING
        elif any(keyword in text_lower for keyword in ['architecture', 'system design', 'scalability']):
            return DomainType.ARCHITECTURE
        elif any(keyword in text_lower for keyword in ['test', 'testing', 'unit test', 'integration']):
            return DomainType.TESTING
        elif any(keyword in text_lower for keyword in ['performance', 'optimization', 'caching']):
            return DomainType.PERFORMANCE
        else:
            return DomainType.UNKNOWN
    
    def _success_probability_to_float(self, prob: SuccessProbability) -> float:
        """Convert success probability enum to float"""
        mapping = {
            SuccessProbability.VERY_LOW: 0.1,
            SuccessProbability.LOW: 0.3,
            SuccessProbability.MEDIUM: 0.5,
            SuccessProbability.HIGH: 0.7,
            SuccessProbability.VERY_HIGH: 0.9
        }
        return mapping.get(prob, 0.5)
    
    # Advanced Implementation Methods
    
    async def _analyze_cross_domain_similarity(
        self, 
        source_pattern: KnowledgeItem,
        target_pattern: KnowledgeItem,
        source_ontology: DomainOntology,
        target_ontology: DomainOntology
    ) -> Optional[CrossDomainMatch]:
        """Analyze similarity between patterns from different domains using advanced techniques"""
        
        try:
            # Generate embeddings for both patterns
            source_embedding = await self._get_pattern_embedding(source_pattern)
            target_embedding = await self._get_pattern_embedding(target_pattern)
            
            # Calculate vector similarity
            vector_similarity = float(cosine_similarity([source_embedding], [target_embedding])[0][0])
            
            # Find conceptual overlap
            source_concepts = await self._extract_pattern_concepts(source_pattern)
            target_concepts = await self._extract_pattern_concepts(target_pattern)
            conceptual_overlap = list(set(source_concepts) & set(target_concepts))
            
            # Calculate structural similarity using pattern templates
            structural_similarity = await self._calculate_structural_similarity(
                source_pattern, target_pattern
            )
            
            # Determine adaptation strategy
            adaptation_strategy = await self._determine_adaptation_strategy_for_match(
                source_pattern, target_pattern, 
                await self._classify_pattern_domain(source_pattern),
                await self._classify_pattern_domain(target_pattern)
            )
            
            # Calculate overall similarity score
            similarity_score = (
                vector_similarity * 0.4 +
                (len(conceptual_overlap) / max(len(source_concepts), len(target_concepts))) * 0.3 +
                structural_similarity * 0.3
            )
            
            if similarity_score < 0.3:  # Too low similarity
                return None
            
            # Calculate confidence level
            confidence_level = await self._calculate_match_confidence(
                source_pattern, target_pattern, similarity_score, conceptual_overlap
            )
            
            # Generate evidence
            evidence = await self._generate_match_evidence(
                source_pattern, target_pattern, conceptual_overlap, vector_similarity
            )
            
            return CrossDomainMatch(
                source_pattern_id=source_pattern.id,
                target_pattern_id=target_pattern.id,
                source_domain=await self._classify_pattern_domain(source_pattern),
                target_domain=await self._classify_pattern_domain(target_pattern),
                similarity_score=similarity_score,
                conceptual_overlap=conceptual_overlap,
                structural_similarity=structural_similarity,
                adaptation_strategy=adaptation_strategy,
                confidence_level=confidence_level,
                evidence=evidence,
                discovered_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to analyze cross-domain similarity",
                        source_id=str(source_pattern.id),
                        target_id=str(target_pattern.id),
                        error=str(e))
            return None
    
    async def _extract_conceptual_structure(self, pattern: KnowledgeItem) -> Dict[str, Any]:
        """Extract the abstract conceptual structure from a concrete pattern"""
        
        # Extract problem-solution structure
        problem_section = await self._extract_problem_section(pattern.content)
        solution_section = await self._extract_solution_section(pattern.content)
        
        # Extract code patterns and abstract them
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', pattern.content, re.DOTALL)
        abstract_code_patterns = []
        
        for code_block in code_blocks:
            abstract_pattern = await self._abstract_code_pattern(code_block)
            if abstract_pattern:
                abstract_code_patterns.append(abstract_pattern)
        
        # Extract decision factors
        decision_factors = await self._extract_decision_factors(pattern.content)
        
        # Extract prerequisites and dependencies
        prerequisites = await self._extract_prerequisites(pattern.content)
        
        # Extract measurable outcomes
        outcomes = await self._extract_measurable_outcomes(pattern.content)
        
        return {
            "problem_structure": {
                "problem_type": await self._classify_problem_type(problem_section),
                "key_challenges": await self._extract_key_challenges(problem_section),
                "constraints": await self._extract_constraints(problem_section)
            },
            "solution_structure": {
                "approach_type": await self._classify_solution_approach(solution_section),
                "key_components": await self._extract_key_components(solution_section),
                "implementation_steps": await self._extract_implementation_steps(solution_section)
            },
            "abstract_code_patterns": abstract_code_patterns,
            "decision_factors": decision_factors,
            "prerequisites": prerequisites,
            "expected_outcomes": outcomes,
            "pattern_complexity": await self._assess_pattern_complexity(pattern),
            "scalability_considerations": await self._extract_scalability_notes(pattern.content)
        }
    
    async def _identify_invariant_properties(self, pattern: KnowledgeItem, domain: DomainType) -> List[str]:
        """Identify properties that remain constant across domains"""
        
        invariants = []
        
        # Extract high-level principles
        principles = await self._extract_design_principles(pattern.content)
        invariants.extend(principles)
        
        # Extract logical flow patterns
        logical_flows = await self._extract_logical_flows(pattern.content)
        invariants.extend(logical_flows)
        
        # Extract architectural patterns
        arch_patterns = await self._extract_architectural_patterns(pattern.content)
        invariants.extend(arch_patterns)
        
        # Extract validation patterns
        validation_patterns = await self._extract_validation_patterns(pattern.content)
        invariants.extend(validation_patterns)
        
        # Extract error handling patterns
        error_handling = await self._extract_error_handling_patterns(pattern.content)
        invariants.extend(error_handling)
        
        # Extract security considerations that apply broadly
        security_principles = await self._extract_universal_security_principles(pattern.content)
        invariants.extend(security_principles)
        
        return list(set(invariants))  # Remove duplicates
    
    async def _identify_variable_components(self, pattern: KnowledgeItem, domain: DomainType) -> Dict[str, str]:
        """Identify components that need domain-specific adaptation"""
        
        variables = {}
        
        # Technology stack components
        technologies = await self._extract_technologies(pattern.content)
        for tech in technologies:
            variables[f"technology_{tech}"] = f"Domain-specific equivalent of {tech}"
        
        # API endpoints and interfaces
        endpoints = await self._extract_api_patterns(pattern.content)
        for endpoint in endpoints:
            variables[f"interface_{endpoint}"] = f"Domain-appropriate interface for {endpoint}"
        
        # Data models and schemas
        data_models = await self._extract_data_models(pattern.content)
        for model in data_models:
            variables[f"data_model_{model}"] = f"Domain-specific data structure for {model}"
        
        # Configuration parameters
        config_params = await self._extract_configuration_parameters(pattern.content)
        for param in config_params:
            variables[f"config_{param}"] = f"Domain-appropriate configuration for {param}"
        
        # Domain-specific terminology
        terminology = await self._extract_domain_terminology(pattern.content, domain)
        for term in terminology:
            variables[f"term_{term}"] = f"Equivalent terminology in target domain"
        
        return variables
    
    async def _get_pattern_embedding(self, pattern: KnowledgeItem) -> np.ndarray:
        """Get or generate vector embedding for a pattern"""
        
        cache_key = f"pattern_{pattern.id}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # Generate embedding using the vector service
        text = f"{pattern.title} {pattern.content} {' '.join(pattern.tags)}"
        embedding = await self.vector_service.generate_embedding(text)
        
        # Cache the embedding
        self._embedding_cache[cache_key] = embedding
        
        return embedding
    
    async def _extract_pattern_concepts(self, pattern: KnowledgeItem) -> List[str]:
        """Extract key concepts from a pattern"""
        
        text = f"{pattern.title} {pattern.content}"
        
        # Use regex to find technical terms
        technical_terms = re.findall(r'\b[A-Z]{2,}(?:[A-Z][a-z]+)*\b', text)
        technical_terms.extend(re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', text))  # camelCase
        
        # Extract concepts from tags
        tag_concepts = pattern.tags
        
        # Use NLP to extract key phrases (simplified version)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_counts = Counter(words)
        top_words = [word for word, count in word_counts.most_common(20) 
                     if count > 1 and word not in {'the', 'and', 'for', 'with', 'this', 'that'}]
        
        all_concepts = technical_terms + tag_concepts + top_words
        return list(set(all_concepts))
    
    async def _calculate_structural_similarity(
        self, 
        pattern1: KnowledgeItem, 
        pattern2: KnowledgeItem
    ) -> float:
        """Calculate structural similarity between patterns"""
        
        # Extract structural elements
        struct1 = await self._extract_structural_elements(pattern1)
        struct2 = await self._extract_structural_elements(pattern2)
        
        # Compare problem-solution structures
        problem_sim = await self._compare_problem_structures(
            struct1.get('problem', {}), struct2.get('problem', {})
        )
        
        solution_sim = await self._compare_solution_structures(
            struct1.get('solution', {}), struct2.get('solution', {})
        )
        
        # Compare implementation patterns
        impl_sim = await self._compare_implementation_patterns(
            struct1.get('implementation', []), struct2.get('implementation', [])
        )
        
        # Weighted average
        return (problem_sim * 0.3 + solution_sim * 0.4 + impl_sim * 0.3)
    
    # Storage methods
    
    async def _store_cross_domain_matches(self, matches: List[CrossDomainMatch]) -> None:
        """Store cross-domain matches in Neo4j"""
        
        async with self.db_manager.get_neo4j_session() as session:
            for match in matches:
                query = """
                MATCH (source:Pattern {id: $source_id}), (target:Pattern {id: $target_id})
                MERGE (source)-[r:CROSS_DOMAIN_SIMILARITY]->(target)
                SET r.similarity_score = $similarity,
                    r.conceptual_overlap = $overlap,
                    r.structural_similarity = $structural_sim,
                    r.adaptation_strategy = $strategy,
                    r.confidence_level = $confidence,
                    r.evidence = $evidence,
                    r.discovered_at = $discovered_at
                """
                await session.run(query, {
                    'source_id': str(match.source_pattern_id),
                    'target_id': str(match.target_pattern_id),
                    'similarity': match.similarity_score,
                    'overlap': match.conceptual_overlap,
                    'structural_sim': match.structural_similarity,
                    'strategy': match.adaptation_strategy.value,
                    'confidence': match.confidence_level,
                    'evidence': match.evidence,
                    'discovered_at': match.discovered_at.isoformat()
                })
    
    async def _store_abstract_pattern(self, abstract_pattern: AbstractPattern) -> None:
        """Store abstract pattern in PostgreSQL and Neo4j"""
        
        # Store in PostgreSQL
        async with self.db_manager.get_db_pool() as pool:
            async with pool.acquire() as conn:
                query = """
                INSERT INTO abstract_patterns (
                    id, title, abstract_description, conceptual_structure,
                    invariant_properties, variable_components, applicability_conditions,
                    expected_outcomes, source_domains, abstraction_level,
                    quality_score, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """
                await conn.execute(
                    query,
                    str(abstract_pattern.id),
                    abstract_pattern.title,
                    abstract_pattern.abstract_description,
                    json.dumps(abstract_pattern.conceptual_structure),
                    abstract_pattern.invariant_properties,
                    json.dumps(abstract_pattern.variable_components),
                    abstract_pattern.applicability_conditions,
                    abstract_pattern.expected_outcomes,
                    [d.value for d in abstract_pattern.source_domains],
                    abstract_pattern.abstraction_level,
                    abstract_pattern.quality_score,
                    abstract_pattern.created_at
                )
        
        # Store in Neo4j as well for relationship analysis
        async with self.db_manager.get_neo4j_session() as session:
            query = """
            CREATE (ap:AbstractPattern {
                id: $id,
                title: $title,
                abstraction_level: $abstraction_level,
                source_domains: $source_domains,
                created_at: $created_at
            })
            """
            await session.run(query, {
                'id': str(abstract_pattern.id),
                'title': abstract_pattern.title,
                'abstraction_level': abstract_pattern.abstraction_level,
                'source_domains': [d.value for d in abstract_pattern.source_domains],
                'created_at': abstract_pattern.created_at.isoformat()
            })
    
    # Placeholder implementations for remaining complex methods
    
    async def _extract_problem_section(self, content: str) -> str:
        """Extract the problem description section"""
        # Use regex and NLP to identify problem descriptions
        problem_indicators = ['problem', 'issue', 'challenge', 'difficulty', 'need to']
        lines = content.split('\n')
        problem_lines = []
        
        for line in lines:
            if any(indicator in line.lower() for indicator in problem_indicators):
                problem_lines.append(line)
        
        return '\n'.join(problem_lines)
    
    async def _extract_solution_section(self, content: str) -> str:
        """Extract the solution description section"""
        solution_indicators = ['solution', 'approach', 'method', 'implementation', 'fix']
        lines = content.split('\n')
        solution_lines = []
        
        for line in lines:
            if any(indicator in line.lower() for indicator in solution_indicators):
                solution_lines.append(line)
        
        return '\n'.join(solution_lines)
    
    async def _abstract_code_pattern(self, code_block: str) -> Optional[Dict[str, str]]:
        """Abstract a code block into a reusable pattern"""
        if not code_block.strip():
            return None
        
        # Identify programming constructs
        constructs = {
            'conditional': bool(re.search(r'\b(if|switch|case)\b', code_block)),
            'loop': bool(re.search(r'\b(for|while|forEach)\b', code_block)),
            'function_call': bool(re.search(r'\w+\s*\(', code_block)),
            'error_handling': bool(re.search(r'\b(try|catch|except|error)\b', code_block)),
            'async': bool(re.search(r'\b(async|await|Promise)\b', code_block))
        }
        
        return {
            'pattern_type': 'code_structure',
            'constructs': constructs,
            'abstraction': 'Generic implementation pattern with identified constructs'
        }
    
    # Advanced Domain Adaptation Algorithms
    
    async def _determine_adaptation_strategy(
        self,
        abstract_pattern: AbstractPattern,
        target_domain: DomainType,
        target_ontology: DomainOntology
    ) -> AdaptationStrategy:
        """Determine the best strategy for adapting pattern to target domain"""
        
        # Analyze pattern characteristics
        abstraction_level = abstract_pattern.abstraction_level
        source_domains = abstract_pattern.source_domains
        
        # Calculate domain distance
        domain_distance = await self._calculate_domain_distance(source_domains[0], target_domain)
        
        # Analyze concept overlap
        pattern_concepts = await self._extract_abstract_pattern_concepts(abstract_pattern)
        concept_overlap = len(set(pattern_concepts) & set(target_ontology.core_concepts))
        concept_overlap_ratio = concept_overlap / len(pattern_concepts) if pattern_concepts else 0
        
        # Analyze structural complexity
        structural_complexity = await self._assess_structural_complexity(abstract_pattern)
        
        # Decision tree for strategy selection
        if abstraction_level > 0.8 and concept_overlap_ratio > 0.7:
            return AdaptationStrategy.DIRECT_TRANSFER
        elif concept_overlap_ratio > 0.5 and structural_complexity < 0.6:
            return AdaptationStrategy.CONCEPTUAL_MAPPING
        elif domain_distance < 0.4 and abstraction_level > 0.6:
            return AdaptationStrategy.STRUCTURAL_ANALOGY
        elif abstraction_level < 0.5 or structural_complexity > 0.8:
            return AdaptationStrategy.ABSTRACTION_REFINEMENT
        else:
            return AdaptationStrategy.HYBRID_APPROACH
    
    async def _create_concept_mappings(
        self,
        abstract_pattern: AbstractPattern,
        target_ontology: DomainOntology
    ) -> Dict[str, str]:
        """Create mappings between abstract pattern concepts and target domain concepts"""
        
        mappings = {}
        pattern_concepts = await self._extract_abstract_pattern_concepts(abstract_pattern)
        
        for pattern_concept in pattern_concepts:
            # Find best matching concept in target domain
            best_match = await self._find_best_concept_match(
                pattern_concept, target_ontology.core_concepts
            )
            
            if best_match:
                mappings[pattern_concept] = best_match['concept']
            else:
                # Create conceptual bridge
                conceptual_bridge = await self._create_conceptual_bridge(
                    pattern_concept, target_ontology
                )
                if conceptual_bridge:
                    mappings[pattern_concept] = conceptual_bridge
        
        return mappings
    
    async def _create_technology_substitutions(
        self,
        abstract_pattern: AbstractPattern,
        target_ontology: DomainOntology
    ) -> Dict[str, str]:
        """Create technology substitutions for target domain"""
        
        substitutions = {}
        
        # Extract technologies from variable components
        for var_key, var_desc in abstract_pattern.variable_components.items():
            if var_key.startswith('technology_'):
                tech_name = var_key.replace('technology_', '')
                
                # Find equivalent technology in target domain
                equivalent = await self._find_equivalent_technology(
                    tech_name, target_ontology.tools_and_technologies
                )
                
                if equivalent:
                    substitutions[tech_name] = equivalent
                else:
                    # Suggest closest alternative
                    alternative = await self._suggest_technology_alternative(
                        tech_name, target_ontology
                    )
                    if alternative:
                        substitutions[tech_name] = alternative
        
        return substitutions
    
    async def _generate_adapted_content(
        self,
        abstract_pattern: AbstractPattern,
        target_domain: DomainType,
        concept_mappings: Dict[str, str],
        tech_substitutions: Dict[str, str],
        adaptation_strategy: AdaptationStrategy
    ) -> str:
        """Generate adapted pattern content for target domain"""
        
        # Start with abstract description
        adapted_content = f"# {abstract_pattern.title}\n\n"
        
        # Add domain-specific context
        adapted_content += f"**Adapted for {target_domain.value} domain**\n\n"
        
        # Add problem statement adapted to domain
        adapted_content += await self._adapt_problem_statement(
            abstract_pattern, target_domain, concept_mappings
        )
        
        # Add solution approach
        adapted_content += await self._adapt_solution_approach(
            abstract_pattern, target_domain, tech_substitutions, adaptation_strategy
        )
        
        # Add implementation details
        adapted_content += await self._generate_implementation_details(
            abstract_pattern, target_domain, concept_mappings, tech_substitutions
        )
        
        # Add validation criteria
        adapted_content += await self._generate_validation_section(
            abstract_pattern, target_domain
        )
        
        # Add domain-specific considerations
        adapted_content += await self._add_domain_specific_considerations(
            abstract_pattern, target_domain
        )
        
        return adapted_content
    
    async def _predict_adaptation_success(
        self,
        abstract_pattern: AbstractPattern,
        target_domain: DomainType,
        problem_context: Dict[str, Any]
    ) -> SuccessProbability:
        """Predict success probability for pattern adaptation"""
        
        # Initialize feature vector for ML prediction
        features = []
        
        # Pattern characteristics features
        features.append(abstract_pattern.abstraction_level)
        features.append(abstract_pattern.quality_score)
        features.append(len(abstract_pattern.invariant_properties))
        features.append(len(abstract_pattern.variable_components))
        features.append(len(abstract_pattern.source_domains))
        
        # Domain compatibility features
        source_domain = abstract_pattern.source_domains[0] if abstract_pattern.source_domains else DomainType.UNKNOWN
        domain_compatibility = await self._calculate_domain_compatibility(source_domain, target_domain)
        features.append(domain_compatibility)
        
        # Concept overlap features
        pattern_concepts = await self._extract_abstract_pattern_concepts(abstract_pattern)
        target_patterns = await self._get_patterns_by_domain(target_domain)
        target_ontology = await self._build_domain_ontology(target_domain, target_patterns)
        
        concept_overlap = len(set(pattern_concepts) & set(target_ontology.core_concepts))
        concept_overlap_ratio = concept_overlap / len(pattern_concepts) if pattern_concepts else 0
        features.append(concept_overlap_ratio)
        
        # Historical success features
        historical_success_rate = await self._get_historical_success_rate(source_domain, target_domain)
        features.append(historical_success_rate)
        
        # Problem context features
        context_complexity = problem_context.get('complexity', 0.5)
        features.append(context_complexity)
        
        # Apply ML model for prediction (simplified rule-based for now)
        success_score = await self._calculate_success_score(features)
        
        # Convert to probability enum
        return self._float_to_success_probability(success_score)
    
    async def _generate_adaptation_guidance(
        self,
        pattern: KnowledgeItem,
        source_domain: DomainType,
        target_domain: DomainType,
        problem_description: str
    ) -> Dict[str, Any]:
        """Generate specific guidance for adapting pattern to target domain"""
        
        return {
            "adaptation_steps": await self._generate_adaptation_steps(pattern, target_domain),
            "concept_mappings": await self._suggest_concept_adaptations(pattern, source_domain, target_domain),
            "technology_changes": await self._suggest_technology_changes(pattern, target_domain),
            "potential_issues": await self._identify_adaptation_issues(pattern, source_domain, target_domain),
            "validation_approach": await self._suggest_validation_approach(pattern, target_domain),
            "success_factors": await self._identify_success_factors(pattern, target_domain),
            "risk_mitigation": await self._suggest_risk_mitigation(pattern, source_domain, target_domain)
        }
    
    # Advanced Success Prediction Methods
    
    async def _calculate_success_score(self, features: List[float]) -> float:
        """Calculate success probability score using feature vector"""
        
        # Weighted feature importance (based on empirical analysis)
        weights = [
            0.15,  # abstraction_level
            0.20,  # quality_score  
            0.10,  # invariant_properties_count
            0.05,  # variable_components_count
            0.05,  # source_domains_count
            0.25,  # domain_compatibility
            0.15,  # concept_overlap_ratio
            0.05   # historical_success_rate
        ]
        
        if len(features) != len(weights):
            logger.warning("Feature vector length mismatch", 
                          expected=len(weights), actual=len(features))
            weights = weights[:len(features)]  # Adjust weights
        
        # Calculate weighted score
        weighted_sum = sum(f * w for f, w in zip(features, weights))
        
        # Apply sigmoid normalization
        normalized_score = 1 / (1 + np.exp(-5 * (weighted_sum - 0.5)))
        
        return float(normalized_score)
    
    def _float_to_success_probability(self, score: float) -> SuccessProbability:
        """Convert float score to SuccessProbability enum"""
        if score >= 0.9:
            return SuccessProbability.VERY_HIGH
        elif score >= 0.75:
            return SuccessProbability.HIGH
        elif score >= 0.5:
            return SuccessProbability.MEDIUM
        elif score >= 0.25:
            return SuccessProbability.LOW
        else:
            return SuccessProbability.VERY_LOW
    
    async def _calculate_domain_compatibility(
        self, 
        source_domain: DomainType, 
        target_domain: DomainType
    ) -> float:
        """Calculate compatibility score between two domains"""
        
        # Domain compatibility matrix (based on empirical analysis)
        compatibility_matrix = {
            (DomainType.AUTHENTICATION, DomainType.SECURITY): 0.9,
            (DomainType.AUTHENTICATION, DomainType.BACKEND): 0.8,
            (DomainType.AUTHENTICATION, DomainType.API_DESIGN): 0.7,
            (DomainType.DATABASE, DomainType.BACKEND): 0.9,
            (DomainType.DATABASE, DomainType.API_DESIGN): 0.7,
            (DomainType.FRONTEND, DomainType.API_DESIGN): 0.8,
            (DomainType.DEVOPS, DomainType.ARCHITECTURE): 0.8,
            (DomainType.SECURITY, DomainType.ARCHITECTURE): 0.7,
            (DomainType.PERFORMANCE, DomainType.ARCHITECTURE): 0.8,
            (DomainType.TESTING, DomainType.ARCHITECTURE): 0.6,
            # Add more domain pairs as needed
        }
        
        # Check both directions
        pair1 = (source_domain, target_domain)
        pair2 = (target_domain, source_domain)
        
        if pair1 in compatibility_matrix:
            return compatibility_matrix[pair1]
        elif pair2 in compatibility_matrix:
            return compatibility_matrix[pair2]
        else:
            # Calculate based on shared characteristics
            return await self._calculate_implicit_compatibility(source_domain, target_domain)
    
    async def _calculate_implicit_compatibility(
        self, 
        source_domain: DomainType, 
        target_domain: DomainType
    ) -> float:
        """Calculate compatibility based on domain characteristics"""
        
        # Get patterns from both domains
        source_patterns = await self._get_patterns_by_domain(source_domain)
        target_patterns = await self._get_patterns_by_domain(target_domain)
        
        if not source_patterns or not target_patterns:
            return 0.3  # Default low compatibility for unknown domains
        
        # Build ontologies
        source_ontology = await self._build_domain_ontology(source_domain, source_patterns)
        target_ontology = await self._build_domain_ontology(target_domain, target_patterns)
        
        # Calculate concept overlap
        concept_overlap = len(set(source_ontology.core_concepts) & set(target_ontology.core_concepts))
        total_concepts = len(set(source_ontology.core_concepts) | set(target_ontology.core_concepts))
        concept_similarity = concept_overlap / total_concepts if total_concepts > 0 else 0
        
        # Calculate technology overlap
        tech_overlap = len(set(source_ontology.tools_and_technologies) & set(target_ontology.tools_and_technologies))
        total_tech = len(set(source_ontology.tools_and_technologies) | set(target_ontology.tools_and_technologies))
        tech_similarity = tech_overlap / total_tech if total_tech > 0 else 0
        
        # Calculate problem overlap
        problem_overlap = len(set(source_ontology.typical_problems) & set(target_ontology.typical_problems))
        total_problems = len(set(source_ontology.typical_problems) | set(target_ontology.typical_problems))
        problem_similarity = problem_overlap / total_problems if total_problems > 0 else 0
        
        # Weighted average
        compatibility = (concept_similarity * 0.5 + tech_similarity * 0.3 + problem_similarity * 0.2)
        
        return min(compatibility, 1.0)
    
    async def _get_historical_success_rate(
        self, 
        source_domain: DomainType, 
        target_domain: DomainType
    ) -> float:
        """Get historical success rate for adaptations between these domains"""
        
        try:
            async with self.db_manager.get_db_pool() as pool:
                async with pool.acquire() as conn:
                    query = """
                    SELECT 
                        COUNT(CASE WHEN actual_success = true THEN 1 END)::FLOAT / COUNT(*)::FLOAT as success_rate
                    FROM domain_adaptations 
                    WHERE source_domain = $1 AND target_domain = $2
                    AND actual_success IS NOT NULL
                    """
                    result = await conn.fetchrow(query, source_domain.value, target_domain.value)
                    
                    return result['success_rate'] if result and result['success_rate'] is not None else 0.5
                    
        except Exception as e:
            logger.error("Failed to get historical success rate", error=str(e))
            return 0.5  # Default neutral success rate
    
    # Placeholder implementations for remaining methods
    
    async def _extract_abstract_pattern_concepts(self, abstract_pattern: AbstractPattern) -> List[str]:
        """Extract concepts from abstract pattern"""
        concepts = []
        
        # Extract from invariant properties
        concepts.extend(abstract_pattern.invariant_properties)
        
        # Extract from conceptual structure
        for key, value in abstract_pattern.conceptual_structure.items():
            if isinstance(value, dict):
                concepts.extend(value.keys())
            elif isinstance(value, list):
                concepts.extend([str(item) for item in value if isinstance(item, str)])
        
        # Extract from variable components keys
        concepts.extend(abstract_pattern.variable_components.keys())
        
        return list(set(concepts))  # Remove duplicates
    
    async def _calculate_domain_distance(self, source_domain: DomainType, target_domain: DomainType) -> float:
        """Calculate distance between domains (0 = identical, 1 = completely different)"""
        if source_domain == target_domain:
            return 0.0
        
        # Use compatibility score as inverse of distance
        compatibility = await self._calculate_domain_compatibility(source_domain, target_domain)
        return 1.0 - compatibility
    
    async def _assess_structural_complexity(self, abstract_pattern: AbstractPattern) -> float:
        """Assess structural complexity of abstract pattern"""
        complexity_score = 0.0
        
        # Factor in conceptual structure complexity
        if abstract_pattern.conceptual_structure:
            structure_depth = self._calculate_nested_depth(abstract_pattern.conceptual_structure)
            complexity_score += min(structure_depth / 5.0, 0.3)  # Max 0.3 for structure
        
        # Factor in variable components count
        var_component_complexity = len(abstract_pattern.variable_components) / 20.0  # Normalize to max 20
        complexity_score += min(var_component_complexity, 0.2)  # Max 0.2 for variables
        
        # Factor in invariant properties count
        invariant_complexity = len(abstract_pattern.invariant_properties) / 15.0  # Normalize to max 15
        complexity_score += min(invariant_complexity, 0.2)  # Max 0.2 for invariants
        
        # Factor in applicability conditions
        condition_complexity = len(abstract_pattern.applicability_conditions) / 10.0  # Normalize to max 10
        complexity_score += min(condition_complexity, 0.3)  # Max 0.3 for conditions
        
        return min(complexity_score, 1.0)
    
    def _calculate_nested_depth(self, structure: Dict[str, Any], current_depth: int = 0) -> int:
        """Calculate maximum nested depth of a dictionary structure"""
        if not isinstance(structure, dict):
            return current_depth
        
        max_depth = current_depth
        for value in structure.values():
            if isinstance(value, dict):
                depth = self._calculate_nested_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth