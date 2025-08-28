/**
 * BETTY Memory System TypeScript SDK - Utilities
 * 
 * This module provides utility functions for the BETTY TypeScript SDK,
 * including JWT validation, filter formatting, and data processing.
 */

import { Filter } from '../types';
import { BettyError, ValidationError } from '../errors/BettyErrors';

/**
 * Validate JWT token format and extract basic information.
 * Note: This only validates format, not signature.
 */
export function validateJwtToken(token: string): {
  header: any;
  payload: any;
  valid: boolean;
  expiresAt?: Date;
  userId?: string;
  username?: string;
  permissions?: string[];
  role?: string;
} {
  if (!token || typeof token !== 'string') {
    throw new BettyError('API key must be a non-empty string');
  }

  // Split JWT into parts
  const parts = token.split('.');
  
  if (parts.length !== 3) {
    throw new BettyError('Invalid JWT format. Expected 3 parts separated by dots.');
  }

  try {
    // Decode header
    const headerData = parts[0] + '='.repeat((4 - parts[0].length % 4) % 4);
    const header = JSON.parse(atob(headerData.replace(/-/g, '+').replace(/_/g, '/')));

    // Decode payload
    const payloadData = parts[1] + '='.repeat((4 - parts[1].length % 4) % 4);
    const payload = JSON.parse(atob(payloadData.replace(/-/g, '+').replace(/_/g, '/')));

    // Validate required claims
    if (!payload.exp) {
      throw new BettyError("JWT token missing 'exp' (expiration) claim");
    }

    // Check if token is expired
    const expiresAt = new Date(payload.exp * 1000);
    const now = new Date();
    
    if (expiresAt < now) {
      throw new BettyError('JWT token has expired');
    }

    return {
      header,
      payload,
      valid: true,
      expiresAt,
      userId: payload.user_id,
      username: payload.username,
      permissions: payload.permissions || [],
      role: payload.role
    };

  } catch (error) {
    if (error instanceof BettyError) {
      throw error;
    }
    throw new BettyError(`Failed to validate JWT token: ${error.message}`);
  }
}

/**
 * Extract permissions from JWT token.
 */
export function extractPermissionsFromToken(token: string): string[] {
  try {
    const tokenData = validateJwtToken(token);
    return tokenData.permissions || [];
  } catch {
    return [];
  }
}

/**
 * Check if token contains a specific permission.
 */
export function checkPermission(token: string, requiredPermission: string): boolean {
  const permissions = extractPermissionsFromToken(token);
  return permissions.includes(requiredPermission);
}

/**
 * Format and validate filter conditions for API requests.
 */
export function formatFilters(filters: Filter[]): Filter[] {
  if (!filters || !Array.isArray(filters)) {
    return [];
  }

  const validOperators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'contains'];
  
  return filters.map((filter, index) => {
    // Validate required fields
    if (!filter.field || !filter.operator || filter.value === undefined) {
      throw new ValidationError(
        `Filter ${index} missing required fields`,
        { [`filters[${index}]`]: ['Must have field, operator, and value'] }
      );
    }

    // Validate operator
    if (!validOperators.includes(filter.operator)) {
      throw new ValidationError(
        `Invalid operator in filter ${index}`,
        { [`filters[${index}].operator`]: [`Must be one of: ${validOperators.join(', ')}`] }
      );
    }

    // Validate value for 'in' operator
    if (filter.operator === 'in' && !Array.isArray(filter.value)) {
      throw new ValidationError(
        `Filter ${index} with 'in' operator must have array value`,
        { [`filters[${index}].value`]: ["Must be an array when using 'in' operator"] }
      );
    }

    return {
      field: filter.field,
      operator: filter.operator,
      value: filter.value
    };
  });
}

/**
 * Merge multiple result sets using different strategies.
 */
export function mergeSearchResults<T extends { id?: string; similarity_score?: number; ranking_score?: number }>(
  resultSets: T[][],
  mergeStrategy: 'score' | 'round_robin' | 'weighted' = 'score',
  maxResults?: number
): T[] {
  if (!resultSets || resultSets.length === 0) {
    return [];
  }

  // Flatten all results and track source
  const allResults: (T & { _sourceSet?: number })[] = [];
  const seenIds = new Set<string>();

  for (let setIndex = 0; setIndex < resultSets.length; setIndex++) {
    for (const result of resultSets[setIndex]) {
      // Skip duplicates based on ID
      if (result.id && seenIds.has(result.id)) {
        continue;
      }

      // Add source information
      const resultWithSource = { ...result, _sourceSet: setIndex };
      allResults.push(resultWithSource);
      
      if (result.id) {
        seenIds.add(result.id);
      }
    }
  }

  // Apply merge strategy
  let mergedResults: (T & { _sourceSet?: number })[];

  if (mergeStrategy === 'score') {
    // Sort by similarity or ranking score (descending)
    mergedResults = allResults.sort((a, b) => {
      const scoreA = a.similarity_score ?? a.ranking_score ?? 0;
      const scoreB = b.similarity_score ?? b.ranking_score ?? 0;
      return scoreB - scoreA;
    });

  } else if (mergeStrategy === 'round_robin') {
    // Interleave results from different sets
    mergedResults = [];
    const maxSetLength = Math.max(...resultSets.map(set => set.length));
    const processedIds = new Set<string>();

    for (let i = 0; i < maxSetLength; i++) {
      for (let setIndex = 0; setIndex < resultSets.length; setIndex++) {
        const result = resultSets[setIndex][i];
        if (result && (!result.id || !processedIds.has(result.id))) {
          mergedResults.push({ ...result, _sourceSet: setIndex });
          if (result.id) {
            processedIds.add(result.id);
          }
        }
      }
    }

  } else if (mergeStrategy === 'weighted') {
    // Weight results based on source set index (earlier sets weighted higher)
    mergedResults = allResults.sort((a, b) => {
      const baseScoreA = a.similarity_score ?? a.ranking_score ?? 0;
      const baseScoreB = b.similarity_score ?? b.ranking_score ?? 0;
      
      const setWeightA = 1.0 - ((a._sourceSet ?? 0) * 0.1);
      const setWeightB = 1.0 - ((b._sourceSet ?? 0) * 0.1);
      
      const weightedScoreA = baseScoreA * setWeightA;
      const weightedScoreB = baseScoreB * setWeightB;
      
      return weightedScoreB - weightedScoreA;
    });

  } else {
    mergedResults = allResults;
  }

  // Remove internal fields and limit results
  const cleanResults = mergedResults.map(result => {
    const { _sourceSet, ...cleanResult } = result;
    return cleanResult as T;
  });

  return maxResults && maxResults > 0 
    ? cleanResults.slice(0, maxResults)
    : cleanResults;
}

/**
 * Sanitize search query by removing potentially harmful content.
 */
export function sanitizeQuery(query: string): string {
  if (!query || typeof query !== 'string') {
    return '';
  }

  // Remove excessive whitespace
  let sanitized = query.replace(/\s+/g, ' ').trim();

  // Remove potential script injection patterns
  const dangerousPatterns = [
    /<script[^>]*>/gi,
    /<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /;\s*DROP\s+TABLE/gi,
    /;\s*DELETE\s+FROM/gi,
    /;\s*INSERT\s+INTO/gi,
    /;\s*UPDATE\s+/gi,
    /UNION\s+SELECT/gi
  ];

  for (const pattern of dangerousPatterns) {
    sanitized = sanitized.replace(pattern, '');
  }

  // Limit query length
  const MAX_QUERY_LENGTH = 1000;
  if (sanitized.length > MAX_QUERY_LENGTH) {
    sanitized = sanitized.slice(0, MAX_QUERY_LENGTH);
  }

  return sanitized;
}

/**
 * Validate UUID format.
 */
export function validateUuid(uuidString: string): boolean {
  if (!uuidString || typeof uuidString !== 'string') {
    return false;
  }

  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidPattern.test(uuidString);
}

/**
 * Generate a unique request ID for tracking.
 */
export function generateRequestId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substr(2, 9);
  return `betty-${timestamp}-${random}`;
}

/**
 * Format datetime for API requests.
 */
export function formatDateTime(date: Date): string {
  return date.toISOString();
}

/**
 * Parse datetime string from API responses.
 */
export function parseDateTime(dateString: string): Date {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    throw new BettyError(`Invalid datetime format: ${dateString}`);
  }
  return date;
}

/**
 * Calculate basic text similarity score using Jaccard similarity.
 */
export function calculateSimilarity(text1: string, text2: string): number {
  if (!text1 || !text2) {
    return 0;
  }

  const words1 = new Set(text1.toLowerCase().split(/\s+/));
  const words2 = new Set(text2.toLowerCase().split(/\s+/));

  const intersection = new Set([...words1].filter(x => words2.has(x)));
  const union = new Set([...words1, ...words2]);

  return union.size === 0 ? 0 : intersection.size / union.size;
}

/**
 * Extract keywords from text using simple heuristics.
 */
export function extractKeywords(text: string, maxKeywords = 10): string[] {
  if (!text) {
    return [];
  }

  const words = text.toLowerCase().match(/\b\w+\b/g) || [];

  // Common stop words
  const stopWords = new Set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
    'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
    'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
  ]);

  // Filter and count words
  const wordCounts = new Map<string, number>();
  
  for (const word of words) {
    if (word.length > 2 && !stopWords.has(word)) {
      wordCounts.set(word, (wordCounts.get(word) || 0) + 1);
    }
  }

  // Sort by frequency and return top keywords
  return Array.from(wordCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxKeywords)
    .map(([word]) => word);
}

/**
 * Split array into chunks of specified size.
 */
export function chunkArray<T>(array: T[], chunkSize: number): T[][] {
  if (chunkSize <= 0) {
    throw new Error('Chunk size must be positive');
  }

  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize));
  }
  return chunks;
}

/**
 * Deep merge two objects.
 */
export function deepMerge<T extends Record<string, any>>(obj1: T, obj2: Partial<T>): T {
  const result = { ...obj1 };

  for (const [key, value] of Object.entries(obj2)) {
    if (value !== undefined) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value) &&
          typeof result[key] === 'object' && result[key] !== null && !Array.isArray(result[key])) {
        result[key] = deepMerge(result[key], value);
      } else {
        result[key] = value;
      }
    }
  }

  return result;
}

/**
 * Mask sensitive fields in object for logging.
 */
export function maskSensitiveData(
  data: Record<string, any>,
  sensitiveFields: string[] = ['apiKey', 'token', 'password', 'secret', 'key']
): Record<string, any> {
  const masked: Record<string, any> = {};

  for (const [key, value] of Object.entries(data)) {
    const keyLower = key.toLowerCase();
    const isSensitive = sensitiveFields.some(field => keyLower.includes(field.toLowerCase()));

    if (isSensitive && typeof value === 'string' && value.length > 8) {
      masked[key] = `${value.slice(0, 4)}...${value.slice(-4)}`;
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      masked[key] = maskSensitiveData(value, sensitiveFields);
    } else {
      masked[key] = value;
    }
  }

  return masked;
}

/**
 * Debounce function calls.
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): T & { cancel: () => void } {
  let timeoutId: NodeJS.Timeout | number | undefined;

  const debounced = ((...args: Parameters<T>) => {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId as any);
    }
    
    timeoutId = setTimeout(() => {
      func(...args);
    }, wait);
  }) as T & { cancel: () => void };

  debounced.cancel = () => {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId as any);
    }
  };

  return debounced;
}

/**
 * Throttle function calls.
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): T & { cancel: () => void } {
  let timeoutId: NodeJS.Timeout | number | undefined;
  let lastExecTime = 0;

  const throttled = ((...args: Parameters<T>) => {
    const currentTime = Date.now();
    
    if (currentTime - lastExecTime >= wait) {
      func(...args);
      lastExecTime = currentTime;
    } else if (timeoutId === undefined) {
      timeoutId = setTimeout(() => {
        func(...args);
        lastExecTime = Date.now();
        timeoutId = undefined;
      }, wait - (currentTime - lastExecTime));
    }
  }) as T & { cancel: () => void };

  throttled.cancel = () => {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId as any);
    }
  };

  return throttled;
}

/**
 * Format error message for user-friendly display.
 */
export function formatErrorMessage(error: Error): string {
  if (error instanceof BettyError) {
    return error.message;
  }
  return error.message || 'Unknown error occurred';
}

/**
 * Check if code is running in browser environment.
 */
export function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.document !== 'undefined';
}

/**
 * Check if code is running in Node.js environment.
 */
export function isNode(): boolean {
  return typeof process !== 'undefined' && process.versions && process.versions.node !== undefined;
}

/**
 * Sleep for specified milliseconds.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a retry wrapper for async functions.
 */
export function withRetry<T extends (...args: any[]) => Promise<any>>(
  func: T,
  maxRetries = 3,
  delayMs = 1000
): T {
  return (async (...args: Parameters<T>): Promise<Awaited<ReturnType<T>>> => {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
      try {
        return await func(...args);
      } catch (error) {
        lastError = error as Error;
        
        if (attempt > maxRetries) {
          break;
        }
        
        await sleep(delayMs * attempt);
      }
    }
    
    throw lastError!;
  }) as T;
}