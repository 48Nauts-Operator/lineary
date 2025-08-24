#!/usr/bin/env python3
"""
BETTY Memory System v2.0 - API Endpoint Mapper

This tool provides mapping between v1.x and v2.0 API endpoints,
request/response transformations, and compatibility helpers.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse, urljoin
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class EndpointMapping:
    """Mapping between v1.x and v2.0 API endpoints."""
    v1_method: str
    v1_path: str
    v2_method: str
    v2_path: str
    request_transformer: Optional[str] = None
    response_transformer: Optional[str] = None
    deprecated: bool = False
    notes: Optional[str] = None
    breaking_changes: List[str] = None
    
    def __post_init__(self):
        if self.breaking_changes is None:
            self.breaking_changes = []


@dataclass
class APIChange:
    """Documentation of API changes between versions."""
    category: str  # 'breaking', 'deprecation', 'new_feature', 'enhancement'
    endpoint: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    migration_guide: str
    examples: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = {}


class APIMapper:
    """
    Map API endpoints and requests between BETTY v1.x and v2.0.
    
    Provides:
    - Endpoint mapping and translation
    - Request/response format transformation
    - Deprecation warnings and migration guidance
    - Breaking change documentation
    - Compatibility layer suggestions
    """
    
    def __init__(self, log_level: str = "INFO"):
        """
        Initialize API mapper.
        
        Args:
            log_level: Logging level
        """
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize mappings
        self.endpoint_mappings = self._initialize_endpoint_mappings()
        self.api_changes = self._initialize_api_changes()
        
        # Request/response transformers
        self.request_transformers = self._initialize_request_transformers()
        self.response_transformers = self._initialize_response_transformers()
    
    def _initialize_endpoint_mappings(self) -> List[EndpointMapping]:
        """Initialize endpoint mappings between v1.x and v2.0."""
        return [
            # Knowledge Management
            EndpointMapping(
                v1_method="POST",
                v1_path="/api/v1/knowledge/add",
                v2_method="POST",
                v2_path="/api/v2/knowledge/add",
                request_transformer="transform_add_knowledge_request",
                response_transformer="transform_add_knowledge_response",
                breaking_changes=[
                    "Field 'type' renamed to 'knowledge_type'",
                    "Metadata structure changed to nested format",
                    "Response includes additional fields: id, embeddings, access_control"
                ]
            ),
            
            EndpointMapping(
                v1_method="GET",
                v1_path="/api/v1/knowledge/{id}",
                v2_method="GET",
                v2_path="/api/v2/knowledge/{id}",
                response_transformer="transform_get_knowledge_response",
                breaking_changes=[
                    "Response includes additional metadata fields",
                    "Embeddings data now included in response",
                    "Access control information added"
                ]
            ),
            
            EndpointMapping(
                v1_method="PUT",
                v1_path="/api/v1/knowledge/{id}",
                v2_method="PUT",
                v2_path="/api/v2/knowledge/{id}",
                request_transformer="transform_update_knowledge_request",
                response_transformer="transform_update_knowledge_response",
                breaking_changes=[
                    "Field 'type' renamed to 'knowledge_type'",
                    "Partial updates now supported with different semantics"
                ]
            ),
            
            EndpointMapping(
                v1_method="DELETE",
                v1_path="/api/v1/knowledge/{id}",
                v2_method="DELETE",
                v2_path="/api/v2/knowledge/{id}",
                notes="Soft delete behavior changed - items are marked as deleted, not removed"
            ),
            
            # Search Endpoints
            EndpointMapping(
                v1_method="GET",
                v1_path="/api/v1/search",
                v2_method="POST",
                v2_path="/api/v2/query/advanced-search",
                request_transformer="transform_search_request",
                response_transformer="transform_search_response",
                breaking_changes=[
                    "Changed from GET to POST method",
                    "Query parameters moved to request body",
                    "Response format completely restructured",
                    "New search types and ranking algorithms available"
                ],
                notes="Major endpoint restructure - see advanced search documentation"
            ),
            
            EndpointMapping(
                v1_method="POST",
                v1_path="/api/v1/search/semantic",
                v2_method="POST",
                v2_path="/api/v2/query/advanced-search",
                request_transformer="transform_semantic_search_request",
                response_transformer="transform_search_response",
                breaking_changes=[
                    "Merged into advanced search endpoint",
                    "Use search_type: 'semantic' parameter"
                ]
            ),
            
            # New v2.0 Endpoints (no v1.x equivalent)
            EndpointMapping(
                v1_method="",
                v1_path="",
                v2_method="POST",
                v2_path="/api/v2/query/pattern-match",
                notes="New in v2.0 - Pattern matching capabilities"
            ),
            
            EndpointMapping(
                v1_method="",
                v1_path="",
                v2_method="POST",
                v2_path="/api/v2/query/semantic-clusters",
                notes="New in v2.0 - Semantic clustering functionality"
            ),
            
            EndpointMapping(
                v1_method="",
                v1_path="",
                v2_method="POST",
                v2_path="/api/v2/batch/knowledge/import",
                notes="New in v2.0 - Batch import operations"
            ),
            
            EndpointMapping(
                v1_method="",
                v1_path="",
                v2_method="POST",
                v2_path="/api/v2/cross-project/search",
                notes="New in v2.0 - Cross-project intelligence"
            ),
            
            # User Management
            EndpointMapping(
                v1_method="GET",
                v1_path="/api/v1/users/profile",
                v2_method="GET",
                v2_path="/api/v2/users/profile",
                response_transformer="transform_user_profile_response",
                breaking_changes=[
                    "Profile structure expanded with new fields",
                    "Role and permissions format changed"
                ]
            ),
            
            # Authentication
            EndpointMapping(
                v1_method="POST",
                v1_path="/api/v1/auth/login",
                v2_method="POST",
                v2_path="/api/v2/auth/login",
                request_transformer="transform_auth_request",
                response_transformer="transform_auth_response",
                breaking_changes=[
                    "JWT token structure changed",
                    "Additional claims added to token",
                    "Refresh token mechanism introduced"
                ]
            ),
            
            # Deprecated v1.x Endpoints
            EndpointMapping(
                v1_method="GET",
                v1_path="/api/v1/knowledge/list",
                v2_method="POST",
                v2_path="/api/v2/query/advanced-search",
                deprecated=True,
                request_transformer="transform_list_to_search_request",
                response_transformer="transform_search_response",
                breaking_changes=[
                    "Replaced by advanced search with empty query",
                    "Pagination parameters changed",
                    "Filtering moved to request body"
                ],
                notes="Deprecated - use advanced search with appropriate filters"
            ),
            
            # System Endpoints
            EndpointMapping(
                v1_method="GET",
                v1_path="/api/v1/health",
                v2_method="GET",
                v2_path="/api/health",
                notes="Health check endpoint moved to root level"
            ),
            
            EndpointMapping(
                v1_method="GET",
                v1_path="/api/v1/version",
                v2_method="GET",
                v2_path="/api/version/info",
                response_transformer="transform_version_response",
                breaking_changes=[
                    "Response format expanded with more detailed version information"
                ]
            ),
        ]
    
    def _initialize_api_changes(self) -> List[APIChange]:
        """Initialize documentation of API changes."""
        return [
            APIChange(
                category="breaking",
                endpoint="/api/v1/search",
                description="Search endpoint changed from GET to POST with body parameters",
                impact="high",
                migration_guide="Update HTTP method and move query parameters to request body",
                examples={
                    "v1_request": {
                        "method": "GET",
                        "url": "/api/v1/search?q=machine%20learning&limit=10&type=document"
                    },
                    "v2_request": {
                        "method": "POST",
                        "url": "/api/v2/query/advanced-search",
                        "body": {
                            "query": "machine learning",
                            "max_results": 10,
                            "search_type": "hybrid",
                            "filters": [{"field": "knowledge_type", "operator": "eq", "value": "document"}]
                        }
                    }
                }
            ),
            
            APIChange(
                category="breaking",
                endpoint="/api/v1/knowledge/*",
                description="Knowledge type field renamed from 'type' to 'knowledge_type'",
                impact="medium",
                migration_guide="Update all requests to use 'knowledge_type' instead of 'type'",
                examples={
                    "v1_field": {"type": "document"},
                    "v2_field": {"knowledge_type": "document"}
                }
            ),
            
            APIChange(
                category="new_feature",
                endpoint="/api/v2/query/pattern-match",
                description="New pattern matching capabilities for knowledge graphs",
                impact="low",
                migration_guide="No migration required - new feature",
                examples={
                    "usage": {
                        "method": "POST",
                        "url": "/api/v2/query/pattern-match",
                        "body": {
                            "pattern_type": "relationship_chains",
                            "max_depth": 5,
                            "min_confidence": 0.7
                        }
                    }
                }
            ),
            
            APIChange(
                category="enhancement",
                endpoint="/api/v2/auth/login",
                description="JWT tokens now include additional claims and RBAC information",
                impact="low",
                migration_guide="Update token parsing to handle new claims structure",
                examples={
                    "v1_token_claims": {
                        "user_id": "123",
                        "username": "user",
                        "exp": 1234567890
                    },
                    "v2_token_claims": {
                        "user_id": "123",
                        "username": "user",
                        "role": "user",
                        "permissions": ["knowledge:read", "knowledge:write"],
                        "project_access": ["project1", "project2"],
                        "exp": 1234567890,
                        "iat": 1234560000
                    }
                }
            ),
            
            APIChange(
                category="deprecation",
                endpoint="/api/v1/knowledge/list",
                description="List endpoint deprecated in favor of advanced search",
                impact="medium",
                migration_guide="Replace with POST to /api/v2/query/advanced-search with empty query",
                examples={
                    "deprecated": {
                        "method": "GET",
                        "url": "/api/v1/knowledge/list?page=1&limit=20&type=document"
                    },
                    "replacement": {
                        "method": "POST",
                        "url": "/api/v2/query/advanced-search",
                        "body": {
                            "query": "",
                            "max_results": 20,
                            "filters": [{"field": "knowledge_type", "operator": "eq", "value": "document"}]
                        }
                    }
                }
            )
        ]
    
    def _initialize_request_transformers(self) -> Dict[str, Callable]:
        """Initialize request transformation functions."""
        return {
            "transform_add_knowledge_request": self._transform_add_knowledge_request,
            "transform_update_knowledge_request": self._transform_update_knowledge_request,
            "transform_search_request": self._transform_search_request,
            "transform_semantic_search_request": self._transform_semantic_search_request,
            "transform_auth_request": self._transform_auth_request,
            "transform_list_to_search_request": self._transform_list_to_search_request,
        }
    
    def _initialize_response_transformers(self) -> Dict[str, Callable]:
        """Initialize response transformation functions."""
        return {
            "transform_add_knowledge_response": self._transform_add_knowledge_response,
            "transform_get_knowledge_response": self._transform_get_knowledge_response,
            "transform_update_knowledge_response": self._transform_update_knowledge_response,
            "transform_search_response": self._transform_search_response,
            "transform_user_profile_response": self._transform_user_profile_response,
            "transform_auth_response": self._transform_auth_response,
            "transform_version_response": self._transform_version_response,
        }
    
    def find_mapping(self, v1_method: str, v1_path: str) -> Optional[EndpointMapping]:
        """
        Find endpoint mapping for v1.x endpoint.
        
        Args:
            v1_method: HTTP method
            v1_path: API path (supports path parameters with {})
            
        Returns:
            EndpointMapping if found, None otherwise
        """
        # Normalize path by removing query parameters
        clean_path = v1_path.split('?')[0]
        
        for mapping in self.endpoint_mappings:
            if mapping.v1_method == v1_method:
                # Check for exact match first
                if mapping.v1_path == clean_path:
                    return mapping
                
                # Check for parameterized path match
                if self._paths_match(mapping.v1_path, clean_path):
                    return mapping
        
        return None
    
    def _paths_match(self, pattern_path: str, actual_path: str) -> bool:
        """Check if actual path matches pattern with parameters."""
        # Convert path pattern to regex
        pattern = re.escape(pattern_path)
        pattern = re.sub(r'\\{[^}]+\\}', r'[^/]+', pattern)
        pattern = f'^{pattern}$'
        
        return bool(re.match(pattern, actual_path))
    
    def transform_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """
        Transform v1.x request to v2.0 format.
        
        Args:
            v1_request: Original v1.x request
            mapping: Endpoint mapping information
            
        Returns:
            Transformed v2.0 request
        """
        if not mapping.request_transformer:
            return v1_request
        
        transformer = self.request_transformers.get(mapping.request_transformer)
        if transformer:
            return transformer(v1_request, mapping)
        
        self.logger.warning(f"Request transformer not found: {mapping.request_transformer}")
        return v1_request
    
    def transform_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """
        Transform v2.0 response to v1.x compatible format.
        
        Args:
            v2_response: v2.0 API response
            mapping: Endpoint mapping information
            
        Returns:
            v1.x compatible response
        """
        if not mapping.response_transformer:
            return v2_response
        
        transformer = self.response_transformers.get(mapping.response_transformer)
        if transformer:
            return transformer(v2_response, mapping)
        
        self.logger.warning(f"Response transformer not found: {mapping.response_transformer}")
        return v2_response
    
    def get_migration_guide(self, v1_method: str, v1_path: str) -> Dict[str, Any]:
        """
        Get comprehensive migration guide for a v1.x endpoint.
        
        Args:
            v1_method: HTTP method
            v1_path: API path
            
        Returns:
            Migration guide with mapping, changes, and examples
        """
        mapping = self.find_mapping(v1_method, v1_path)
        
        if not mapping:
            return {
                "status": "not_found",
                "message": f"No mapping found for {v1_method} {v1_path}",
                "suggestions": self._suggest_similar_endpoints(v1_path)
            }
        
        # Find related API changes
        related_changes = [
            change for change in self.api_changes
            if v1_path.startswith(change.endpoint) or change.endpoint in v1_path
        ]
        
        guide = {
            "status": "found",
            "mapping": asdict(mapping),
            "migration_steps": self._generate_migration_steps(mapping),
            "breaking_changes": mapping.breaking_changes,
            "related_changes": [asdict(change) for change in related_changes],
            "code_examples": self._generate_code_examples(mapping),
            "testing_recommendations": self._generate_testing_recommendations(mapping)
        }
        
        if mapping.deprecated:
            guide["deprecation_warning"] = f"Endpoint {v1_path} is deprecated. " + (mapping.notes or "")
        
        return guide
    
    def _suggest_similar_endpoints(self, v1_path: str) -> List[str]:
        """Suggest similar endpoints for unmapped paths."""
        suggestions = []
        path_parts = v1_path.split('/')
        
        for mapping in self.endpoint_mappings:
            if any(part in mapping.v1_path for part in path_parts if part):
                suggestions.append(f"{mapping.v1_method} {mapping.v1_path} -> {mapping.v2_method} {mapping.v2_path}")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _generate_migration_steps(self, mapping: EndpointMapping) -> List[str]:
        """Generate step-by-step migration instructions."""
        steps = []
        
        # Method change
        if mapping.v1_method != mapping.v2_method:
            steps.append(f"Change HTTP method from {mapping.v1_method} to {mapping.v2_method}")
        
        # URL change
        if mapping.v1_path != mapping.v2_path:
            steps.append(f"Update URL from {mapping.v1_path} to {mapping.v2_path}")
        
        # Request transformation
        if mapping.request_transformer:
            steps.append("Transform request format (see code examples)")
        
        # Response handling
        if mapping.response_transformer:
            steps.append("Update response handling for new format")
        
        # Breaking changes
        for change in mapping.breaking_changes:
            steps.append(f"Handle breaking change: {change}")
        
        return steps
    
    def _generate_code_examples(self, mapping: EndpointMapping) -> Dict[str, Any]:
        """Generate code examples for migration."""
        examples = {
            "v1_example": {
                "method": mapping.v1_method,
                "url": mapping.v1_path,
            },
            "v2_example": {
                "method": mapping.v2_method,
                "url": mapping.v2_path,
            }
        }
        
        # Add specific examples based on endpoint
        if "knowledge/add" in mapping.v2_path:
            examples["v1_example"]["body"] = {
                "title": "Example Document",
                "content": "This is example content",
                "type": "document",
                "tags": ["example", "test"]
            }
            examples["v2_example"]["body"] = {
                "title": "Example Document",
                "content": "This is example content",
                "knowledge_type": "document",
                "metadata": {
                    "tags": ["example", "test"]
                }
            }
        
        elif "search" in mapping.v1_path:
            examples["v1_example"]["url"] = "/api/v1/search?q=example&limit=10"
            examples["v2_example"]["body"] = {
                "query": "example",
                "max_results": 10,
                "search_type": "hybrid"
            }
        
        return examples
    
    def _generate_testing_recommendations(self, mapping: EndpointMapping) -> List[str]:
        """Generate testing recommendations for migration."""
        recommendations = []
        
        recommendations.append("Test with existing production data")
        recommendations.append("Validate response format matches expectations")
        
        if mapping.breaking_changes:
            recommendations.append("Specifically test all breaking changes")
        
        if mapping.deprecated:
            recommendations.append("Plan deprecation timeline and communication")
        
        if mapping.request_transformer or mapping.response_transformer:
            recommendations.append("Test request/response transformations thoroughly")
        
        return recommendations
    
    # Request Transformation Methods
    
    def _transform_add_knowledge_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform add knowledge request from v1.x to v2.0."""
        v2_request = v1_request.copy()
        
        # Rename 'type' to 'knowledge_type'
        if 'type' in v2_request:
            v2_request['knowledge_type'] = v2_request.pop('type')
        
        # Move tags to metadata
        if 'tags' in v2_request:
            metadata = v2_request.get('metadata', {})
            metadata['tags'] = v2_request.pop('tags')
            v2_request['metadata'] = metadata
        
        return v2_request
    
    def _transform_update_knowledge_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform update knowledge request from v1.x to v2.0."""
        return self._transform_add_knowledge_request(v1_request, mapping)
    
    def _transform_search_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform search request from v1.x to v2.0."""
        # Extract query parameters from URL or body
        query_params = v1_request.get('params', {})
        
        v2_request = {
            "query": query_params.get('q', query_params.get('query', '')),
            "search_type": "hybrid",
            "max_results": int(query_params.get('limit', 20)),
            "similarity_threshold": 0.7
        }
        
        # Convert filters
        if 'type' in query_params:
            v2_request['filters'] = [{
                "field": "knowledge_type",
                "operator": "eq",
                "value": query_params['type']
            }]
        
        return v2_request
    
    def _transform_semantic_search_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform semantic search request from v1.x to v2.0."""
        v2_request = self._transform_search_request(v1_request, mapping)
        v2_request['search_type'] = 'semantic'
        return v2_request
    
    def _transform_auth_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform auth request from v1.x to v2.0."""
        # Auth requests are generally compatible, but may need additional fields
        return v1_request
    
    def _transform_list_to_search_request(self, v1_request: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform list request to search request."""
        query_params = v1_request.get('params', {})
        
        v2_request = {
            "query": "",  # Empty query for listing
            "search_type": "hybrid",
            "max_results": int(query_params.get('limit', 20)),
            "include_metadata": True
        }
        
        # Add filters from original request
        filters = []
        
        if 'type' in query_params:
            filters.append({
                "field": "knowledge_type",
                "operator": "eq",
                "value": query_params['type']
            })
        
        if 'project_id' in query_params:
            filters.append({
                "field": "project_id",
                "operator": "eq",
                "value": query_params['project_id']
            })
        
        if filters:
            v2_request['filters'] = filters
        
        return v2_request
    
    # Response Transformation Methods
    
    def _transform_add_knowledge_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform add knowledge response from v2.0 to v1.x format."""
        v1_response = v2_response.copy()
        
        # Remove v2.0 specific fields for v1.x compatibility
        v1_response.pop('embeddings', None)
        v1_response.pop('access_control', None)
        v1_response.pop('version', None)
        
        # Rename knowledge_type back to type
        if 'data' in v1_response and 'knowledge_type' in v1_response['data']:
            v1_response['data']['type'] = v1_response['data'].pop('knowledge_type')
        
        return v1_response
    
    def _transform_get_knowledge_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform get knowledge response from v2.0 to v1.x format."""
        return self._transform_add_knowledge_response(v2_response, mapping)
    
    def _transform_update_knowledge_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform update knowledge response from v2.0 to v1.x format."""
        return self._transform_add_knowledge_response(v2_response, mapping)
    
    def _transform_search_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform search response from v2.0 to v1.x format."""
        v1_response = v2_response.copy()
        
        if 'data' in v1_response and 'results' in v1_response['data']:
            # Transform each result item
            transformed_results = []
            
            for result in v1_response['data']['results']:
                transformed_result = result.copy()
                
                # Remove v2.0 specific fields
                transformed_result.pop('similarity_score', None)
                transformed_result.pop('ranking_score', None)
                transformed_result.pop('embeddings', None)
                
                # Rename knowledge_type back to type
                if 'knowledge_type' in transformed_result:
                    transformed_result['type'] = transformed_result.pop('knowledge_type')
                
                transformed_results.append(transformed_result)
            
            v1_response['data']['results'] = transformed_results
            
            # Simplify metadata
            if 'search_metadata' in v1_response['data']:
                metadata = v1_response['data']['search_metadata']
                v1_response['data']['total'] = metadata.get('total_results', 0)
                v1_response['data'].pop('search_metadata')
        
        return v1_response
    
    def _transform_user_profile_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform user profile response from v2.0 to v1.x format."""
        v1_response = v2_response.copy()
        
        if 'data' in v1_response:
            user_data = v1_response['data']
            
            # Flatten profile information
            if 'profile' in user_data:
                profile = user_data.pop('profile')
                user_data.update(profile)
            
            # Simplify permissions
            if 'permissions' in user_data and isinstance(user_data['permissions'], list):
                # Convert v2.0 permissions to v1.x format
                v1_permissions = []
                for perm in user_data['permissions']:
                    if perm.startswith('knowledge:'):
                        v1_permissions.append(perm.split(':')[1])
                user_data['permissions'] = v1_permissions
        
        return v1_response
    
    def _transform_auth_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform auth response from v2.0 to v1.x format."""
        v1_response = v2_response.copy()
        
        # Remove v2.0 specific auth fields
        if 'data' in v1_response:
            v1_response['data'].pop('refresh_token', None)
            v1_response['data'].pop('token_type', None)
        
        return v1_response
    
    def _transform_version_response(self, v2_response: Dict[str, Any], mapping: EndpointMapping) -> Dict[str, Any]:
        """Transform version response from v2.0 to v1.x format."""
        v1_response = v2_response.copy()
        
        if 'data' in v1_response:
            version_data = v1_response['data']
            
            # Simplify version information for v1.x compatibility
            v1_response['data'] = {
                "version": version_data.get('api_version', '2.0.0'),
                "build": version_data.get('build_info', {}).get('commit', 'unknown')
            }
        
        return v1_response
    
    def generate_compatibility_report(self) -> Dict[str, Any]:
        """Generate comprehensive compatibility report between v1.x and v2.0."""
        report = {
            "summary": {
                "total_v1_endpoints": len([m for m in self.endpoint_mappings if m.v1_path]),
                "mapped_endpoints": len([m for m in self.endpoint_mappings if m.v1_path and m.v2_path]),
                "deprecated_endpoints": len([m for m in self.endpoint_mappings if m.deprecated]),
                "new_v2_endpoints": len([m for m in self.endpoint_mappings if not m.v1_path]),
                "breaking_changes": len([c for c in self.api_changes if c.category == "breaking"])
            },
            "endpoint_mappings": [asdict(mapping) for mapping in self.endpoint_mappings],
            "api_changes": [asdict(change) for change in self.api_changes],
            "migration_priority": self._generate_migration_priority(),
            "compatibility_matrix": self._generate_compatibility_matrix(),
            "recommendations": self._generate_migration_recommendations()
        }
        
        return report
    
    def _generate_migration_priority(self) -> List[Dict[str, Any]]:
        """Generate migration priority list based on impact and usage."""
        priorities = []
        
        for mapping in self.endpoint_mappings:
            if not mapping.v1_path:  # Skip new v2.0 endpoints
                continue
            
            priority_score = 0
            
            # High priority for breaking changes
            if mapping.breaking_changes:
                priority_score += len(mapping.breaking_changes) * 3
            
            # High priority for deprecated endpoints
            if mapping.deprecated:
                priority_score += 5
            
            # Medium priority for method changes
            if mapping.v1_method != mapping.v2_method:
                priority_score += 2
            
            # Low priority for response-only changes
            if mapping.response_transformer and not mapping.request_transformer:
                priority_score += 1
            
            priorities.append({
                "endpoint": f"{mapping.v1_method} {mapping.v1_path}",
                "priority_score": priority_score,
                "priority_level": "high" if priority_score >= 5 else "medium" if priority_score >= 2 else "low",
                "breaking_changes": mapping.breaking_changes,
                "deprecated": mapping.deprecated
            })
        
        return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)
    
    def _generate_compatibility_matrix(self) -> Dict[str, Any]:
        """Generate compatibility matrix showing what works across versions."""
        matrix = {
            "fully_compatible": [],  # No changes needed
            "request_compatible": [],  # Only response format changed
            "response_compatible": [],  # Only request format changed
            "breaking_changes": [],  # Both request and response changed
            "deprecated": [],  # Deprecated endpoints
            "new_in_v2": []  # New v2.0 endpoints
        }
        
        for mapping in self.endpoint_mappings:
            endpoint_id = f"{mapping.v1_method} {mapping.v1_path}" if mapping.v1_path else f"{mapping.v2_method} {mapping.v2_path}"
            
            if not mapping.v1_path:
                matrix["new_in_v2"].append(endpoint_id)
            elif mapping.deprecated:
                matrix["deprecated"].append(endpoint_id)
            elif mapping.breaking_changes:
                matrix["breaking_changes"].append(endpoint_id)
            elif mapping.request_transformer and mapping.response_transformer:
                matrix["breaking_changes"].append(endpoint_id)
            elif mapping.request_transformer:
                matrix["response_compatible"].append(endpoint_id)
            elif mapping.response_transformer:
                matrix["request_compatible"].append(endpoint_id)
            else:
                matrix["fully_compatible"].append(endpoint_id)
        
        return matrix
    
    def _generate_migration_recommendations(self) -> List[str]:
        """Generate migration recommendations."""
        return [
            "Start with fully compatible endpoints to build confidence",
            "Address deprecated endpoints first to avoid future breaking changes",
            "Test request/response transformations thoroughly in staging environment",
            "Implement gradual migration with fallback mechanisms",
            "Update client SDKs before migrating server endpoints",
            "Monitor API usage patterns to prioritize most-used endpoints",
            "Set up comprehensive logging during migration period",
            "Plan rollback procedures for each migration step",
            "Communicate breaking changes to all API consumers well in advance",
            "Consider implementing compatibility layer for smooth transition"
        ]
    
    def save_report(self, output_path: str):
        """Save compatibility report to file."""
        report = self.generate_compatibility_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Compatibility report saved to {output_path}")


async def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="BETTY API endpoint mapper and compatibility checker")
    parser.add_argument("--action", required=True, choices=["map", "report", "guide"], help="Action to perform")
    parser.add_argument("--method", help="HTTP method for mapping lookup")
    parser.add_argument("--path", help="API path for mapping lookup")
    parser.add_argument("--output", help="Output file for reports")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    mapper = APIMapper(log_level=args.log_level)
    
    if args.action == "map" and args.method and args.path:
        # Find mapping for specific endpoint
        mapping = mapper.find_mapping(args.method, args.path)
        
        if mapping:
            print(json.dumps(asdict(mapping), indent=2))
        else:
            print(f"No mapping found for {args.method} {args.path}")
            suggestions = mapper._suggest_similar_endpoints(args.path)
            if suggestions:
                print("Similar endpoints:")
                for suggestion in suggestions:
                    print(f"  {suggestion}")
    
    elif args.action == "guide" and args.method and args.path:
        # Generate migration guide
        guide = mapper.get_migration_guide(args.method, args.path)
        print(json.dumps(guide, indent=2))
    
    elif args.action == "report":
        # Generate compatibility report
        report = mapper.generate_compatibility_report()
        
        if args.output:
            mapper.save_report(args.output)
        else:
            print(json.dumps(report, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())