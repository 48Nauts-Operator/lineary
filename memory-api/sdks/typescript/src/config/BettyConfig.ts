/**
 * BETTY Memory System TypeScript SDK - Configuration
 * 
 * This module provides configuration management for the BETTY TypeScript SDK,
 * including environment-based configuration and validation.
 */

/**
 * Configuration options for BETTY client.
 */
export interface BettyClientOptions {
  /** JWT token for authentication */
  apiKey?: string;
  
  /** Base URL for BETTY API */
  baseUrl?: string;
  
  /** Request timeout in seconds */
  timeout?: number;
  
  /** Maximum retry attempts */
  maxRetries?: number;
  
  /** Base retry delay in seconds */
  retryDelay?: number;
  
  /** Retry backoff factor */
  retryBackoffFactor?: number;
  
  /** Maximum retry delay in seconds */
  maxRetryDelay?: number;
  
  /** Enable request logging */
  logRequests?: boolean;
  
  /** Enable response caching */
  enableCaching?: boolean;
  
  /** Cache TTL in seconds */
  cacheTtl?: number;
  
  /** Enable request deduplication */
  enableRequestDeduplication?: boolean;
  
  /** Custom headers to include in requests */
  customHeaders?: Record<string, string>;
  
  /** Validate SSL certificates */
  validateSsl?: boolean;
  
  /** User agent string */
  userAgent?: string;
}

/**
 * Configuration class for BETTY client with validation and defaults.
 */
export class BettyConfig {
  public readonly apiKey?: string;
  public readonly baseUrl: string;
  public readonly timeout: number;
  public readonly maxRetries: number;
  public readonly retryDelay: number;
  public readonly retryBackoffFactor: number;
  public readonly maxRetryDelay: number;
  public readonly logRequests: boolean;
  public readonly enableCaching: boolean;
  public readonly cacheTtl: number;
  public readonly enableRequestDeduplication: boolean;
  public readonly customHeaders: Record<string, string>;
  public readonly validateSsl: boolean;
  public readonly userAgent: string;

  /**
   * Create configuration with validation.
   * 
   * @param options - Configuration options
   */
  constructor(options: BettyClientOptions = {}) {
    // Apply defaults and validate
    this.apiKey = options.apiKey || this.getEnvValue('BETTY_API_KEY');
    this.baseUrl = options.baseUrl || this.getEnvValue('BETTY_BASE_URL') || 'http://localhost:3034/api/v2';
    this.timeout = this.parseNumber(options.timeout || this.getEnvValue('BETTY_TIMEOUT'), 30);
    this.maxRetries = this.parseNumber(options.maxRetries || this.getEnvValue('BETTY_MAX_RETRIES'), 3);
    this.retryDelay = this.parseNumber(options.retryDelay || this.getEnvValue('BETTY_RETRY_DELAY'), 1);
    this.retryBackoffFactor = this.parseNumber(options.retryBackoffFactor || this.getEnvValue('BETTY_RETRY_BACKOFF_FACTOR'), 2);
    this.maxRetryDelay = this.parseNumber(options.maxRetryDelay || this.getEnvValue('BETTY_MAX_RETRY_DELAY'), 60);
    this.logRequests = this.parseBoolean(options.logRequests ?? this.getEnvValue('BETTY_LOG_REQUESTS'), false);
    this.enableCaching = this.parseBoolean(options.enableCaching ?? this.getEnvValue('BETTY_ENABLE_CACHING'), true);
    this.cacheTtl = this.parseNumber(options.cacheTtl || this.getEnvValue('BETTY_CACHE_TTL'), 300);
    this.enableRequestDeduplication = this.parseBoolean(
      options.enableRequestDeduplication ?? this.getEnvValue('BETTY_ENABLE_DEDUPLICATION'), 
      true
    );
    this.customHeaders = options.customHeaders || {};
    this.validateSsl = this.parseBoolean(options.validateSsl ?? this.getEnvValue('BETTY_VALIDATE_SSL'), true);
    this.userAgent = options.userAgent || 'betty-typescript-sdk/2.0.0';

    this.validate();
  }

  /**
   * Get environment variable value.
   */
  private getEnvValue(key: string): string | undefined {
    // Check if we're in Node.js environment
    if (typeof process !== 'undefined' && process.env) {
      return process.env[key];
    }
    return undefined;
  }

  /**
   * Parse number from string or number.
   */
  private parseNumber(value: any, defaultValue: number): number {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = parseInt(value, 10);
      return isNaN(parsed) ? defaultValue : parsed;
    }
    return defaultValue;
  }

  /**
   * Parse boolean from string or boolean.
   */
  private parseBoolean(value: any, defaultValue: boolean): boolean {
    if (typeof value === 'boolean') return value;
    if (typeof value === 'string') {
      return value.toLowerCase() === 'true';
    }
    return defaultValue;
  }

  /**
   * Validate configuration values.
   */
  private validate(): void {
    // Validate timeout
    if (this.timeout <= 0) {
      throw new Error('Timeout must be positive');
    }

    // Validate retry configuration
    if (this.maxRetries < 0) {
      throw new Error('Max retries cannot be negative');
    }

    if (this.retryDelay <= 0) {
      throw new Error('Retry delay must be positive');
    }

    if (this.retryBackoffFactor < 1) {
      throw new Error('Retry backoff factor must be >= 1');
    }

    if (this.maxRetryDelay <= 0) {
      throw new Error('Max retry delay must be positive');
    }

    // Validate cache TTL
    if (this.cacheTtl <= 0) {
      throw new Error('Cache TTL must be positive');
    }

    // Validate base URL format
    if (!this.baseUrl.startsWith('http://') && !this.baseUrl.startsWith('https://')) {
      throw new Error('Base URL must start with http:// or https://');
    }
  }

  /**
   * Create configuration from environment variables.
   */
  static fromEnvironment(prefix = 'BETTY_'): BettyConfig {
    const getEnvVar = (suffix: string) => {
      if (typeof process === 'undefined' || !process.env) {
        return undefined;
      }
      return process.env[`${prefix}${suffix}`];
    };

    return new BettyConfig({
      apiKey: getEnvVar('API_KEY'),
      baseUrl: getEnvVar('BASE_URL'),
      timeout: getEnvVar('TIMEOUT') ? parseInt(getEnvVar('TIMEOUT')!, 10) : undefined,
      maxRetries: getEnvVar('MAX_RETRIES') ? parseInt(getEnvVar('MAX_RETRIES')!, 10) : undefined,
      retryDelay: getEnvVar('RETRY_DELAY') ? parseFloat(getEnvVar('RETRY_DELAY')!) : undefined,
      retryBackoffFactor: getEnvVar('RETRY_BACKOFF_FACTOR') ? parseFloat(getEnvVar('RETRY_BACKOFF_FACTOR')!) : undefined,
      maxRetryDelay: getEnvVar('MAX_RETRY_DELAY') ? parseInt(getEnvVar('MAX_RETRY_DELAY')!, 10) : undefined,
      logRequests: getEnvVar('LOG_REQUESTS')?.toLowerCase() === 'true',
      enableCaching: getEnvVar('ENABLE_CACHING')?.toLowerCase() === 'true',
      cacheTtl: getEnvVar('CACHE_TTL') ? parseInt(getEnvVar('CACHE_TTL')!, 10) : undefined,
      enableRequestDeduplication: getEnvVar('ENABLE_DEDUPLICATION')?.toLowerCase() === 'true',
      validateSsl: getEnvVar('VALIDATE_SSL')?.toLowerCase() === 'true'
    });
  }

  /**
   * Create configuration from object.
   */
  static fromObject(obj: Record<string, any>): BettyConfig {
    return new BettyConfig({
      apiKey: obj.apiKey || obj.api_key,
      baseUrl: obj.baseUrl || obj.base_url,
      timeout: obj.timeout,
      maxRetries: obj.maxRetries || obj.max_retries,
      retryDelay: obj.retryDelay || obj.retry_delay,
      retryBackoffFactor: obj.retryBackoffFactor || obj.retry_backoff_factor,
      maxRetryDelay: obj.maxRetryDelay || obj.max_retry_delay,
      logRequests: obj.logRequests || obj.log_requests,
      enableCaching: obj.enableCaching || obj.enable_caching,
      cacheTtl: obj.cacheTtl || obj.cache_ttl,
      enableRequestDeduplication: obj.enableRequestDeduplication || obj.enable_request_deduplication,
      customHeaders: obj.customHeaders || obj.custom_headers,
      validateSsl: obj.validateSsl || obj.validate_ssl,
      userAgent: obj.userAgent || obj.user_agent
    });
  }

  /**
   * Create a copy of configuration with overrides.
   */
  copy(overrides: Partial<BettyClientOptions> = {}): BettyConfig {
    return new BettyConfig({
      apiKey: overrides.apiKey ?? this.apiKey,
      baseUrl: overrides.baseUrl ?? this.baseUrl,
      timeout: overrides.timeout ?? this.timeout,
      maxRetries: overrides.maxRetries ?? this.maxRetries,
      retryDelay: overrides.retryDelay ?? this.retryDelay,
      retryBackoffFactor: overrides.retryBackoffFactor ?? this.retryBackoffFactor,
      maxRetryDelay: overrides.maxRetryDelay ?? this.maxRetryDelay,
      logRequests: overrides.logRequests ?? this.logRequests,
      enableCaching: overrides.enableCaching ?? this.enableCaching,
      cacheTtl: overrides.cacheTtl ?? this.cacheTtl,
      enableRequestDeduplication: overrides.enableRequestDeduplication ?? this.enableRequestDeduplication,
      customHeaders: { ...this.customHeaders, ...overrides.customHeaders },
      validateSsl: overrides.validateSsl ?? this.validateSsl,
      userAgent: overrides.userAgent ?? this.userAgent
    });
  }

  /**
   * Convert configuration to plain object.
   */
  toObject(): BettyClientOptions {
    return {
      apiKey: this.apiKey,
      baseUrl: this.baseUrl,
      timeout: this.timeout,
      maxRetries: this.maxRetries,
      retryDelay: this.retryDelay,
      retryBackoffFactor: this.retryBackoffFactor,
      maxRetryDelay: this.maxRetryDelay,
      logRequests: this.logRequests,
      enableCaching: this.enableCaching,
      cacheTtl: this.cacheTtl,
      enableRequestDeduplication: this.enableRequestDeduplication,
      customHeaders: { ...this.customHeaders },
      validateSsl: this.validateSsl,
      userAgent: this.userAgent
    };
  }

  /**
   * Convert configuration to safe object (without sensitive data).
   */
  toSafeObject(): Record<string, any> {
    const obj = this.toObject();
    
    // Mask API key
    if (obj.apiKey) {
      obj.apiKey = `${obj.apiKey.slice(0, 10)}...${obj.apiKey.slice(-4)}`;
    }
    
    return obj;
  }

  /**
   * Convert configuration to JSON string.
   */
  toJSON(): string {
    return JSON.stringify(this.toSafeObject(), null, 2);
  }

  /**
   * String representation of configuration.
   */
  toString(): string {
    return `BettyConfig(${this.toJSON()})`;
  }
}

/**
 * Default configuration instance.
 */
export const defaultConfig = new BettyConfig();

/**
 * Create configuration with smart defaults.
 * Tries environment variables first, then falls back to defaults.
 */
export function createConfig(options: BettyClientOptions = {}): BettyConfig {
  try {
    // Try to merge environment config with provided options
    const envConfig = BettyConfig.fromEnvironment();
    return new BettyConfig({
      ...envConfig.toObject(),
      ...options
    });
  } catch {
    // Fall back to just the provided options
    return new BettyConfig(options);
  }
}