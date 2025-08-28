// ABOUTME: AI-powered routes for code review, test generation, and quality analysis
// ABOUTME: Provides REST endpoints for AI Orchestrator and Code Quality Engine services

import { Router, Request, Response } from 'express';
import { AIOrchestrator } from '../services/AIOrchestrator';
import { CodeQualityEngine } from '../services/CodeQualityEngine';
import { DatabaseService } from '../services/DatabaseService';

interface Context {
  db: DatabaseService;
  ai: AIOrchestrator;
  codeQuality: CodeQualityEngine;
}

export function aiRoutes(context: Context) {
  const router = Router();
  const { ai, codeQuality, db } = context;

  // Code Review Endpoints
  router.post('/review', async (req: Request, res: Response) => {
    try {
      const { code, language, context: reviewContext, files_changed, issue_id } = req.body;
      
      if (!code || !language) {
        return res.status(400).json({ 
          error: 'Missing required fields: code and language' 
        });
      }

      const result = await ai.reviewCode({
        code,
        language,
        context: reviewContext,
        files_changed,
        issue_id
      });

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('Code review failed:', error);
      res.status(500).json({
        error: 'Code review failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Test Generation Endpoints
  router.post('/generate-tests', async (req: Request, res: Response) => {
    try {
      const { code, language, framework, test_type = 'unit', coverage_target } = req.body;
      
      if (!code || !language) {
        return res.status(400).json({ 
          error: 'Missing required fields: code and language' 
        });
      }

      const result = await ai.generateTests({
        code,
        language,
        framework,
        test_type,
        coverage_target
      });

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('Test generation failed:', error);
      res.status(500).json({
        error: 'Test generation failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Documentation Generation Endpoints
  router.post('/generate-docs', async (req: Request, res: Response) => {
    try {
      const { code, language, doc_type = 'api', existing_docs } = req.body;
      
      if (!code || !language) {
        return res.status(400).json({ 
          error: 'Missing required fields: code and language' 
        });
      }

      const result = await ai.generateDocumentation({
        code,
        language,
        doc_type,
        existing_docs
      });

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('Documentation generation failed:', error);
      res.status(500).json({
        error: 'Documentation generation failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Prompt Optimization Endpoints
  router.post('/optimize-prompt', async (req: Request, res: Response) => {
    try {
      const { 
        original_prompt, 
        context: promptContext, 
        target_model = 'gpt-4', 
        optimization_goals = ['clarity', 'specificity'] 
      } = req.body;
      
      if (!original_prompt || !promptContext) {
        return res.status(400).json({ 
          error: 'Missing required fields: original_prompt and context' 
        });
      }

      const result = await ai.optimizePrompt({
        original_prompt,
        context: promptContext,
        target_model,
        optimization_goals
      });

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('Prompt optimization failed:', error);
      res.status(500).json({
        error: 'Prompt optimization failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Quality Check Endpoints
  router.post('/quality-check', async (req: Request, res: Response) => {
    try {
      const { 
        project_path, 
        language, 
        framework,
        eslint_config,
        prettier_config,
        typescript_config,
        test_command,
        exclude_patterns
      } = req.body;
      
      if (!project_path || !language) {
        return res.status(400).json({ 
          error: 'Missing required fields: project_path and language' 
        });
      }

      const result = await codeQuality.runQualityCheck({
        project_path,
        language,
        framework,
        eslint_config,
        prettier_config,
        typescript_config,
        test_command,
        exclude_patterns
      });

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('Quality check failed:', error);
      res.status(500).json({
        error: 'Quality check failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Auto-fix Endpoints
  router.post('/auto-fix', async (req: Request, res: Response) => {
    try {
      const { 
        project_path, 
        language,
        fix_lint_issues = true,
        format_code = true,
        fix_imports = true,
        update_dependencies = false,
        apply_security_fixes = false
      } = req.body;
      
      if (!project_path || !language) {
        return res.status(400).json({ 
          error: 'Missing required fields: project_path and language' 
        });
      }

      const config = { project_path, language };
      const options = {
        fix_lint_issues,
        format_code,
        fix_imports,
        update_dependencies,
        apply_security_fixes
      };

      const result = await codeQuality.autoFix(config, options);

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('Auto-fix failed:', error);
      res.status(500).json({
        error: 'Auto-fix failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Prompt Template Management
  router.get('/prompts', async (req: Request, res: Response) => {
    try {
      const { category } = req.query;
      const templates = await ai.getPromptTemplates(category as string);
      
      res.json({
        success: true,
        data: templates
      });
    } catch (error) {
      console.error('Failed to get prompt templates:', error);
      res.status(500).json({
        error: 'Failed to get prompt templates',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  router.post('/prompts', async (req: Request, res: Response) => {
    try {
      const template = await ai.createPromptTemplate(req.body);
      
      res.status(201).json({
        success: true,
        data: template
      });
    } catch (error) {
      console.error('Failed to create prompt template:', error);
      res.status(500).json({
        error: 'Failed to create prompt template',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  router.put('/prompts/:id', async (req: Request, res: Response) => {
    try {
      const { id } = req.params;
      const template = await ai.updatePromptTemplate(id, req.body);
      
      res.json({
        success: true,
        data: template
      });
    } catch (error) {
      console.error('Failed to update prompt template:', error);
      res.status(500).json({
        error: 'Failed to update prompt template',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Batch AI Operations for Issues
  router.post('/process-issues', async (req: Request, res: Response) => {
    try {
      const { issue_ids, operation, options = {} } = req.body;
      
      if (!issue_ids || !Array.isArray(issue_ids) || !operation) {
        return res.status(400).json({ 
          error: 'Missing required fields: issue_ids (array) and operation' 
        });
      }

      // Fetch issues from database
      const issues = [];
      for (const issueId of issue_ids) {
        const issue = await db.getIssueById(issueId);
        if (issue) {
          issues.push(issue);
        }
      }

      const results = await ai.processIssuesWithAI(issues, operation, options);

      res.json({
        success: true,
        data: results
      });
    } catch (error) {
      console.error('Batch AI processing failed:', error);
      res.status(500).json({
        error: 'Batch AI processing failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Health check for AI services
  router.get('/health', async (req: Request, res: Response) => {
    try {
      // Test basic functionality
      await ai.optimizePrompt({
        original_prompt: 'Test prompt',
        context: 'Health check',
        target_model: 'gpt-4',
        optimization_goals: ['clarity']
      });

      res.json({
        success: true,
        message: 'AI services are healthy',
        services: {
          ai_orchestrator: 'operational',
          code_quality_engine: 'operational'
        }
      });
    } catch (error) {
      res.status(503).json({
        success: false,
        message: 'AI services are unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  return router;
}