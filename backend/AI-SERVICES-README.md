# AI Services Documentation

This document provides comprehensive documentation for the AI Orchestrator and Code Quality Engine services in the Lineary backend.

## Table of Contents

1. [Overview](#overview)
2. [AI Orchestrator Service](#ai-orchestrator-service)
3. [Code Quality Engine Service](#code-quality-engine-service)
4. [API Endpoints](#api-endpoints)
5. [Setup and Configuration](#setup-and-configuration)
6. [Usage Examples](#usage-examples)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)

## Overview

The Lineary backend includes two powerful services for AI-powered development assistance:

- **AI Orchestrator**: Provides AI-powered code review, test generation, documentation, and prompt optimization
- **Code Quality Engine**: Runs comprehensive code quality checks including linting, security scanning, testing, and complexity analysis

Both services are production-ready, include comprehensive error handling, and integrate seamlessly with the existing database schema.

## AI Orchestrator Service

### Features

- **Code Review**: AI-powered code analysis with security, performance, and quality assessments
- **Test Generation**: Automatic generation of unit, integration, and end-to-end tests
- **Documentation Generation**: AI-generated API documentation, README files, and technical guides
- **Prompt Optimization**: Intelligent prompt enhancement for better AI interactions
- **Template Management**: Customizable AI prompt templates with success rate tracking

### Core Methods

#### Code Review
```typescript
async reviewCode(request: CodeReviewRequest): Promise<CodeReviewResult>
```

**Parameters:**
- `code`: The source code to review
- `language`: Programming language (javascript, typescript, python, etc.)
- `context`: Optional context about the code's purpose
- `files_changed`: Array of file paths that were modified
- `issue_id`: Optional issue ID for tracking

**Returns:**
- `overall_score`: Overall code quality score (0-100)
- `security_issues`: Array of security vulnerabilities found
- `performance_issues`: Array of performance concerns
- `code_quality_issues`: Array of code quality problems
- `best_practices`: Array of best practice recommendations
- `suggested_improvements`: Array of improvement suggestions
- `estimated_fix_time`: Estimated time to fix issues (hours)

#### Test Generation
```typescript
async generateTests(request: TestGenerationRequest): Promise<TestGenerationResult>
```

**Parameters:**
- `code`: Source code to generate tests for
- `language`: Programming language
- `framework`: Testing framework (jest, pytest, etc.)
- `test_type`: Type of tests ('unit', 'integration', 'e2e')
- `coverage_target`: Target code coverage percentage

**Returns:**
- `test_code`: Generated test code
- `test_file_name`: Suggested test file name
- `test_cases`: Array of test cases with descriptions
- `coverage_estimate`: Estimated code coverage
- `setup_requirements`: Required setup steps
- `dependencies`: Required test dependencies

#### Documentation Generation
```typescript
async generateDocumentation(request: DocumentationRequest): Promise<DocumentationResult>
```

**Parameters:**
- `code`: Source code to document
- `language`: Programming language
- `doc_type`: Documentation type ('api', 'readme', 'technical', 'user_guide')
- `existing_docs`: Optional existing documentation to enhance

**Returns:**
- `documentation`: Generated documentation content
- `format`: Documentation format (markdown, html, plain_text)
- `sections`: Structured documentation sections
- `examples`: Code examples included in documentation

#### Prompt Optimization
```typescript
async optimizePrompt(request: PromptOptimizationRequest): Promise<PromptOptimizationResult>
```

**Parameters:**
- `original_prompt`: The prompt to optimize
- `context`: Context for the prompt usage
- `target_model`: Target AI model ('gpt-4', 'gpt-3.5-turbo', 'claude-3', etc.)
- `optimization_goals`: Array of goals ('clarity', 'conciseness', 'specificity', 'token_efficiency')

**Returns:**
- `optimized_prompt`: Improved prompt
- `improvements`: Array of improvements made
- `token_reduction`: Estimated token reduction percentage
- `estimated_performance_gain`: Expected performance improvement

### Template Management

```typescript
// Get prompt templates
async getPromptTemplates(category?: string): Promise<AIPromptTemplate[]>

// Create new template
async createPromptTemplate(template: Omit<AIPromptTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<AIPromptTemplate>

// Update existing template
async updatePromptTemplate(id: string, updates: Partial<AIPromptTemplate>): Promise<AIPromptTemplate>
```

## Code Quality Engine Service

### Features

- **Linting**: ESLint integration for JavaScript/TypeScript, similar tools for other languages
- **Security Scanning**: Multiple security scanners (npm audit, bandit, semgrep)
- **Test Execution**: Automated test running with coverage analysis
- **Complexity Analysis**: Cyclomatic and cognitive complexity measurement
- **Code Formatting**: Prettier, Black, and other formatter integration
- **Type Checking**: TypeScript type checking and coverage analysis
- **Auto-fix**: Automatic fixing of linting issues and code formatting

### Core Methods

#### Quality Check
```typescript
async runQualityCheck(config: QualityCheckConfig): Promise<QualityReport>
```

**Configuration:**
- `project_path`: Path to the project directory
- `language`: Primary programming language
- `framework`: Optional framework specification
- `eslint_config`: ESLint configuration file path
- `prettier_config`: Prettier configuration file path
- `typescript_config`: TypeScript configuration file path
- `test_command`: Custom test command
- `exclude_patterns`: Patterns to exclude from analysis

**Returns:**
- `overall_score`: Overall quality score (0-100)
- `lint_results`: Linting results for each file
- `security_results`: Security scan results
- `test_results`: Test execution results with coverage
- `complexity_results`: Code complexity analysis
- `format_results`: Code formatting check results
- `type_check_results`: TypeScript type checking results
- `recommendations`: Prioritized improvement recommendations
- `metrics`: Detailed quality metrics

#### Auto-fix
```typescript
async autoFix(config: QualityCheckConfig, options: AutoFixOptions): Promise<AutoFixResult>
```

**Options:**
- `fix_lint_issues`: Automatically fix linting problems
- `format_code`: Format code using configured formatter
- `fix_imports`: Organize and fix import statements
- `update_dependencies`: Update outdated dependencies
- `apply_security_fixes`: Apply automatic security fixes

**Returns:**
- `fixes_applied`: Number of fixes applied
- `files_modified`: Array of modified file paths
- `fixes_summary`: Summary of fixes applied by category
- `remaining_issues`: Number of issues that require manual intervention

## API Endpoints

### Code Review
```
POST /api/ai/review
```

### Test Generation
```
POST /api/ai/generate-tests
```

### Documentation Generation
```
POST /api/ai/generate-docs
```

### Prompt Optimization
```
POST /api/ai/optimize-prompt
```

### Quality Check
```
POST /api/ai/quality-check
```

### Auto-fix
```
POST /api/ai/auto-fix
```

### Prompt Template Management
```
GET /api/ai/prompts?category=<category>
POST /api/ai/prompts
PUT /api/ai/prompts/:id
```

### Batch Processing
```
POST /api/ai/process-issues
```

### Health Check
```
GET /api/ai/health
```

## Setup and Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_linear

# Optional
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com
DEFAULT_AI_MODEL=gpt-4
MAX_TOKENS=4000
AI_TEMPERATURE=0.1
REDIS_URL=redis://localhost:6379
```

### Tool Dependencies

The Code Quality Engine requires various tools to be installed:

```bash
# Node.js tools
npm install -g eslint prettier typescript

# Python tools (if analyzing Python code)
pip install bandit black radon

# Security tools
npm install -g semgrep
```

### Database Setup

The services use the existing `ai_prompts` table and create quality metrics in the `quality_metrics` table:

```sql
-- AI Prompts table (already exists)
CREATE TABLE ai_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    prompt_template TEXT NOT NULL,
    variables JSONB,
    success_rate DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Metrics table (already exists)
CREATE TABLE quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID,
    metric_type VARCHAR(50) NOT NULL,
    value JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Basic Code Review

```typescript
const reviewResult = await aiOrchestrator.reviewCode({
  code: `
    function calculateTotal(items) {
      let total = 0;
      for (let i = 0; i < items.length; i++) {
        total += items[i].price * items[i].quantity;
      }
      return total;
    }
  `,
  language: 'javascript',
  context: 'E-commerce cart total calculation'
});

console.log('Overall Score:', reviewResult.overall_score);
console.log('Security Issues:', reviewResult.security_issues.length);
```

### Quality Check

```typescript
const qualityReport = await codeQuality.runQualityCheck({
  project_path: '/path/to/project',
  language: 'typescript',
  framework: 'react'
});

console.log('Overall Score:', qualityReport.overall_score);
console.log('Code Coverage:', qualityReport.metrics.code_coverage);
```

### API Usage

```bash
# Code Review
curl -X POST http://localhost:8000/api/ai/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function example() { return 42; }",
    "language": "javascript",
    "context": "Simple example function"
  }'

# Quality Check
curl -X POST http://localhost:8000/api/ai/quality-check \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "language": "typescript"
  }'
```

## Error Handling

Both services include comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **API Rate Limits**: Intelligent rate limiting and fallback strategies
- **Tool Availability**: Graceful degradation when optional tools aren't available
- **Invalid Input**: Clear validation error messages
- **Service Failures**: Fallback to alternative AI providers when configured

Example error response:
```json
{
  "success": false,
  "error": "Code review failed",
  "message": "OpenAI API rate limit exceeded. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

## Performance Considerations

### AI Orchestrator

- **Model Selection**: Choose appropriate models for different tasks (GPT-4 for complex analysis, GPT-3.5-turbo for simple tasks)
- **Token Management**: Automatic prompt optimization to reduce token usage
- **Caching**: Prompt template caching and result memoization
- **Batch Processing**: Support for processing multiple issues simultaneously

### Code Quality Engine

- **Tool Parallelization**: Run multiple quality checks concurrently
- **Incremental Analysis**: Only analyze changed files when possible
- **Resource Management**: Configurable timeouts and memory limits
- **Result Caching**: Cache results to avoid redundant analysis

### Database Performance

- **Connection Pooling**: Efficient database connection management
- **Indexed Queries**: Optimized queries for prompt templates and metrics
- **Batch Inserts**: Efficient bulk data operations
- **Query Optimization**: Minimal database round-trips

### Best Practices

1. **Configuration**: Use environment-specific configurations
2. **Monitoring**: Implement comprehensive logging and monitoring
3. **Rate Limiting**: Respect API rate limits and implement backoff strategies
4. **Error Recovery**: Implement retry logic with exponential backoff
5. **Resource Cleanup**: Properly clean up resources and connections
6. **Security**: Secure API keys and sensitive configuration
7. **Testing**: Comprehensive test coverage for all service methods

## Integration Examples

For complete integration examples, see the `examples/ai-services-usage.ts` file, which demonstrates:

- Service initialization
- All major features
- Error handling patterns
- API usage examples
- Environment setup guide

The services are designed to be production-ready and can handle high-volume usage with proper configuration and monitoring.