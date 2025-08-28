/**
 * BETTY Memory System TypeScript SDK
 * 
 * Official TypeScript/JavaScript client library for BETTY Memory System v2.0 API.
 * Provides complete access to advanced knowledge management capabilities including
 * semantic search, pattern matching, batch operations, and real-time features.
 * 
 * @example
 * ```typescript
 * import { BettyClient } from '@betty/memory-sdk';
 * 
 * const client = new BettyClient({
 *   apiKey: 'your-jwt-token',
 *   baseUrl: 'http://localhost:3034/api/v2'
 * });
 * 
 * const results = await client.advancedSearch({
 *   query: 'machine learning optimization',
 *   searchType: 'hybrid',
 *   maxResults: 20
 * });
 * ```
 */

export { BettyClient } from './client/BettyClient';
export { BettyConfig, BettyClientOptions } from './config/BettyConfig';

// Export all types
export * from './types';

// Export errors
export * from './errors';

// Export utilities
export * from './utils';

// Export version information
export const VERSION = '2.0.0';

/**
 * SDK version information
 */
export const SDK_INFO = {
  name: '@betty/memory-sdk',
  version: VERSION,
  description: 'Official TypeScript SDK for BETTY Memory System v2.0',
  author: 'BETTY Development Team',
  license: 'MIT'
} as const;