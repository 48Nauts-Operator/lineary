"""
BETTY Memory System Python SDK - Utilities

This module provides utility functions for the BETTY Python SDK,
including JWT token validation, filter formatting, and result processing.
"""

import json
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import re

from .exceptions import BettyException, ValidationException


def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Validate and decode JWT token (without signature verification).
    
    Note: This only validates the format and extracts claims.
    Signature verification is handled by the API server.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing token claims
        
    Raises:
        BettyException: If token format is invalid
    """
    
    if not token or not isinstance(token, str):
        raise BettyException("API key must be a non-empty string")
    
    # Split JWT into parts
    parts = token.split('.')
    
    if len(parts) != 3:
        raise BettyException("Invalid JWT format. Expected 3 parts separated by dots.")
    
    try:
        # Decode header
        header_data = parts[0] + '=' * (4 - len(parts[0]) % 4)  # Add padding
        header = json.loads(base64.urlsafe_b64decode(header_data))
        
        # Decode payload
        payload_data = parts[1] + '=' * (4 - len(parts[1]) % 4)  # Add padding
        payload = json.loads(base64.urlsafe_b64decode(payload_data))
        
        # Validate required claims
        if 'exp' not in payload:
            raise BettyException("JWT token missing 'exp' (expiration) claim")
        
        # Check if token is expired (with 5 minute buffer)
        exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        if exp_time < current_time:
            raise BettyException("JWT token has expired")
        
        return {
            'header': header,
            'payload': payload,
            'valid': True,
            'expires_at': exp_time,
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'permissions': payload.get('permissions', []),
            'role': payload.get('role')
        }
        
    except json.JSONDecodeError as e:
        raise BettyException(f"Invalid JWT JSON format: {e}")
    except Exception as e:
        raise BettyException(f"Failed to validate JWT token: {e}")


def extract_permissions_from_token(token: str) -> List[str]:
    """
    Extract permissions from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        List of permission strings
    """
    
    try:
        token_data = validate_jwt_token(token)
        return token_data.get('permissions', [])
    except Exception:
        return []


def check_permission(token: str, required_permission: str) -> bool:
    """
    Check if token contains a specific permission.
    
    Args:
        token: JWT token string
        required_permission: Permission to check for
        
    Returns:
        True if permission is present, False otherwise
    """
    
    permissions = extract_permissions_from_token(token)
    return required_permission in permissions


def format_filters(filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format and validate filter conditions for API requests.
    
    Args:
        filters: List of filter dictionaries
        
    Returns:
        Formatted and validated filters
        
    Raises:
        ValidationException: If filter format is invalid
    """
    
    if not filters:
        return []
    
    if not isinstance(filters, list):
        raise ValidationException(
            message="Filters must be a list of filter objects",
            field_errors={"filters": ["Must be a list"]}
        )
    
    formatted_filters = []
    
    for i, filter_obj in enumerate(filters):
        if not isinstance(filter_obj, dict):
            raise ValidationException(
                message="Each filter must be a dictionary",
                field_errors={f"filters[{i}]": ["Must be a dictionary"]}
            )
        
        # Required fields
        required_fields = ['field', 'operator', 'value']
        missing_fields = [field for field in required_fields if field not in filter_obj]
        
        if missing_fields:
            raise ValidationException(
                message=f"Filter {i} missing required fields",
                field_errors={f"filters[{i}]": [f"Missing fields: {', '.join(missing_fields)}"]}
            )
        
        # Validate operator
        valid_operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'contains']
        operator = filter_obj['operator']
        
        if operator not in valid_operators:
            raise ValidationException(
                message=f"Invalid operator in filter {i}",
                field_errors={f"filters[{i}].operator": [f"Must be one of: {', '.join(valid_operators)}"]}
            )
        
        # Validate value for 'in' operator
        if operator == 'in' and not isinstance(filter_obj['value'], list):
            raise ValidationException(
                message=f"Filter {i} with 'in' operator must have list value",
                field_errors={f"filters[{i}].value": ["Must be a list when using 'in' operator"]}
            )
        
        formatted_filters.append({
            'field': filter_obj['field'],
            'operator': operator,
            'value': filter_obj['value']
        })
    
    return formatted_filters


def merge_search_results(result_sets: List[List[Dict]], 
                        merge_strategy: str = "score",
                        max_results: int = None) -> List[Dict]:
    """
    Merge multiple search result sets using different strategies.
    
    Args:
        result_sets: List of result sets to merge
        merge_strategy: Strategy for merging ("score", "round_robin", "weighted")
        max_results: Maximum number of results to return
        
    Returns:
        Merged list of results
    """
    
    if not result_sets:
        return []
    
    # Flatten all results and track source
    all_results = []
    seen_ids = set()
    
    for set_idx, result_set in enumerate(result_sets):
        for result in result_set:
            # Skip duplicates based on ID
            result_id = result.get('id')
            if result_id and result_id in seen_ids:
                continue
            
            # Add source information
            result_copy = result.copy()
            result_copy['_source_set'] = set_idx
            
            all_results.append(result_copy)
            if result_id:
                seen_ids.add(result_id)
    
    # Apply merge strategy
    if merge_strategy == "score":
        # Sort by similarity or ranking score (descending)
        all_results.sort(key=lambda x: x.get('similarity_score', x.get('ranking_score', 0)), reverse=True)
    
    elif merge_strategy == "round_robin":
        # Interleave results from different sets
        merged = []
        max_set_length = max(len(rs) for rs in result_sets) if result_sets else 0
        
        for i in range(max_set_length):
            for set_idx, result_set in enumerate(result_sets):
                if i < len(result_set):
                    result_id = result_set[i].get('id')
                    if not result_id or result_id not in seen_ids:
                        result_copy = result_set[i].copy()
                        result_copy['_source_set'] = set_idx
                        merged.append(result_copy)
                        if result_id:
                            seen_ids.add(result_id)
        
        all_results = merged
    
    elif merge_strategy == "weighted":
        # Weight results based on source set index (earlier sets weighted higher)
        def weighted_score(result):
            base_score = result.get('similarity_score', result.get('ranking_score', 0))
            set_weight = 1.0 - (result.get('_source_set', 0) * 0.1)  # Reduce by 10% per set
            return base_score * set_weight
        
        all_results.sort(key=weighted_score, reverse=True)
    
    # Remove internal fields
    for result in all_results:
        result.pop('_source_set', None)
    
    # Limit results if specified
    if max_results and max_results > 0:
        all_results = all_results[:max_results]
    
    return all_results


def sanitize_query(query: str) -> str:
    """
    Sanitize search query by removing potentially harmful content.
    
    Args:
        query: Search query string
        
    Returns:
        Sanitized query string
    """
    
    if not query or not isinstance(query, str):
        return ""
    
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query.strip())
    
    # Remove potential SQL injection patterns (basic protection)
    dangerous_patterns = [
        r';\s*DROP\s+TABLE',
        r';\s*DELETE\s+FROM',
        r';\s*INSERT\s+INTO',
        r';\s*UPDATE\s+',
        r'UNION\s+SELECT',
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
    ]
    
    for pattern in dangerous_patterns:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    
    # Limit query length
    MAX_QUERY_LENGTH = 1000
    if len(query) > MAX_QUERY_LENGTH:
        query = query[:MAX_QUERY_LENGTH]
    
    return query


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: String to validate as UUID
        
    Returns:
        True if valid UUID format, False otherwise
    """
    
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    return bool(uuid_pattern.match(uuid_string))


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracking.
    
    Returns:
        Unique request ID string
    """
    
    # Combine timestamp and random component
    timestamp = datetime.now(timezone.utc).isoformat()
    hash_input = f"{timestamp}-{id(object())}"
    
    # Create short hash
    hash_object = hashlib.sha256(hash_input.encode())
    short_hash = hash_object.hexdigest()[:12]
    
    return f"betty-{short_hash}"


def format_datetime(dt: datetime) -> str:
    """
    Format datetime for API requests.
    
    Args:
        dt: Datetime object
        
    Returns:
        ISO 8601 formatted string
    """
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def parse_datetime(dt_string: str) -> datetime:
    """
    Parse datetime string from API responses.
    
    Args:
        dt_string: ISO 8601 datetime string
        
    Returns:
        Datetime object
    """
    
    try:
        # Handle different datetime formats
        if dt_string.endswith('Z'):
            dt_string = dt_string[:-1] + '+00:00'
        
        return datetime.fromisoformat(dt_string)
    
    except ValueError as e:
        raise BettyException(f"Invalid datetime format: {dt_string}") from e


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate basic text similarity score.
    
    Note: This is a simple implementation for utility purposes.
    The actual semantic similarity is calculated by the BETTY API.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0 and 1
    """
    
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text using simple heuristics.
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of extracted keywords
    """
    
    if not text:
        return []
    
    # Convert to lowercase and split
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
        'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Filter and count words
    word_counts = {}
    for word in words:
        if len(word) > 2 and word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    
    return chunks


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def mask_sensitive_data(data: Dict[str, Any], 
                       sensitive_fields: List[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive fields in dictionary for logging.
    
    Args:
        data: Dictionary containing potentially sensitive data
        sensitive_fields: List of field names to mask
        
    Returns:
        Dictionary with sensitive fields masked
    """
    
    if sensitive_fields is None:
        sensitive_fields = ['api_key', 'token', 'password', 'secret', 'key']
    
    masked_data = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field name contains sensitive keywords
        is_sensitive = any(sensitive in key_lower for sensitive in sensitive_fields)
        
        if is_sensitive and isinstance(value, str) and len(value) > 8:
            # Mask middle part, show first and last few characters
            masked_data[key] = f"{value[:4]}...{value[-4:]}"
        elif isinstance(value, dict):
            # Recursively mask nested dictionaries
            masked_data[key] = mask_sensitive_data(value, sensitive_fields)
        else:
            masked_data[key] = value
    
    return masked_data


def retry_with_backoff(max_retries: int = 3, 
                      base_delay: float = 1.0,
                      backoff_factor: float = 2.0,
                      max_delay: float = 60.0):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries
        backoff_factor: Backoff multiplier
        max_delay: Maximum delay between retries
        
    Returns:
        Decorator function
    """
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import asyncio
            from .exceptions import is_retryable_exception, get_retry_delay
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt == max_retries:
                        break
                    
                    # Check if exception is retryable
                    if not is_retryable_exception(e):
                        break
                    
                    # Calculate delay
                    delay = get_retry_delay(e, attempt + 1)
                    delay = min(delay, max_delay)
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # Re-raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def format_error_message(error: Exception) -> str:
    """
    Format error message for user-friendly display.
    
    Args:
        error: Exception to format
        
    Returns:
        Formatted error message
    """
    
    if hasattr(error, 'message'):
        return error.message
    
    return str(error)


def validate_project_id(project_id: str) -> bool:
    """
    Validate project ID format.
    
    Args:
        project_id: Project ID to validate
        
    Returns:
        True if valid project ID format
    """
    
    return validate_uuid(project_id)


def normalize_knowledge_type(knowledge_type: str) -> str:
    """
    Normalize knowledge type string.
    
    Args:
        knowledge_type: Knowledge type to normalize
        
    Returns:
        Normalized knowledge type
    """
    
    if not knowledge_type:
        return "document"
    
    # Convert to lowercase and replace spaces/underscores with hyphens
    normalized = knowledge_type.lower().strip()
    normalized = re.sub(r'[\s_]+', '-', normalized)
    
    # Remove special characters except hyphens
    normalized = re.sub(r'[^a-z0-9-]', '', normalized)
    
    return normalized or "document"