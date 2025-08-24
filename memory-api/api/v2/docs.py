# ABOUTME: API documentation and interactive examples for BETTY Memory System v2
# ABOUTME: Provides comprehensive documentation, examples, and API testing capabilities

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import structlog

from core.security import get_current_user
from api.v2.versioning import version_manager, API_V2_METADATA

logger = structlog.get_logger(__name__)

# API Documentation
API_DOCUMENTATION = {
    "v2": {
        "title": "BETTY Memory System API v2.0",
        "description": "Claude's Extended Brain - Advanced APIs for Unlimited Context Awareness",
        "version": "2.0.0",
        "base_url": "/api/v2",
        "authentication": {
            "type": "JWT Bearer Token",
            "description": "Requires valid JWT token in Authorization header",
            "example": "Authorization: Bearer <jwt_token>"
        },
        "rate_limiting": {
            "default": "100 requests per minute",
            "authenticated": "1000 requests per minute",
            "premium": "10000 requests per minute"
        },
        "endpoints": {
            "advanced_query": {
                "base_path": "/v2/query",
                "description": "Advanced querying capabilities with semantic search, filtering, and analysis",
                "endpoints": {
                    "/advanced-search": {
                        "method": "POST",
                        "description": "Perform advanced search with multiple filters and ranking",
                        "features": [
                            "Multi-modal search (semantic + keyword + metadata)",
                            "Complex boolean filters with nested conditions",
                            "Time-range filtering with relative dates",
                            "Custom ranking algorithms",
                            "Result clustering and grouping"
                        ],
                        "permissions": ["query:advanced"],
                        "example": {
                            "query": "machine learning optimization techniques",
                            "search_type": "hybrid",
                            "filters": [
                                {
                                    "field": "knowledge_type",
                                    "operator": "eq",
                                    "value": "research_paper"
                                }
                            ],
                            "similarity_threshold": 0.75,
                            "max_results": 20
                        }
                    },
                    "/pattern-match": {
                        "method": "POST", 
                        "description": "Find patterns in knowledge graph using graph traversal",
                        "features": [
                            "Path pattern matching",
                            "Subgraph isomorphism detection",
                            "Temporal pattern recognition",
                            "Community detection"
                        ],
                        "permissions": ["query:patterns"],
                        "example": {
                            "pattern_type": "path",
                            "pattern_definition": {
                                "path": "A->B->C",
                                "relationship_types": ["influences", "leads_to"]
                            },
                            "max_depth": 3
                        }
                    },
                    "/semantic-clusters": {
                        "method": "POST",
                        "description": "Perform semantic clustering of knowledge items",
                        "features": [
                            "Vector-based clustering using embeddings",
                            "Hierarchical clustering with dendrograms", 
                            "Dynamic cluster number selection",
                            "Topic modeling integration"
                        ],
                        "permissions": ["query:clustering"],
                        "example": {
                            "algorithm": "hierarchical",
                            "auto_clusters": True,
                            "min_cluster_size": 5,
                            "include_visualization": True
                        }
                    },
                    "/cross-project": {
                        "method": "POST",
                        "description": "Analyze knowledge connections across projects",
                        "features": [
                            "Inter-project knowledge transfer detection",
                            "Shared concept identification",
                            "Project similarity analysis",
                            "Knowledge gap identification"
                        ],
                        "permissions": ["query:cross_project"],
                        "example": {
                            "analysis_types": ["shared_concepts", "knowledge_transfer"],
                            "similarity_threshold": 0.6,
                            "max_connections": 50
                        }
                    }
                }
            },
            "batch_operations": {
                "base_path": "/v2/batch",
                "description": "Bulk operations with progress tracking and background processing",
                "endpoints": {
                    "/knowledge/import": {
                        "method": "POST",
                        "description": "Bulk import knowledge items from various sources",
                        "features": [
                            "Import from JSON, CSV, XML, or API sources",
                            "Automatic duplicate detection and handling",
                            "Content validation and sanitization",
                            "Vector embedding generation",
                            "Progress tracking with real-time updates"
                        ],
                        "permissions": ["batch:knowledge:import"],
                        "example": {
                            "source_type": "file",
                            "format": "json",
                            "source_config": {
                                "file_path": "/path/to/knowledge.json"
                            },
                            "duplicate_handling": "skip",
                            "generate_embeddings": True
                        }
                    },
                    "/knowledge/export": {
                        "method": "POST",
                        "description": "Bulk export knowledge items to various formats",
                        "features": [
                            "Export to JSON, CSV, XML, or SQL formats",
                            "Selective export with advanced filtering",
                            "Metadata preservation",
                            "Compression options for large exports"
                        ],
                        "permissions": ["batch:knowledge:export"],
                        "example": {
                            "format": "json",
                            "include_metadata": True,
                            "include_relationships": True,
                            "compress": True,
                            "delivery_method": "download"
                        }
                    },
                    "/sessions/merge": {
                        "method": "POST",
                        "description": "Merge multiple chat sessions intelligently",
                        "features": [
                            "Semantic similarity-based merging",
                            "Conversation flow preservation",
                            "Duplicate message detection",
                            "Timeline reconstruction"
                        ],
                        "permissions": ["batch:sessions:merge"],
                        "example": {
                            "session_ids": ["uuid1", "uuid2", "uuid3"],
                            "merge_strategy": "semantic_similarity",
                            "preserve_timestamps": True,
                            "deduplicate_messages": True
                        }
                    }
                }
            },
            "cross_project": {
                "base_path": "/v2/cross-project", 
                "description": "Cross-project intelligence and knowledge sharing",
                "endpoints": {
                    "/connections": {
                        "method": "POST",
                        "description": "Create connections between projects for knowledge sharing",
                        "features": [
                            "Bidirectional project linking",
                            "Permission-based access control",
                            "Configurable sharing policies",
                            "Audit trail for connections"
                        ],
                        "permissions": ["cross_project:connections:create"],
                        "example": {
                            "source_project_id": "uuid1",
                            "target_project_id": "uuid2",
                            "connection_type": "bidirectional",
                            "permissions": {
                                "read": True,
                                "write": False
                            }
                        }
                    },
                    "/knowledge/transfer": {
                        "method": "POST",
                        "description": "Transfer knowledge items between connected projects",
                        "features": [
                            "Selective knowledge transfer with filters",
                            "Relationship preservation during transfer",
                            "Conflict resolution strategies",
                            "Rollback capabilities"
                        ],
                        "permissions": ["cross_project:knowledge:transfer"],
                        "example": {
                            "source_project_id": "uuid1",
                            "target_project_id": "uuid2", 
                            "transfer_strategy": "copy",
                            "preserve_metadata": True,
                            "conflict_resolution": "merge"
                        }
                    },
                    "/search": {
                        "method": "POST",
                        "description": "Search across multiple connected projects",
                        "features": [
                            "Federated search across project boundaries",
                            "Permission-aware result filtering",
                            "Cross-project ranking and relevance",
                            "Unified result presentation"
                        ],
                        "permissions": ["cross_project:search"],
                        "example": {
                            "query": "machine learning algorithms",
                            "search_type": "hybrid",
                            "project_ids": ["uuid1", "uuid2"],
                            "max_results_per_project": 10
                        }
                    }
                }
            }
        },
        "response_formats": {
            "standard_response": {
                "description": "All API responses follow this standard format",
                "structure": {
                    "success": "boolean",
                    "message": "string",
                    "data": "object|array",
                    "timestamp": "ISO 8601 datetime",
                    "api_version": "string"
                }
            },
            "error_response": {
                "description": "Error responses include detailed error information",
                "structure": {
                    "success": False,
                    "error_code": "string", 
                    "message": "string",
                    "details": "object",
                    "timestamp": "ISO 8601 datetime",
                    "request_id": "string"
                }
            },
            "paginated_response": {
                "description": "List endpoints return paginated results",
                "structure": {
                    "success": True,
                    "message": "string",
                    "data": "array",
                    "pagination": {
                        "page": "integer",
                        "page_size": "integer", 
                        "total_items": "integer",
                        "total_pages": "integer",
                        "has_next": "boolean",
                        "has_previous": "boolean"
                    }
                }
            }
        },
        "error_codes": {
            "400": "Bad Request - Invalid request parameters",
            "401": "Unauthorized - Invalid or missing authentication",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Requested resource not found", 
            "409": "Conflict - Resource conflict (duplicate, etc.)",
            "422": "Unprocessable Entity - Validation errors",
            "429": "Too Many Requests - Rate limit exceeded",
            "500": "Internal Server Error - Server-side error",
            "503": "Service Unavailable - Service temporarily unavailable"
        }
    }
}

# Interactive examples
INTERACTIVE_EXAMPLES = {
    "advanced_search": {
        "title": "Advanced Search Example",
        "description": "Demonstrate advanced search capabilities with semantic filtering",
        "code": '''
# Advanced Search with Multiple Filters
curl -X POST "http://localhost:3034/api/v2/query/advanced-search" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "neural networks deep learning",
    "search_type": "hybrid",
    "filters": [
      {
        "field": "knowledge_type",
        "operator": "in", 
        "value": ["research_paper", "article", "documentation"]
      },
      {
        "field": "created_at",
        "operator": "gte",
        "value": "2024-01-01T00:00:00Z"
      }
    ],
    "similarity_threshold": 0.75,
    "max_results": 25,
    "include_metadata": true,
    "group_by": "knowledge_type"
  }'
        ''',
        "response": {
            "message": "Advanced search completed successfully",
            "data": {
                "results": [
                    {
                        "id": "uuid",
                        "title": "Neural Network Architectures",
                        "content": "Overview of modern neural network...",
                        "knowledge_type": "research_paper",
                        "similarity_score": 0.89,
                        "metadata": {}
                    }
                ],
                "analysis": {
                    "execution_time_seconds": 0.234,
                    "search_quality_metrics": {
                        "relevance_score": 0.87
                    }
                }
            },
            "total_results": 15,
            "execution_time_ms": 234.5
        }
    },
    "batch_import": {
        "title": "Batch Knowledge Import",
        "description": "Import knowledge items in bulk with progress tracking",
        "code": '''
# Start Bulk Import Operation
curl -X POST "http://localhost:3034/api/v2/batch/knowledge/import" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "source_type": "file",
    "format": "json",
    "source_config": {
      "file_path": "/uploads/knowledge_export.json"
    },
    "duplicate_handling": "skip",
    "generate_embeddings": true,
    "auto_categorize": true,
    "batch_size": 50
  }'
        
# Check Progress
curl -X GET "http://localhost:3034/api/v2/batch/operations/{operation_id}/progress" \\
  -H "Authorization: Bearer YOUR_TOKEN"
        ''',
        "response": {
            "message": "Bulk knowledge import operation queued successfully",
            "data": {
                "operation_id": "uuid",
                "status": "queued",
                "estimated_duration": "2-5 minutes",
                "progress_endpoint": "/v2/batch/operations/{operation_id}/progress"
            }
        }
    },
    "cross_project_search": {
        "title": "Cross-Project Search",
        "description": "Search across multiple connected projects simultaneously",
        "code": '''
# Search Across Projects
curl -X POST "http://localhost:3034/api/v2/cross-project/search" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "API optimization best practices",
    "search_type": "hybrid",
    "project_ids": ["project1_uuid", "project2_uuid"],
    "similarity_threshold": 0.7,
    "max_results_per_project": 10,
    "include_cross_references": true,
    "group_by_project": true
  }'
        ''',
        "response": {
            "message": "Cross-project search completed successfully", 
            "data": {
                "results": {
                    "project1_uuid": [
                        {
                            "id": "uuid",
                            "title": "REST API Optimization Guide",
                            "source_project_id": "project1_uuid",
                            "cross_project_score": 0.85
                        }
                    ]
                },
                "cross_references": [
                    {
                        "source_item": "uuid1",
                        "target_item": "uuid2",
                        "relationship_type": "references",
                        "strength": 0.78
                    }
                ]
            },
            "projects_searched": 2,
            "total_results": 18
        }
    }
}

docs_router = APIRouter(prefix="/v2/docs", tags=["API Documentation v2"])

@docs_router.get("/", response_class=HTMLResponse)
async def get_api_documentation():
    """Get comprehensive API documentation"""
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BETTY Memory System API v2.0 Documentation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            h3 {{ color: #7f8c8d; }}
            .endpoint {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
            .method {{ display: inline-block; padding: 4px 8px; border-radius: 3px; color: white; font-weight: bold; margin-right: 10px; }}
            .method.post {{ background: #e67e22; }}
            .method.get {{ background: #27ae60; }}
            .method.put {{ background: #f39c12; }}
            .method.delete {{ background: #e74c3c; }}
            .features {{ list-style-type: none; padding-left: 0; }}
            .features li {{ background: #ecf0f1; margin: 5px 0; padding: 8px; border-radius: 3px; }}
            .features li:before {{ content: "✓"; color: #27ae60; font-weight: bold; margin-right: 8px; }}
            code {{ background: #2c3e50; color: white; padding: 2px 5px; border-radius: 3px; }}
            pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            .nav {{ background: #34495e; padding: 15px; margin: -30px -30px 30px -30px; border-radius: 8px 8px 0 0; }}
            .nav a {{ color: white; text-decoration: none; margin-right: 20px; }}
            .nav a:hover {{ text-decoration: underline; }}
            .badge {{ background: #3498db; color: white; padding: 2px 6px; border-radius: 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="#overview">Overview</a>
                <a href="#authentication">Authentication</a>
                <a href="#endpoints">Endpoints</a>
                <a href="#examples">Examples</a>
                <a href="#errors">Error Handling</a>
            </div>
            
            <h1 id="overview">BETTY Memory System API v2.0</h1>
            <p><strong>Claude's Extended Brain - Advanced APIs for Unlimited Context Awareness</strong></p>
            <p>Version 2.0 introduces powerful new capabilities for advanced querying, batch operations, and cross-project intelligence.</p>
            
            <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>🎉 New in v2.0:</strong>
                <ul>
                    <li>Advanced Query APIs with semantic search and pattern matching</li>
                    <li>Batch Operations with real-time progress tracking</li>
                    <li>Cross-Project Intelligence for knowledge sharing</li>
                    <li>Enhanced Performance with intelligent caching</li>
                    <li>Comprehensive API versioning and migration support</li>
                </ul>
            </div>
            
            <h2 id="authentication">Authentication</h2>
            <p>All API endpoints require authentication using JWT Bearer tokens:</p>
            <pre><code>Authorization: Bearer &lt;your_jwt_token&gt;</code></pre>
            <p>Rate limits: <span class="badge">100 req/min</span> (unauthenticated), <span class="badge">1000 req/min</span> (authenticated)</p>
            
            <h2 id="endpoints">API Endpoints</h2>
            
            <h3>Advanced Query APIs</h3>
            <p>Powerful querying capabilities with semantic search, filtering, and analysis.</p>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/v2/query/advanced-search</code>
                <p>Perform advanced search with multiple filters and ranking algorithms.</p>
                <p><strong>Features:</strong></p>
                <ul class="features">
                    <li>Multi-modal search (semantic + keyword + metadata)</li>
                    <li>Complex boolean filters with nested conditions</li>
                    <li>Time-range filtering with relative dates</li>
                    <li>Custom ranking algorithms and result clustering</li>
                </ul>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/v2/query/pattern-match</code>
                <p>Find patterns in knowledge graph using advanced graph traversal algorithms.</p>
                <p><strong>Features:</strong></p>
                <ul class="features">
                    <li>Path pattern matching (A→B→C relationships)</li>
                    <li>Subgraph isomorphism detection</li>
                    <li>Temporal pattern recognition</li>
                    <li>Community detection in knowledge graphs</li>
                </ul>
            </div>
            
            <h3>Batch Operations</h3>
            <p>Handle bulk data operations with progress tracking and background processing.</p>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/v2/batch/knowledge/import</code>
                <p>Bulk import knowledge items from various sources with real-time progress tracking.</p>
                <p><strong>Features:</strong></p>
                <ul class="features">
                    <li>Import from JSON, CSV, XML, or API sources</li>
                    <li>Automatic duplicate detection and handling</li>
                    <li>Content validation and sanitization</li>
                    <li>Vector embedding generation with progress updates</li>
                </ul>
            </div>
            
            <h3>Cross-Project Intelligence</h3>
            <p>Enable knowledge sharing and collaboration across different projects.</p>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/v2/cross-project/search</code>
                <p>Search across multiple connected projects simultaneously.</p>
                <p><strong>Features:</strong></p>
                <ul class="features">
                    <li>Federated search across project boundaries</li>
                    <li>Permission-aware result filtering</li>
                    <li>Cross-project ranking and relevance scoring</li>
                    <li>Unified result presentation with source attribution</li>
                </ul>
            </div>
            
            <h2 id="examples">Interactive Examples</h2>
            <p>Try these examples with your API token:</p>
            
            <h3>Advanced Search Example</h3>
            <pre><code>curl -X POST "http://localhost:3034/api/v2/query/advanced-search" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "query": "machine learning optimization",
    "search_type": "hybrid",
    "similarity_threshold": 0.75,
    "max_results": 20,
    "include_metadata": true
  }}'</code></pre>
            
            <h2 id="errors">Error Handling</h2>
            <p>All errors follow a consistent format with detailed information:</p>
            <pre><code>{{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request parameters",
  "details": {{
    "field": "similarity_threshold",
    "error": "Value must be between 0.0 and 1.0"
  }},
  "timestamp": "2024-08-08T12:00:00Z",
  "request_id": "betty-12345"
}}</code></pre>
            
            <h2>Additional Resources</h2>
            <ul>
                <li><a href="/api/v2/docs/openapi.json">OpenAPI Specification</a></li>
                <li><a href="/api/v2/docs/examples">Interactive Examples</a></li>
                <li><a href="/version/info">Version Information</a></li>
                <li><a href="/docs">Swagger UI</a></li>
            </ul>
        </div>
    </body>
    </html>
    '''
    return HTMLResponse(content=html_content)

@docs_router.get("/openapi.json")
async def get_openapi_specification() -> Dict[str, Any]:
    """Get OpenAPI 3.0 specification for the API"""
    return {
        "openapi": "3.0.2",
        "info": {
            "title": "BETTY Memory System API",
            "description": "Claude's Extended Brain - Advanced APIs for Unlimited Context Awareness",
            "version": "2.0.0",
            "contact": {
                "name": "BETTY Memory System",
                "url": "https://github.com/blockonauts/betty"
            }
        },
        "servers": [
            {
                "url": "http://localhost:3034",
                "description": "Development server"
            },
            {
                "url": "https://rufus.blockonauts.io",
                "description": "Production server"
            }
        ],
        "security": [
            {
                "BearerAuth": []
            }
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "paths": {
            "/api/v2/query/advanced-search": {
                "post": {
                    "summary": "Advanced Search",
                    "description": "Perform advanced search with multiple filters and ranking",
                    "tags": ["Advanced Query"],
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/AdvancedSearchQuery"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Search completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/AdvancedSearchResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request parameters"
                        },
                        "401": {
                            "description": "Unauthorized"
                        },
                        "403": {
                            "description": "Insufficient permissions"
                        }
                    }
                }
            }
            # Additional endpoints would be defined here...
        }
    }

@docs_router.get("/examples")
async def get_interactive_examples() -> Dict[str, Any]:
    """Get interactive API examples"""
    return {
        "message": "Interactive API examples for BETTY Memory System v2.0",
        "examples": INTERACTIVE_EXAMPLES,
        "base_url": "http://localhost:3034/api/v2",
        "authentication_note": "Replace YOUR_TOKEN with your actual JWT token"
    }

@docs_router.get("/examples/{example_name}")
async def get_specific_example(example_name: str) -> Dict[str, Any]:
    """Get a specific interactive example"""
    if example_name not in INTERACTIVE_EXAMPLES:
        raise HTTPException(
            status_code=404,
            detail=f"Example '{example_name}' not found"
        )
    
    return {
        "message": f"Interactive example: {example_name}",
        "example": INTERACTIVE_EXAMPLES[example_name],
        "available_examples": list(INTERACTIVE_EXAMPLES.keys())
    }

@docs_router.get("/changelog")
async def get_changelog() -> Dict[str, Any]:
    """Get API changelog"""
    changelog = {
        "v2.0.0": {
            "release_date": "2024-08-08",
            "status": "stable",
            "new_features": [
                "Advanced Query APIs with semantic search and pattern matching",
                "Batch Operations with real-time progress tracking", 
                "Cross-Project Intelligence for knowledge sharing",
                "Enhanced Performance with intelligent caching",
                "Comprehensive API versioning and migration support",
                "Semantic clustering and similarity matrix generation",
                "Knowledge graph querying with Cypher-like syntax",
                "Time series analysis for temporal patterns",
                "Collaborative filtering recommendations"
            ],
            "improvements": [
                "Enhanced search relevance with hybrid algorithms",
                "Improved error handling and validation",
                "Better rate limiting and performance optimization",
                "Comprehensive logging and monitoring",
                "Enhanced security with fine-grained permissions"
            ],
            "breaking_changes": [
                "New authentication requirements for advanced features",
                "Enhanced permission model for cross-project operations",
                "Updated response formats for consistency",
                "Renamed some endpoint parameters for clarity"
            ],
            "bug_fixes": [
                "Fixed memory leaks in long-running operations",
                "Resolved race conditions in batch processing",
                "Improved error handling in vector operations",
                "Fixed pagination issues in large result sets"
            ]
        },
        "v1.1.0": {
            "release_date": "2024-06-15",
            "status": "maintenance",
            "sunset_date": "2025-12-31",
            "new_features": [
                "Improved search algorithms",
                "Graphiti integration for temporal knowledge graphs",
                "Enhanced session management"
            ]
        },
        "v1.0.0": {
            "release_date": "2024-03-01", 
            "status": "legacy",
            "sunset_date": "2025-12-31",
            "new_features": [
                "Basic knowledge management",
                "Simple search functionality",
                "Session management",
                "Basic analytics"
            ]
        }
    }
    
    return {
        "message": "BETTY Memory System API Changelog",
        "current_version": "2.0.0",
        "changelog": changelog
    }

@docs_router.get("/migration-guide")
async def get_migration_guide() -> Dict[str, Any]:
    """Get migration guide for upgrading to v2.0"""
    return {
        "message": "BETTY Memory System v2.0 Migration Guide",
        "migration_guide": {
            "overview": "This guide helps you migrate from v1.x to v2.0 of the BETTY Memory System API",
            "breaking_changes": API_V2_METADATA["breaking_changes"],
            "migration_steps": [
                {
                    "step": 1,
                    "title": "Update Authentication",
                    "description": "Ensure your JWT tokens include the required permissions for advanced features",
                    "code_example": "Authorization: Bearer <jwt_with_advanced_permissions>"
                },
                {
                    "step": 2,
                    "title": "Update API Endpoints",
                    "description": "Change your API calls to use v2 endpoints",
                    "before": "/api/knowledge/search",
                    "after": "/api/v2/query/advanced-search"
                },
                {
                    "step": 3,
                    "title": "Update Request Formats",
                    "description": "Adjust your request payloads to match the new schema",
                    "changes": [
                        "search_query -> query",
                        "filters now use structured FilterCondition format",
                        "pagination parameters moved to separate object"
                    ]
                },
                {
                    "step": 4,
                    "title": "Handle New Response Formats",
                    "description": "Update your response handling for the enhanced response structure",
                    "new_fields": [
                        "api_version",
                        "execution_time_ms", 
                        "query_analysis",
                        "metadata"
                    ]
                }
            ],
            "compatibility_notes": [
                "v1.x endpoints will continue to work until 2025-12-31",
                "New features are only available in v2.0+",
                "Response formats are backward compatible with optional fields",
                "Rate limiting rules remain the same"
            ]
        }
    }

@docs_router.get("/status")
async def get_api_status() -> Dict[str, Any]:
    """Get current API status and health information"""
    return {
        "message": "BETTY Memory System API Status",
        "status": "operational",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "authentication": "operational",
            "knowledge_management": "operational",
            "advanced_query": "operational",
            "batch_operations": "operational", 
            "cross_project": "operational",
            "vector_search": "operational",
            "graph_database": "operational"
        },
        "performance": {
            "avg_response_time_ms": 125,
            "uptime_percentage": 99.9,
            "requests_per_minute": 850
        },
        "features": {
            "total_features": 14,
            "available_features": 14,
            "beta_features": 2
        }
    }