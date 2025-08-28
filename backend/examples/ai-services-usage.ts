// ABOUTME: Example usage of AI Orchestrator and Code Quality Engine services
// ABOUTME: Demonstrates how to integrate AI-powered features into the Lineary application

import { Pool } from 'pg';
import { AIOrchestrator } from '../src/services/AIOrchestrator';
import { CodeQualityEngine } from '../src/services/CodeQualityEngine';

// Example code to analyze
const exampleCode = `
function calculateTotal(items: Item[]): number {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price * items[i].quantity;
  }
  return total;
}

interface Item {
  id: string;
  name: string;
  price: number;
  quantity: number;
}
`;

async function demonstrateAIServices() {
  // Initialize database connection
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL || 'postgresql://localhost:5432/ai_linear'
  });

  // Initialize services
  const aiOrchestrator = new AIOrchestrator(pool, {
    openai_api_key: process.env.OPENAI_API_KEY || 'your-api-key',
    default_model: 'gpt-4',
    max_tokens: 4000,
    temperature: 0.1
  });

  const codeQuality = new CodeQualityEngine(pool);

  await aiOrchestrator.initialize();
  await codeQuality.initialize();

  console.log('🤖 AI Services Demo Started\n');

  // 1. Code Review Example
  console.log('📝 1. Code Review Example');
  console.log('='.repeat(50));
  
  try {
    const reviewResult = await aiOrchestrator.reviewCode({
      code: exampleCode,
      language: 'typescript',
      context: 'E-commerce total calculation function',
      files_changed: ['src/utils/cart.ts']
    });

    console.log('Review Score:', reviewResult.overall_score);
    console.log('Security Issues:', reviewResult.security_issues.length);
    console.log('Performance Issues:', reviewResult.performance_issues.length);
    console.log('Suggested Improvements:');
    reviewResult.suggested_improvements.forEach((improvement, i) => {
      console.log(`  ${i + 1}. ${improvement}`);
    });
  } catch (error) {
    console.error('Code review failed:', error.message);
  }

  console.log('\n');

  // 2. Test Generation Example
  console.log('🧪 2. Test Generation Example');
  console.log('='.repeat(50));
  
  try {
    const testResult = await aiOrchestrator.generateTests({
      code: exampleCode,
      language: 'typescript',
      framework: 'jest',
      test_type: 'unit',
      coverage_target: 90
    });

    console.log('Test File:', testResult.test_file_name);
    console.log('Test Cases Generated:', testResult.test_cases.length);
    console.log('Estimated Coverage:', testResult.coverage_estimate + '%');
    console.log('Test Cases:');
    testResult.test_cases.forEach((testCase, i) => {
      console.log(`  ${i + 1}. ${testCase.name} (${testCase.type})`);
    });
  } catch (error) {
    console.error('Test generation failed:', error.message);
  }

  console.log('\n');

  // 3. Documentation Generation Example
  console.log('📚 3. Documentation Generation Example');
  console.log('='.repeat(50));
  
  try {
    const docsResult = await aiOrchestrator.generateDocumentation({
      code: exampleCode,
      language: 'typescript',
      doc_type: 'api'
    });

    console.log('Documentation Format:', docsResult.format);
    console.log('Sections Generated:', docsResult.sections.length);
    console.log('Examples Included:', docsResult.examples.length);
    console.log('Documentation Preview:');
    console.log(docsResult.documentation.substring(0, 200) + '...');
  } catch (error) {
    console.error('Documentation generation failed:', error.message);
  }

  console.log('\n');

  // 4. Prompt Optimization Example
  console.log('⚡ 4. Prompt Optimization Example');
  console.log('='.repeat(50));
  
  try {
    const originalPrompt = 'Please review this code and tell me what you think about it and if there are any issues';
    const optimizedResult = await aiOrchestrator.optimizePrompt({
      original_prompt: originalPrompt,
      context: 'Code review for TypeScript e-commerce functions',
      target_model: 'gpt-4',
      optimization_goals: ['clarity', 'specificity', 'token_efficiency']
    });

    console.log('Original Prompt:', originalPrompt);
    console.log('Optimized Prompt:', optimizedResult.optimized_prompt);
    console.log('Token Reduction:', optimizedResult.token_reduction + '%');
    console.log('Performance Gain:', optimizedResult.estimated_performance_gain + '%');
  } catch (error) {
    console.error('Prompt optimization failed:', error.message);
  }

  console.log('\n');

  // 5. Code Quality Check Example
  console.log('🔍 5. Code Quality Check Example');
  console.log('='.repeat(50));
  
  try {
    const qualityResult = await codeQuality.runQualityCheck({
      project_path: '/path/to/your/project',
      language: 'typescript',
      framework: 'react',
      eslint_config: '.eslintrc.js',
      prettier_config: '.prettierrc',
      typescript_config: 'tsconfig.json'
    });

    console.log('Overall Score:', qualityResult.overall_score);
    console.log('Code Coverage:', qualityResult.metrics.code_coverage + '%');
    console.log('Security Score:', qualityResult.metrics.security_score);
    console.log('Technical Debt:', qualityResult.metrics.technical_debt + ' hours');
    console.log('Recommendations:', qualityResult.recommendations.length);
    
    qualityResult.recommendations.forEach((rec, i) => {
      console.log(`  ${i + 1}. [${rec.priority.toUpperCase()}] ${rec.description}`);
    });
  } catch (error) {
    console.error('Quality check failed:', error.message);
  }

  console.log('\n');

  // 6. Auto-fix Example
  console.log('🔧 6. Auto-fix Example');
  console.log('='.repeat(50));
  
  try {
    const autoFixResult = await codeQuality.autoFix(
      {
        project_path: '/path/to/your/project',
        language: 'typescript'
      },
      {
        fix_lint_issues: true,
        format_code: true,
        fix_imports: true,
        update_dependencies: false,
        apply_security_fixes: false
      }
    );

    console.log('Fixes Applied:', autoFixResult.fixes_applied);
    console.log('Files Modified:', autoFixResult.files_modified.length);
    console.log('Remaining Issues:', autoFixResult.remaining_issues);
    console.log('Fix Summary:');
    autoFixResult.fixes_summary.forEach((fix, i) => {
      console.log(`  ${i + 1}. ${fix.type}: ${fix.description}`);
    });
  } catch (error) {
    console.error('Auto-fix failed:', error.message);
  }

  console.log('\n');

  // 7. Prompt Template Management Example
  console.log('📋 7. Prompt Template Management Example');
  console.log('='.repeat(50));
  
  try {
    // Create a custom prompt template
    const newTemplate = await aiOrchestrator.createPromptTemplate({
      category: 'custom_review',
      prompt_template: `Review the following {{language}} code for {{focus_area}}:

Code:
\`\`\`{{language}}
{{code}}
\`\`\`

Please focus specifically on {{focus_area}} and provide detailed feedback.`,
      variables: { language: '', code: '', focus_area: '' },
      success_rate: 0,
      usage_count: 0
    });

    console.log('Created Template ID:', newTemplate.id);
    console.log('Template Category:', newTemplate.category);

    // Get all templates
    const templates = await aiOrchestrator.getPromptTemplates();
    console.log('Total Templates:', templates.length);
    
    // Get templates by category
    const reviewTemplates = await aiOrchestrator.getPromptTemplates('code_review');
    console.log('Code Review Templates:', reviewTemplates.length);
  } catch (error) {
    console.error('Template management failed:', error.message);
  }

  console.log('\n🎉 AI Services Demo Completed!');
  
  // Clean up
  await pool.end();
}

// API Usage Examples
function demonstrateAPIUsage() {
  console.log('🌐 API Usage Examples');
  console.log('='.repeat(50));

  console.log('1. Code Review API:');
  console.log(`
POST /api/ai/review
Content-Type: application/json

{
  "code": "function example() { return 'hello'; }",
  "language": "javascript",
  "context": "Simple greeting function",
  "issue_id": "123e4567-e89b-12d3-a456-426614174000"
}
  `);

  console.log('2. Test Generation API:');
  console.log(`
POST /api/ai/generate-tests
Content-Type: application/json

{
  "code": "function add(a, b) { return a + b; }",
  "language": "javascript",
  "framework": "jest",
  "test_type": "unit",
  "coverage_target": 95
}
  `);

  console.log('3. Quality Check API:');
  console.log(`
POST /api/ai/quality-check
Content-Type: application/json

{
  "project_path": "/path/to/project",
  "language": "typescript",
  "framework": "react",
  "eslint_config": ".eslintrc.js"
}
  `);

  console.log('4. Auto-fix API:');
  console.log(`
POST /api/ai/auto-fix
Content-Type: application/json

{
  "project_path": "/path/to/project",
  "language": "typescript",
  "fix_lint_issues": true,
  "format_code": true,
  "fix_imports": true
}
  `);

  console.log('5. Batch Processing API:');
  console.log(`
POST /api/ai/process-issues
Content-Type: application/json

{
  "issue_ids": ["123e4567-e89b-12d3-a456-426614174000"],
  "operation": "review",
  "options": {
    "auto_assign_reviewers": true
  }
}
  `);
}

// Environment Setup Guide
function showEnvironmentSetup() {
  console.log('⚙️  Environment Setup Guide');
  console.log('='.repeat(50));

  console.log(`
Required Environment Variables:

# AI Services
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key (optional)
ANTHROPIC_BASE_URL=https://api.anthropic.com (optional)
DEFAULT_AI_MODEL=gpt-4
MAX_TOKENS=4000
AI_TEMPERATURE=0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_linear

# Redis
REDIS_URL=redis://localhost:6379

# Optional Code Quality Tools
INSTALL_CODE_TOOLS=true
  `);

  console.log(`
Required Tools Installation:

# Node.js tools
npm install -g eslint prettier typescript

# Python tools (if using Python projects)
pip install bandit black radon

# Security tools
npm install -g semgrep
  `);
}

// Run the demo if this file is executed directly
if (require.main === module) {
  demonstrateAIServices().catch(console.error);
  demonstrateAPIUsage();
  showEnvironmentSetup();
}

export {
  demonstrateAIServices,
  demonstrateAPIUsage,
  showEnvironmentSetup
};