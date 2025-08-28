/**
 * BETTY Memory System TypeScript SDK - Error Classes
 * 
 * This module defines custom error classes for the BETTY TypeScript SDK,
 * providing detailed error information and proper inheritance.
 */

/**
 * Base error class for all BETTY SDK errors.
 */
export class BettyError extends Error {
  public readonly details: Record<string, any>;

  constructor(message: string, details: Record<string, any> = {}) {
    super(message);
    this.name = this.constructor.name;
    this.details = details;

    // Maintain proper stack trace (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert error to JSON representation.
   */
  toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      details: this.details,
      stack: this.stack
    };
  }

  /**
   * String representation of the error.
   */
  toString(): string {
    if (Object.keys(this.details).length > 0) {
      return `${this.name}: ${this.message} (Details: ${JSON.stringify(this.details)})`;
    }
    return `${this.name}: ${this.message}`;
  }
}

/**
 * Error for general API failures.
 */
export class BettyAPIError extends BettyError {
  public readonly statusCode?: number;
  public readonly requestId?: string;

  constructor(
    message: string,
    statusCode?: number,
    details: Record<string, any> = {},
    requestId?: string
  ) {
    super(message, details);
    this.statusCode = statusCode;
    this.requestId = requestId;
  }

  /**
   * Convert error to JSON representation.
   */
  toJSON(): Record<string, any> {
    return {
      ...super.toJSON(),
      statusCode: this.statusCode,
      requestId: this.requestId
    };
  }

  /**
   * String representation with status code and request ID.
   */
  toString(): string {
    const parts = [this.message];

    if (this.statusCode) {
      parts.push(`Status: ${this.statusCode}`);
    }

    if (this.requestId) {
      parts.push(`Request ID: ${this.requestId}`);
    }

    if (Object.keys(this.details).length > 0) {
      parts.push(`Details: ${JSON.stringify(this.details)}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for authentication failures.
 */
export class AuthenticationError extends BettyAPIError {
  constructor(
    message = 'Authentication failed',
    details: Record<string, any> = {},
    requestId?: string
  ) {
    super(message, 401, details, requestId);
  }
}

/**
 * Error for permission/authorization failures.
 */
export class PermissionError extends BettyAPIError {
  public readonly missingPermissions: string[];
  public readonly userPermissions: string[];

  constructor(
    message = 'Permission denied',
    missingPermissions: string[] = [],
    userPermissions: string[] = [],
    details: Record<string, any> = {},
    requestId?: string
  ) {
    super(
      message,
      403,
      {
        ...details,
        missing_permissions: missingPermissions,
        user_permissions: userPermissions
      },
      requestId
    );
    
    this.missingPermissions = missingPermissions;
    this.userPermissions = userPermissions;
  }

  /**
   * String representation with permission details.
   */
  toString(): string {
    const parts = [this.message];

    if (this.missingPermissions.length > 0) {
      parts.push(`Missing: ${this.missingPermissions.join(', ')}`);
    }

    if (this.userPermissions.length > 0) {
      parts.push(`Current: ${this.userPermissions.join(', ')}`);
    }

    if (this.requestId) {
      parts.push(`Request ID: ${this.requestId}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for rate limiting.
 */
export class RateLimitError extends BettyAPIError {
  public readonly retryAfter?: number;
  public readonly limitInfo: Record<string, any>;

  constructor(
    message = 'Rate limit exceeded',
    retryAfter?: number,
    limitInfo: Record<string, any> = {},
    details: Record<string, any> = {},
    requestId?: string
  ) {
    super(
      message,
      429,
      {
        ...details,
        retry_after: retryAfter,
        limit_info: limitInfo
      },
      requestId
    );
    
    this.retryAfter = retryAfter;
    this.limitInfo = limitInfo;
  }

  /**
   * String representation with rate limit details.
   */
  toString(): string {
    const parts = [this.message];

    if (this.retryAfter) {
      parts.push(`Retry after: ${this.retryAfter}s`);
    }

    if (this.limitInfo.requests_per_minute) {
      parts.push(`Limit: ${this.limitInfo.requests_per_minute}/min`);
    }

    if (this.limitInfo.current_usage) {
      parts.push(`Current: ${this.limitInfo.current_usage}`);
    }

    if (this.requestId) {
      parts.push(`Request ID: ${this.requestId}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for request validation failures.
 */
export class ValidationError extends BettyAPIError {
  public readonly fieldErrors: Record<string, string[]>;

  constructor(
    message = 'Request validation failed',
    fieldErrors: Record<string, string[]> = {},
    details: Record<string, any> = {},
    requestId?: string
  ) {
    super(
      message,
      422,
      {
        ...details,
        field_errors: fieldErrors
      },
      requestId
    );
    
    this.fieldErrors = fieldErrors;
  }

  /**
   * String representation with field error details.
   */
  toString(): string {
    const parts = [this.message];

    if (Object.keys(this.fieldErrors).length > 0) {
      const errorSummary = Object.entries(this.fieldErrors)
        .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
        .join('; ');
      parts.push(`Field errors: ${errorSummary}`);
    }

    if (this.requestId) {
      parts.push(`Request ID: ${this.requestId}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for request timeouts.
 */
export class TimeoutError extends BettyError {
  public readonly timeoutMs?: number;
  public readonly operation?: string;

  constructor(
    message = 'Request timeout',
    timeoutMs?: number,
    operation?: string
  ) {
    super(message, {
      timeout_ms: timeoutMs,
      operation
    });
    
    this.timeoutMs = timeoutMs;
    this.operation = operation;
  }

  /**
   * String representation with timeout details.
   */
  toString(): string {
    const parts = [this.message];

    if (this.operation) {
      parts.push(`Operation: ${this.operation}`);
    }

    if (this.timeoutMs) {
      parts.push(`Timeout: ${this.timeoutMs}ms`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for connection issues.
 */
export class ConnectionError extends BettyError {
  public readonly endpoint?: string;
  public readonly cause?: Error;

  constructor(
    message = 'Connection error',
    endpoint?: string,
    cause?: Error
  ) {
    super(message, {
      endpoint,
      cause: cause?.message
    });
    
    this.endpoint = endpoint;
    this.cause = cause;
  }

  /**
   * String representation with connection details.
   */
  toString(): string {
    const parts = [this.message];

    if (this.endpoint) {
      parts.push(`Endpoint: ${this.endpoint}`);
    }

    if (this.cause) {
      parts.push(`Cause: ${this.cause.message}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for WebSocket-related issues.
 */
export class WebSocketError extends BettyError {
  public readonly connectionState?: string;
  public readonly closeCode?: number;
  public readonly closeReason?: string;

  constructor(
    message = 'WebSocket error',
    connectionState?: string,
    closeCode?: number,
    closeReason?: string
  ) {
    super(message, {
      connection_state: connectionState,
      close_code: closeCode,
      close_reason: closeReason
    });
    
    this.connectionState = connectionState;
    this.closeCode = closeCode;
    this.closeReason = closeReason;
  }

  /**
   * String representation with WebSocket details.
   */
  toString(): string {
    const parts = [this.message];

    if (this.connectionState) {
      parts.push(`State: ${this.connectionState}`);
    }

    if (this.closeCode !== undefined) {
      parts.push(`Close code: ${this.closeCode}`);
    }

    if (this.closeReason) {
      parts.push(`Reason: ${this.closeReason}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Error for configuration issues.
 */
export class ConfigurationError extends BettyError {
  public readonly configField?: string;
  public readonly configValue?: any;

  constructor(
    message = 'Configuration error',
    configField?: string,
    configValue?: any
  ) {
    super(message, {
      config_field: configField,
      config_value: configValue
    });
    
    this.configField = configField;
    this.configValue = configValue;
  }

  /**
   * String representation with configuration details.
   */
  toString(): string {
    const parts = [this.message];

    if (this.configField) {
      parts.push(`Field: ${this.configField}`);
    }

    if (this.configValue !== undefined) {
      parts.push(`Value: ${this.configValue}`);
    }

    return `${this.name}: ${parts.join(' | ')}`;
  }
}

/**
 * Create appropriate API error from response data.
 */
export function createAPIErrorFromResponse(
  statusCode: number,
  responseData: any,
  requestId?: string
): BettyAPIError {
  const message = responseData?.message || 'API request failed';
  const details = responseData?.details || {};

  switch (statusCode) {
    case 401:
      return new AuthenticationError(message, details, requestId);

    case 403:
      return new PermissionError(
        message,
        details.missing_permissions || [],
        details.user_permissions || [],
        details,
        requestId
      );

    case 422:
      return new ValidationError(
        message,
        details.field_errors || {},
        details,
        requestId
      );

    case 429:
      return new RateLimitError(
        message,
        details.retry_after,
        details.limit_info || {},
        details,
        requestId
      );

    default:
      return new BettyAPIError(message, statusCode, details, requestId);
  }
}

/**
 * Check if error is retryable.
 */
export function isRetryableError(error: Error): boolean {
  // Retryable errors
  if (error instanceof TimeoutError || error instanceof ConnectionError) {
    return true;
  }

  // Server errors are retryable
  if (error instanceof BettyAPIError) {
    return error.statusCode ? error.statusCode >= 500 : false;
  }

  // Rate limits are retryable after delay
  if (error instanceof RateLimitError) {
    return true;
  }

  return false;
}

/**
 * Get retry delay for an error.
 */
export function getRetryDelay(error: Error, attempt: number): number {
  // Rate limit exceptions have specific retry delay
  if (error instanceof RateLimitError && error.retryAfter) {
    return error.retryAfter * 1000; // Convert to milliseconds
  }

  // Exponential backoff for other retryable errors
  const baseDelay = 1000; // 1 second
  const maxDelay = 60000; // 60 seconds
  const backoffFactor = 2;

  const delay = baseDelay * Math.pow(backoffFactor, attempt - 1);
  return Math.min(delay, maxDelay);
}

/**
 * Format error message for user-friendly display.
 */
export function formatErrorMessage(error: Error): string {
  if (error instanceof BettyError) {
    return error.message;
  }
  
  return error.message || 'Unknown error';
}

/**
 * Check if error indicates authentication failure.
 */
export function isAuthenticationError(error: Error): error is AuthenticationError {
  return error instanceof AuthenticationError;
}

/**
 * Check if error indicates permission failure.
 */
export function isPermissionError(error: Error): error is PermissionError {
  return error instanceof PermissionError;
}

/**
 * Check if error indicates rate limiting.
 */
export function isRateLimitError(error: Error): error is RateLimitError {
  return error instanceof RateLimitError;
}

/**
 * Check if error indicates validation failure.
 */
export function isValidationError(error: Error): error is ValidationError {
  return error instanceof ValidationError;
}