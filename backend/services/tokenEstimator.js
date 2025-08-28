// ABOUTME: Token estimation service for calculating LLM token costs
// ABOUTME: Provides accurate cost predictions based on issue complexity

class TokenEstimator {
  constructor() {
    // Base token costs for different operations
    this.baseCosts = {
      issueAnalysis: 500,        // Analyzing the issue description
      contextGathering: 1000,     // Understanding project context
      codeGeneration: 2000,       // Base for code generation
      testGeneration: 1500,       // Writing tests
      documentation: 800,         // Documentation generation
      review: 600                 // Code review tokens
    };

    // Multipliers based on complexity factors
    this.complexityMultipliers = {
      storyPoints: {
        1: 0.5,
        2: 0.8,
        3: 1.0,
        5: 1.5,
        8: 2.0,
        13: 3.0,
        21: 4.0
      },
      priority: {
        1: 1.3,  // Critical - more thorough analysis
        2: 1.2,  // High
        3: 1.0,  // Medium
        4: 0.9,  // Low
        5: 0.8   // Backlog
      },
      issueType: {
        'bug': 1.2,          // Bugs need more analysis
        'feature': 1.5,      // Features need more generation
        'refactor': 1.3,     // Refactoring needs careful analysis
        'documentation': 0.7, // Docs are lighter
        'test': 0.9,         // Tests are predictable
        'optimization': 1.4  // Performance work needs analysis
      }
    };

    // Token count per character ratios (approximate)
    this.charToTokenRatio = 0.25; // ~4 chars per token on average
  }

  /**
   * Estimate tokens for an issue based on its properties
   */
  estimateIssueTokens(issue) {
    let totalTokens = 0;

    // 1. Base cost for issue analysis
    totalTokens += this.baseCosts.issueAnalysis;

    // 2. Add tokens based on description length
    if (issue.description) {
      const descriptionTokens = Math.ceil(issue.description.length * this.charToTokenRatio);
      totalTokens += descriptionTokens;
    }

    // 3. Add context gathering cost
    totalTokens += this.baseCosts.contextGathering;

    // 4. Determine issue type and add appropriate costs
    const issueType = this.detectIssueType(issue);
    if (issueType === 'feature' || issueType === 'refactor') {
      totalTokens += this.baseCosts.codeGeneration;
    }
    if (issueType === 'bug' || issueType === 'feature') {
      totalTokens += this.baseCosts.testGeneration;
    }
    if (issue.ai_docs_generated !== false) {
      totalTokens += this.baseCosts.documentation;
    }

    // 5. Apply story point multiplier
    const storyPoints = issue.story_points || 3;
    const spMultiplier = this.complexityMultipliers.storyPoints[storyPoints] || 1.0;
    totalTokens *= spMultiplier;

    // 6. Apply priority multiplier
    const priority = issue.priority || 3;
    const priorityMultiplier = this.complexityMultipliers.priority[priority] || 1.0;
    totalTokens *= priorityMultiplier;

    // 7. Apply issue type multiplier
    const typeMultiplier = this.complexityMultipliers.issueType[issueType] || 1.0;
    totalTokens *= typeMultiplier;

    // 8. Add buffer for iterations and refinements (20%)
    totalTokens *= 1.2;

    // Round to nearest 100
    totalTokens = Math.round(totalTokens / 100) * 100;

    // Calculate confidence based on how much info we have
    const confidence = this.calculateConfidence(issue);

    // Estimate time in minutes (rough: 100 tokens per minute of work)
    const estimatedMinutes = Math.round(totalTokens / 100);

    return {
      token_cost: totalTokens,
      estimated_minutes: estimatedMinutes,
      ai_confidence: confidence,
      breakdown: {
        base_analysis: this.baseCosts.issueAnalysis,
        description_tokens: Math.ceil((issue.description?.length || 0) * this.charToTokenRatio),
        complexity_factor: spMultiplier,
        priority_factor: priorityMultiplier,
        type_factor: typeMultiplier
      }
    };
  }

  /**
   * Detect issue type from title and description
   */
  detectIssueType(issue) {
    const text = `${issue.title} ${issue.description || ''}`.toLowerCase();
    
    if (text.includes('bug') || text.includes('fix') || text.includes('error') || text.includes('broken')) {
      return 'bug';
    }
    if (text.includes('feature') || text.includes('add') || text.includes('implement') || text.includes('create')) {
      return 'feature';
    }
    if (text.includes('refactor') || text.includes('improve') || text.includes('optimize')) {
      return 'refactor';
    }
    if (text.includes('document') || text.includes('docs') || text.includes('readme')) {
      return 'documentation';
    }
    if (text.includes('test') || text.includes('spec') || text.includes('coverage')) {
      return 'test';
    }
    if (text.includes('performance') || text.includes('speed') || text.includes('slow')) {
      return 'optimization';
    }
    
    return 'feature'; // Default
  }

  /**
   * Calculate confidence in the estimate
   */
  calculateConfidence(issue) {
    let confidence = 0.5; // Base confidence

    // More confidence with story points
    if (issue.story_points) confidence += 0.15;
    
    // More confidence with detailed description
    if (issue.description && issue.description.length > 100) confidence += 0.15;
    
    // More confidence with priority set
    if (issue.priority && issue.priority !== 3) confidence += 0.1;
    
    // More confidence with labels
    if (issue.labels && issue.labels.length > 0) confidence += 0.1;

    // Cap at 0.95
    return Math.min(confidence, 0.95);
  }

  /**
   * Calculate cost in USD based on token usage
   */
  calculateCost(tokens, model = 'gpt-4') {
    const pricing = {
      'gpt-4': 0.03,        // $0.03 per 1K tokens
      'gpt-3.5-turbo': 0.001, // $0.001 per 1K tokens  
      'claude-3': 0.025,    // $0.025 per 1K tokens (estimate)
    };

    const pricePerToken = (pricing[model] || pricing['gpt-4']) / 1000;
    return tokens * pricePerToken;
  }

  /**
   * Update estimate based on actual usage
   */
  async updateEstimateFromActual(issueId, actualTokens, pool) {
    try {
      // Store the actual usage for learning
      await pool.query(
        `UPDATE issues 
         SET actual_token_cost = $1,
             token_cost_variance = $1 - COALESCE(token_cost, 0)
         WHERE id = $2`,
        [actualTokens, issueId]
      );

      // TODO: Use this data to improve future estimates via ML
      console.log(`Recorded actual tokens for issue ${issueId}: ${actualTokens}`);
    } catch (error) {
      console.error('Error updating token actuals:', error);
    }
  }
}

module.exports = TokenEstimator;