// BETTY Memory System - Neo4j Constraints and Indexes (Community Edition)
// Database: Neo4j Graph Database for Graphiti Temporal Memory
// Purpose: Temporal knowledge graphs with entity relationships and evolution tracking
//
// NOTE: This version is adapted for Neo4j Community Edition
// Property existence constraints are not available in Community Edition

// =============================================================================
// GRAPHITI CORE NODE CONSTRAINTS
// =============================================================================

// Project Nodes - Top-level project organization
CREATE CONSTRAINT project_uuid_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.uuid IS UNIQUE;

CREATE CONSTRAINT project_name_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.name IS UNIQUE;

// Entity Nodes - Knowledge entities extracted by Graphiti
CREATE CONSTRAINT entity_uuid_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.uuid IS UNIQUE;

// Knowledge Nodes - Specific knowledge items and patterns
CREATE CONSTRAINT knowledge_uuid_unique IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.uuid IS UNIQUE;

// Session Nodes - Claude interaction sessions
CREATE CONSTRAINT session_uuid_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.uuid IS UNIQUE;

// User Nodes - Users interacting with the system
CREATE CONSTRAINT user_uuid_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.uuid IS UNIQUE;

CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE;

// Technology Nodes - Technologies, frameworks, patterns
CREATE CONSTRAINT technology_name_unique IF NOT EXISTS
FOR (t:Technology) REQUIRE t.name IS UNIQUE;

// Domain Nodes - Problem domains and business areas
CREATE CONSTRAINT domain_name_unique IF NOT EXISTS
FOR (d:Domain) REQUIRE d.name IS UNIQUE;

// Pattern Nodes - Code patterns and architectural solutions
CREATE CONSTRAINT pattern_name_unique IF NOT EXISTS
FOR (p:Pattern) REQUIRE p.name IS UNIQUE;

// Problem Nodes - Problems solved and challenges encountered
CREATE CONSTRAINT problem_uuid_unique IF NOT EXISTS
FOR (p:Problem) REQUIRE p.uuid IS UNIQUE;

// Solution Nodes - Solutions and approaches taken
CREATE CONSTRAINT solution_uuid_unique IF NOT EXISTS
FOR (s:Solution) REQUIRE s.uuid IS UNIQUE;

// =============================================================================
// PERFORMANCE INDEXES FOR COMMON QUERIES
// =============================================================================

// Project Indexes
CREATE INDEX project_name_idx IF NOT EXISTS FOR (p:Project) ON (p.name);
CREATE INDEX project_domain_idx IF NOT EXISTS FOR (p:Project) ON (p.domain);
CREATE INDEX project_created_at_idx IF NOT EXISTS FOR (p:Project) ON (p.created_at);

// Entity Indexes - Critical for Graphiti entity operations
CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type);
CREATE INDEX entity_project_idx IF NOT EXISTS FOR (e:Entity) ON (e.project_uuid);
CREATE INDEX entity_created_at_idx IF NOT EXISTS FOR (e:Entity) ON (e.created_at);
CREATE INDEX entity_confidence_idx IF NOT EXISTS FOR (e:Entity) ON (e.confidence_score);

// Knowledge Indexes - Core knowledge retrieval
CREATE INDEX knowledge_title_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.title);
CREATE INDEX knowledge_type_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.knowledge_type);
CREATE INDEX knowledge_domain_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.domain);
CREATE INDEX knowledge_project_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.project_uuid);
CREATE INDEX knowledge_quality_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.quality_score);
CREATE INDEX knowledge_usage_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.usage_count);
CREATE INDEX knowledge_created_at_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.created_at);

// Temporal Indexes - Critical for bi-temporal queries
CREATE INDEX knowledge_valid_from_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.valid_from);
CREATE INDEX knowledge_valid_until_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.valid_until);
CREATE INDEX knowledge_system_time_from_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.system_time_from);
CREATE INDEX knowledge_system_time_until_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.system_time_until);

// Session Indexes
CREATE INDEX session_project_idx IF NOT EXISTS FOR (s:Session) ON (s.project_uuid);
CREATE INDEX session_user_idx IF NOT EXISTS FOR (s:Session) ON (s.user_uuid);
CREATE INDEX session_started_at_idx IF NOT EXISTS FOR (s:Session) ON (s.started_at);
CREATE INDEX session_outcome_idx IF NOT EXISTS FOR (s:Session) ON (s.outcome);

// Technology and Pattern Indexes
CREATE INDEX technology_name_idx IF NOT EXISTS FOR (t:Technology) ON (t.name);
CREATE INDEX technology_category_idx IF NOT EXISTS FOR (t:Technology) ON (t.category);
CREATE INDEX pattern_name_idx IF NOT EXISTS FOR (p:Pattern) ON (p.name);
CREATE INDEX pattern_complexity_idx IF NOT EXISTS FOR (p:Pattern) ON (p.complexity_level);

// Domain Indexes
CREATE INDEX domain_type_idx IF NOT EXISTS FOR (d:Domain) ON (d.domain_type);
CREATE INDEX domain_business_area_idx IF NOT EXISTS FOR (d:Domain) ON (d.business_area);

// Problem and Solution Indexes
CREATE INDEX problem_domain_idx IF NOT EXISTS FOR (p:Problem) ON (p.domain);
CREATE INDEX problem_complexity_idx IF NOT EXISTS FOR (p:Problem) ON (p.complexity_level);
CREATE INDEX solution_success_rate_idx IF NOT EXISTS FOR (s:Solution) ON (s.success_rate);
CREATE INDEX solution_reuse_count_idx IF NOT EXISTS FOR (s:Solution) ON (s.reuse_count);

// =============================================================================
// FULL-TEXT SEARCH INDEXES FOR CONTENT DISCOVERY
// =============================================================================

// Full-text search on knowledge content
CREATE FULLTEXT INDEX knowledge_content_search IF NOT EXISTS
FOR (k:Knowledge) ON EACH [k.title, k.content, k.problem_description, k.solution_description];

// Full-text search on entity names and descriptions
CREATE FULLTEXT INDEX entity_content_search IF NOT EXISTS
FOR (e:Entity) ON EACH [e.name, e.description, e.aliases];

// Full-text search on problems and solutions
CREATE FULLTEXT INDEX problem_solution_search IF NOT EXISTS
FOR (p:Problem|Solution) ON EACH [p.title, p.description, p.context];

// =============================================================================
// RELATIONSHIP INDEXES FOR GRAPH TRAVERSAL PERFORMANCE
// =============================================================================

// Note: Relationship property indexes require specific relationship type in Community Edition
// These will be created as needed when specific relationship types are defined

// =============================================================================
// GRAPHITI INITIALIZATION DATA
// =============================================================================

// Create BETTY system project node
MERGE (betty:Project {
    uuid: "betty-system-project",
    name: "BETTY",
    description: "Cross-project memory system providing unlimited context awareness for Claude",
    domain: "localhost",
    project_type: "memory_system",
    business_domain: "ai_systems",
    technology_stack: ["Python", "FastAPI", "PostgreSQL", "Neo4j", "Qdrant", "Redis", "Graphiti"],
    privacy_level: "private",
    created_at: datetime(),
    version: "1.0.0",
    graphiti_enabled: true,
    temporal_tracking: true
});

// Create default user node
MERGE (andre:User {
    uuid: "andre-user",
    username: "andre",
    display_name: "Andre",
    created_at: datetime(),
    context_loading_depth: 15,
    cross_project_suggestions: true,
    memory_retention_days: -1,
    privacy_level: "private",
    intelligent_suggestions: true,
    background_processing: true
});

// Create core domain nodes for knowledge organization
MERGE (auth:Domain {
    uuid: "authentication-domain",
    name: "Authentication",
    domain_type: "technical",
    business_area: "security",
    description: "User authentication, authorization, and security patterns"
});

MERGE (db:Domain {
    uuid: "database-domain", 
    name: "Database",
    domain_type: "technical",
    business_area: "data_management",
    description: "Database design, optimization, and management patterns"
});

MERGE (api:Domain {
    uuid: "api-domain",
    name: "API Design",
    domain_type: "technical", 
    business_area: "software_architecture",
    description: "REST API design, GraphQL, and service architecture patterns"
});

MERGE (frontend:Domain {
    uuid: "frontend-domain",
    name: "Frontend",
    domain_type: "technical",
    business_area: "user_interface",
    description: "Frontend frameworks, UI/UX patterns, and client-side architecture"
});

MERGE (deployment:Domain {
    uuid: "deployment-domain",
    name: "Deployment", 
    domain_type: "technical",
    business_area: "infrastructure",
    description: "Deployment strategies, containerization, and infrastructure management"
});

MERGE (memory:Domain {
    uuid: "memory-systems-domain",
    name: "Memory Systems",
    domain_type: "technical",
    business_area: "ai_systems", 
    description: "AI memory, knowledge graphs, and intelligent systems"
});

// Create core technology nodes
MERGE (python:Technology {
    name: "Python",
    category: "programming_language",
    description: "High-level programming language for backend development",
    ecosystem: ["FastAPI", "Django", "Flask", "SQLAlchemy", "Pydantic"]
});

MERGE (fastapi:Technology {
    name: "FastAPI", 
    category: "web_framework",
    description: "Modern, fast web framework for building APIs with Python",
    parent_technology: "Python"
});

MERGE (postgresql:Technology {
    name: "PostgreSQL",
    category: "database",
    description: "Advanced open-source relational database system",
    features: ["ACID", "JSON", "Full-text search", "Extensions"]
});

MERGE (neo4j:Technology {
    name: "Neo4j",
    category: "graph_database", 
    description: "Leading graph database for connected data",
    features: ["Cypher", "APOC", "Graph algorithms", "Temporal queries"]
});

MERGE (qdrant:Technology {
    name: "Qdrant",
    category: "vector_database",
    description: "Vector similarity search engine for machine learning applications",
    features: ["Embeddings", "Similarity search", "Filtering", "Collections"]
});

MERGE (redis:Technology {
    name: "Redis",
    category: "cache_database",
    description: "In-memory data structure store for caching and messaging", 
    features: ["Key-value", "Pub/Sub", "Streams", "Modules"]
});

MERGE (graphiti:Technology {
    name: "Graphiti",
    category: "ai_framework",
    description: "Temporal knowledge graph framework for AI memory systems",
    features: ["Bi-temporal", "Entity extraction", "Relationship detection"]
});

// Create relationships between technologies
MERGE (fastapi)-[:BUILT_WITH]->(python);
MERGE (graphiti)-[:INTEGRATES_WITH]->(neo4j);
MERGE (betty)-[:USES_TECHNOLOGY]->(python);
MERGE (betty)-[:USES_TECHNOLOGY]->(fastapi);
MERGE (betty)-[:USES_TECHNOLOGY]->(postgresql);
MERGE (betty)-[:USES_TECHNOLOGY]->(neo4j);
MERGE (betty)-[:USES_TECHNOLOGY]->(qdrant);
MERGE (betty)-[:USES_TECHNOLOGY]->(redis);
MERGE (betty)-[:USES_TECHNOLOGY]->(graphiti);

// Create relationships between domains and technologies
MERGE (auth)-[:COMMONLY_USES]->(python);
MERGE (auth)-[:COMMONLY_USES]->(fastapi);
MERGE (db)-[:COMMONLY_USES]->(postgresql);
MERGE (api)-[:COMMONLY_USES]->(fastapi);
MERGE (memory)-[:COMMONLY_USES]->(neo4j);
MERGE (memory)-[:COMMONLY_USES]->(qdrant);
MERGE (memory)-[:COMMONLY_USES]->(graphiti);

// =============================================================================
// COMPLETION AND VERSION TRACKING
// =============================================================================

// Create system metadata node
MERGE (system:SystemMetadata {
    uuid: "betty-neo4j-system",
    schema_version: "1.0.0",
    initialized_at: datetime(),
    graphiti_version: "latest",
    edition: "community",
    features: [
        "temporal_knowledge_graphs",
        "cross_project_intelligence",
        "entity_extraction",
        "relationship_detection",
        "pattern_recognition"
    ]
});

// Create initialization completion marker
MERGE (init:InitializationMarker {
    uuid: "betty-neo4j-init-complete",
    completed_at: datetime(),
    schema_version: "1.0.0",
    constraints_created: 13,
    indexes_created: 30,
    initial_data_loaded: true
});

// Connect initialization to system
MERGE (init)-[:INITIALIZES]->(system);

// Return confirmation
RETURN "BETTY Memory System Neo4j Community Edition initialized successfully" AS status;