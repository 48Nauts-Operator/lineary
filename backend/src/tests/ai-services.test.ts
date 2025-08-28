// ABOUTME: Comprehensive tests for AI Orchestrator and Code Quality Engine services
// ABOUTME: Tests service initialization, core functionality, and error handling

import { Pool } from 'pg';
import { AIOrchestrator } from '../services/AIOrchestrator';
import { CodeQualityEngine } from '../services/CodeQualityEngine';

// Mock database pool for testing
const mockPool = {
  query: jest.fn(),
  connect: jest.fn(),
  end: jest.fn()
} as unknown as Pool;

// Mock OpenAI for testing
jest.mock('openai', () => {
  return {
    __esModule: true,
    default: jest.fn().mockImplementation(() => ({
      chat: {
        completions: {
          create: jest.fn().mockResolvedValue({
            choices: [{
              message: {
                content: JSON.stringify({
                  overall_score: 85,
                  security_issues: [],
                  performance_issues: [],
                  code_quality_issues: [],
                  best_practices: [],
                  suggested_improvements: ['Add type annotations'],
                  estimated_fix_time: 0.5
                })
              }
            }]
          })
        }
      }
    }))
  };
});

describe('AIOrchestrator Service', () => {
  let aiOrchestrator: AIOrchestrator;

  beforeEach(() => {
    jest.clearAllMocks();
    
    aiOrchestrator = new AIOrchestrator(mockPool, {
      openai_api_key: 'test-key',
      default_model: 'gpt-4',
      max_tokens: 4000,
      temperature: 0.1
    });

    // Mock database responses
    mockPool.query = jest.fn().mockImplementation((query, values) => {
      if (query.includes('SELECT * FROM ai_prompts')) {
        return Promise.resolve({
          rows: [{
            id: 'test-id',
            category: 'code_review',
            prompt_template: 'Review this {{language}} code: {{code}}',
            variables: { language: '', code: '' },
            success_rate: 85,
            usage_count: 10,
            created_at: new Date(),
            updated_at: new Date()
          }]
        });
      }
      
      if (query.includes('INSERT INTO ai_prompts')) {
        return Promise.resolve({
          rows: [{
            id: values[0],
            category: values[1],
            prompt_template: values[2],
            variables: JSON.parse(values[3]),
            success_rate: values[4],
            usage_count: values[5],
            created_at: new Date(),
            updated_at: new Date()
          }]
        });
      }
      
      if (query.includes('UPDATE ai_prompts')) {
        return Promise.resolve({ rows: [{}] });
      }
      
      return Promise.resolve({ rows: [] });
    });
  });

  describe('Service Initialization', () => {
    it('should initialize successfully', async () => {
      await expect(aiOrchestrator.initialize()).resolves.not.toThrow();
    });

    it('should load default prompts during initialization', async () => {
      await aiOrchestrator.initialize();
      
      // Should have attempted to create default prompts
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO ai_prompts'),
        expect.any(Array)
      );
    });
  });

  describe('Code Review', () => {
    beforeEach(async () => {
      await aiOrchestrator.initialize();
    });

    it('should perform code review successfully', async () => {
      const request = {
        code: 'function test() { return "hello"; }',
        language: 'javascript',
        context: 'Test function'
      };

      const result = await aiOrchestrator.reviewCode(request);

      expect(result).toHaveProperty('overall_score');
      expect(result).toHaveProperty('security_issues');
      expect(result).toHaveProperty('performance_issues');
      expect(result).toHaveProperty('suggested_improvements');
      expect(typeof result.overall_score).toBe('number');
      expect(Array.isArray(result.security_issues)).toBe(true);
    });

    it('should handle missing required fields', async () => {
      const request = {
        code: '',
        language: 'javascript'
      };

      // Should handle empty code gracefully
      await expect(aiOrchestrator.reviewCode(request)).rejects.toThrow();
    });

    it('should update prompt metrics after successful review', async () => {
      const request = {
        code: 'function test() { return "hello"; }',
        language: 'javascript'
      };

      await aiOrchestrator.reviewCode(request);

      // Should have updated prompt usage metrics
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE ai_prompts'),
        expect.arrayContaining([expect.any(String), true])
      );
    });
  });

  describe('Test Generation', () => {
    beforeEach(async () => {
      await aiOrchestrator.initialize();
    });

    it('should generate tests successfully', async () => {
      const request = {
        code: 'function add(a, b) { return a + b; }',
        language: 'javascript',
        framework: 'jest',
        test_type: 'unit' as const
      };

      // Mock test generation response
      const mockResponse = {
        choices: [{
          message: {
            content: JSON.stringify({
              test_code: 'describe("add", () => { it("should add numbers", () => { expect(add(1, 2)).toBe(3); }); });',
              test_file_name: 'add.test.js',
              test_cases: [{ name: 'should add numbers', description: 'Tests basic addition', type: 'happy_path' }],
              coverage_estimate: 100,
              setup_requirements: [],
              dependencies: ['jest']
            })
          }
        }]
      };

      (aiOrchestrator as any).openai.chat.completions.create.mockResolvedValueOnce(mockResponse);

      const result = await aiOrchestrator.generateTests(request);

      expect(result).toHaveProperty('test_code');
      expect(result).toHaveProperty('test_file_name');
      expect(result).toHaveProperty('test_cases');
      expect(Array.isArray(result.test_cases)).toBe(true);
    });
  });

  describe('Prompt Template Management', () => {
    beforeEach(async () => {
      await aiOrchestrator.initialize();
    });

    it('should get prompt template by category', async () => {
      const template = await aiOrchestrator.getPromptTemplate('code_review');

      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('category');
      expect(template).toHaveProperty('prompt_template');
      expect(template.category).toBe('code_review');
    });

    it('should create new prompt template', async () => {
      const newTemplate = {
        category: 'test_category',
        prompt_template: 'Test template {{variable}}',
        variables: { variable: '' },
        success_rate: 0,
        usage_count: 0
      };

      const result = await aiOrchestrator.createPromptTemplate(newTemplate);

      expect(result).toHaveProperty('id');
      expect(result.category).toBe('test_category');
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO ai_prompts'),
        expect.any(Array)
      );
    });

    it('should get all prompt templates', async () => {
      const templates = await aiOrchestrator.getPromptTemplates();

      expect(Array.isArray(templates)).toBe(true);
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('SELECT * FROM ai_prompts'),
        []
      );
    });
  });
});

describe('CodeQualityEngine Service', () => {
  let codeQuality: CodeQualityEngine;

  beforeEach(() => {
    jest.clearAllMocks();
    codeQuality = new CodeQualityEngine(mockPool);
  });

  describe('Service Initialization', () => {
    it('should initialize successfully', async () => {
      await expect(codeQuality.initialize()).resolves.not.toThrow();
    });

    it('should check tool availability during initialization', async () => {
      // Mock exec to simulate tool availability
      const mockExec = jest.fn().mockImplementation((command) => {
        if (command.includes('which eslint')) {
          return Promise.resolve({ stdout: '/usr/bin/eslint', stderr: '' });
        }
        if (command.includes('which prettier')) {
          return Promise.resolve({ stdout: '/usr/bin/prettier', stderr: '' });
        }
        return Promise.reject(new Error('Tool not found'));
      });

      jest.doMock('util', () => ({
        promisify: () => mockExec
      }));

      await codeQuality.initialize();

      // Should have checked for various tools
      expect(console.log).toHaveBeenCalledWith(expect.stringContaining('Code Quality Engine'));
    });
  });

  describe('Quality Check', () => {
    beforeEach(async () => {
      await codeQuality.initialize();
    });

    it('should run basic quality check', async () => {
      const config = {
        project_path: '/test/project',
        language: 'typescript',
        framework: 'react'
      };

      const result = await codeQuality.runQualityCheck(config);

      expect(result).toHaveProperty('overall_score');
      expect(result).toHaveProperty('metrics');
      expect(result).toHaveProperty('recommendations');
      expect(result).toHaveProperty('timestamp');
      expect(typeof result.overall_score).toBe('number');
      expect(result.overall_score).toBeGreaterThanOrEqual(0);
      expect(result.overall_score).toBeLessThanOrEqual(100);
    });

    it('should handle invalid project path gracefully', async () => {
      const config = {
        project_path: '/nonexistent/path',
        language: 'typescript'
      };

      const result = await codeQuality.runQualityCheck(config);

      // Should return a result even if some checks fail
      expect(result).toHaveProperty('overall_score');
      expect(result.overall_score).toBeGreaterThanOrEqual(0);
    });

    it('should generate appropriate recommendations', async () => {
      const config = {
        project_path: '/test/project',
        language: 'typescript'
      };

      const result = await codeQuality.runQualityCheck(config);

      expect(Array.isArray(result.recommendations)).toBe(true);
      result.recommendations.forEach(rec => {
        expect(rec).toHaveProperty('priority');
        expect(rec).toHaveProperty('category');
        expect(rec).toHaveProperty('description');
        expect(rec).toHaveProperty('action');
        expect(['high', 'medium', 'low']).toContain(rec.priority);
      });
    });
  });

  describe('Auto-fix', () => {
    beforeEach(async () => {
      await codeQuality.initialize();
    });

    it('should perform auto-fix operations', async () => {
      const config = {
        project_path: '/test/project',
        language: 'typescript'
      };

      const options = {
        fix_lint_issues: true,
        format_code: true,
        fix_imports: false,
        update_dependencies: false,
        apply_security_fixes: false
      };

      const result = await codeQuality.autoFix(config, options);

      expect(result).toHaveProperty('fixes_applied');
      expect(result).toHaveProperty('files_modified');
      expect(result).toHaveProperty('fixes_summary');
      expect(result).toHaveProperty('remaining_issues');
      expect(typeof result.fixes_applied).toBe('number');
      expect(Array.isArray(result.files_modified)).toBe(true);
    });

    it('should handle auto-fix failures gracefully', async () => {
      const config = {
        project_path: '/nonexistent/path',
        language: 'typescript'
      };

      const options = {
        fix_lint_issues: true,
        format_code: true,
        fix_imports: false,
        update_dependencies: false,
        apply_security_fixes: false
      };

      // Should not throw even if some fixes fail
      const result = await codeQuality.autoFix(config, options);
      expect(result).toHaveProperty('fixes_applied');
    });
  });

  describe('Metrics Calculation', () => {
    it('should calculate overall score correctly', async () => {
      const config = {
        project_path: '/test/project',
        language: 'typescript'
      };

      const result = await codeQuality.runQualityCheck(config);

      // Score should be between 0 and 100
      expect(result.overall_score).toBeGreaterThanOrEqual(0);
      expect(result.overall_score).toBeLessThanOrEqual(100);

      // Metrics should be properly structured
      expect(result.metrics).toHaveProperty('code_coverage');
      expect(result.metrics).toHaveProperty('technical_debt');
      expect(result.metrics).toHaveProperty('maintainability');
      expect(result.metrics).toHaveProperty('security_score');
      expect(result.metrics).toHaveProperty('complexity_score');
    });
  });
});

describe('Service Integration', () => {
  let aiOrchestrator: AIOrchestrator;
  let codeQuality: CodeQualityEngine;

  beforeEach(async () => {
    aiOrchestrator = new AIOrchestrator(mockPool, {
      openai_api_key: 'test-key',
      default_model: 'gpt-4'
    });

    codeQuality = new CodeQualityEngine(mockPool);

    // Mock database responses
    mockPool.query = jest.fn().mockResolvedValue({ rows: [] });

    await aiOrchestrator.initialize();
    await codeQuality.initialize();
  });

  it('should work together for comprehensive code analysis', async () => {
    const testCode = 'function test() { return "hello"; }';
    
    // Run quality check first
    const qualityResult = await codeQuality.runQualityCheck({
      project_path: '/test/project',
      language: 'javascript'
    });

    // Then run AI review
    const reviewResult = await aiOrchestrator.reviewCode({
      code: testCode,
      language: 'javascript',
      context: 'Test function for integration test'
    });

    expect(qualityResult).toHaveProperty('overall_score');
    expect(reviewResult).toHaveProperty('overall_score');
    
    // Both services should provide complementary insights
    expect(qualityResult.recommendations).toBeDefined();
    expect(reviewResult.suggested_improvements).toBeDefined();
  });

  it('should handle service failures independently', async () => {
    // Mock AI service failure
    (aiOrchestrator as any).openai.chat.completions.create.mockRejectedValueOnce(
      new Error('API unavailable')
    );

    // Quality check should still work
    const qualityResult = await codeQuality.runQualityCheck({
      project_path: '/test/project',
      language: 'javascript'
    });

    expect(qualityResult).toHaveProperty('overall_score');

    // AI review should fail gracefully
    await expect(aiOrchestrator.reviewCode({
      code: 'test',
      language: 'javascript'
    })).rejects.toThrow('API unavailable');
  });
});