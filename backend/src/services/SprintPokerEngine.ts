// ABOUTME: Sprint Poker Engine for AI-powered task estimation
// ABOUTME: Analyzes tasks across 5 dimensions to provide accurate story points and time estimates

export interface ComplexityDimensions {
  code_footprint: number;     // 0-10: How many files/lines need to change
  integration_depth: number;   // 0-10: How many systems/APIs involved
  test_complexity: number;     // 0-10: How complex is testing this
  uncertainty: number;         // 0-10: How much unknown/research needed
  data_volume: number;        // 0-10: How much data manipulation needed
}

export interface TaskEstimation {
  story_points: number;        // Fibonacci: 1, 2, 3, 5, 8, 13, 21
  estimated_hours: number;     // Realistic time estimate
  confidence: number;          // 0-100: How confident in estimate
  complexity_score: ComplexityDimensions;
  reasoning: string[];         // Explanation of estimation
  suggested_subtasks: string[]; // Breakdown for complex tasks
  risks: string[];            // Identified risks
}

export class SprintPokerEngine {
  private readonly storyPointMap = [1, 2, 3, 5, 8, 13, 21];
  
  async estimateTask(description: string, title?: string): Promise<TaskEstimation> {
    // Analyze the task description
    const complexity = this.analyzeComplexity(description, title);
    const storyPoints = this.calculateStoryPoints(complexity);
    const hours = this.calculateHours(storyPoints, complexity);
    const confidence = this.calculateConfidence(complexity);
    const reasoning = this.generateReasoning(complexity, storyPoints);
    const subtasks = this.suggestSubtasks(description, complexity);
    const risks = this.identifyRisks(description, complexity);
    
    return {
      story_points: storyPoints,
      estimated_hours: hours,
      confidence,
      complexity_score: complexity,
      reasoning,
      suggested_subtasks: subtasks,
      risks
    };
  }
  
  private analyzeComplexity(description: string, title?: string): ComplexityDimensions {
    const text = `${title || ''} ${description}`.toLowerCase();
    
    // Code footprint analysis
    const code_footprint = this.analyzeCodeFootprint(text);
    
    // Integration depth analysis
    const integration_depth = this.analyzeIntegrationDepth(text);
    
    // Test complexity analysis
    const test_complexity = this.analyzeTestComplexity(text);
    
    // Uncertainty analysis
    const uncertainty = this.analyzeUncertainty(text);
    
    // Data volume analysis
    const data_volume = this.analyzeDataVolume(text);
    
    return {
      code_footprint,
      integration_depth,
      test_complexity,
      uncertainty,
      data_volume
    };
  }
  
  private analyzeCodeFootprint(text: string): number {
    let score = 2; // Base score
    
    // Keywords that increase code footprint
    const major = ['refactor', 'redesign', 'migrate', 'rewrite', 'architecture'];
    const moderate = ['feature', 'component', 'module', 'service', 'endpoint'];
    const minor = ['fix', 'update', 'tweak', 'adjust', 'change'];
    
    major.forEach(keyword => {
      if (text.includes(keyword)) score += 3;
    });
    
    moderate.forEach(keyword => {
      if (text.includes(keyword)) score += 2;
    });
    
    minor.forEach(keyword => {
      if (text.includes(keyword)) score += 1;
    });
    
    // Check for multiple file mentions
    if (text.match(/\b(files|components|modules|services)\b/g)?.length > 1) {
      score += 2;
    }
    
    return Math.min(10, score);
  }
  
  private analyzeIntegrationDepth(text: string): number {
    let score = 1; // Base score
    
    // Integration keywords
    const integrations = [
      'api', 'database', 'external', 'third-party', 'webhook',
      'graphql', 'rest', 'websocket', 'redis', 'postgres',
      'authentication', 'authorization', 'oauth', 'jwt'
    ];
    
    integrations.forEach(keyword => {
      if (text.includes(keyword)) score += 1.5;
    });
    
    // Multiple system mentions
    if (text.includes('integrate') || text.includes('integration')) {
      score += 2;
    }
    
    return Math.min(10, score);
  }
  
  private analyzeTestComplexity(text: string): number {
    let score = 3; // Base score
    
    // Test-related keywords
    if (text.includes('unit test')) score += 1;
    if (text.includes('integration test')) score += 2;
    if (text.includes('e2e test') || text.includes('end-to-end')) score += 3;
    if (text.includes('test coverage')) score += 2;
    if (text.includes('edge case')) score += 2;
    if (text.includes('performance test')) score += 3;
    
    // Complex scenarios
    if (text.includes('async') || text.includes('concurrent')) score += 2;
    if (text.includes('real-time') || text.includes('websocket')) score += 2;
    
    return Math.min(10, score);
  }
  
  private analyzeUncertainty(text: string): number {
    let score = 2; // Base score
    
    // Uncertainty indicators
    const uncertain = [
      'research', 'investigate', 'explore', 'figure out',
      'not sure', 'maybe', 'possibly', 'might', 'could',
      'spike', 'poc', 'proof of concept', 'experiment'
    ];
    
    uncertain.forEach(keyword => {
      if (text.includes(keyword)) score += 2;
    });
    
    // New technology indicators
    if (text.includes('new') || text.includes('first time')) score += 2;
    if (text.includes('ai') || text.includes('machine learning')) score += 1;
    
    // Clarity indicators (reduce uncertainty)
    if (text.includes('clear') || text.includes('straightforward')) score -= 1;
    if (text.includes('similar to') || text.includes('like')) score -= 1;
    
    return Math.min(10, Math.max(0, score));
  }
  
  private analyzeDataVolume(text: string): number {
    let score = 1; // Base score
    
    // Data-related keywords
    const dataKeywords = [
      'migration', 'bulk', 'batch', 'import', 'export',
      'etl', 'transform', 'aggregate', 'report', 'analytics',
      'large', 'scale', 'performance', 'optimize'
    ];
    
    dataKeywords.forEach(keyword => {
      if (text.includes(keyword)) score += 1.5;
    });
    
    // Specific data operations
    if (text.includes('database')) score += 1;
    if (text.includes('query') || text.includes('queries')) score += 1;
    if (text.match(/\d+k|\d+m|thousand|million/)) score += 2;
    
    return Math.min(10, score);
  }
  
  private calculateStoryPoints(complexity: ComplexityDimensions): number {
    // Weighted average of dimensions
    const weights = {
      code_footprint: 0.30,
      integration_depth: 0.25,
      test_complexity: 0.20,
      uncertainty: 0.15,
      data_volume: 0.10
    };
    
    const weightedScore = 
      complexity.code_footprint * weights.code_footprint +
      complexity.integration_depth * weights.integration_depth +
      complexity.test_complexity * weights.test_complexity +
      complexity.uncertainty * weights.uncertainty +
      complexity.data_volume * weights.data_volume;
    
    // Map to story points
    if (weightedScore <= 2) return 1;
    if (weightedScore <= 3.5) return 2;
    if (weightedScore <= 5) return 3;
    if (weightedScore <= 6.5) return 5;
    if (weightedScore <= 8) return 8;
    if (weightedScore <= 9) return 13;
    return 21;
  }
  
  private calculateHours(storyPoints: number, complexity: ComplexityDimensions): number {
    // Base hours per story point
    const baseHours = {
      1: 1,
      2: 2.5,
      3: 4,
      5: 8,
      8: 16,
      13: 24,
      21: 40
    };
    
    let hours = baseHours[storyPoints] || 8;
    
    // Adjust for uncertainty
    if (complexity.uncertainty > 7) {
      hours *= 1.5;
    } else if (complexity.uncertainty > 5) {
      hours *= 1.25;
    }
    
    // Round to nearest 0.5
    return Math.round(hours * 2) / 2;
  }
  
  private calculateConfidence(complexity: ComplexityDimensions): number {
    // Start with high confidence
    let confidence = 95;
    
    // Reduce based on uncertainty
    confidence -= complexity.uncertainty * 5;
    
    // Reduce for very complex tasks
    const avgComplexity = Object.values(complexity).reduce((a, b) => a + b, 0) / 5;
    if (avgComplexity > 7) confidence -= 10;
    if (avgComplexity > 8.5) confidence -= 10;
    
    return Math.max(30, Math.min(100, confidence));
  }
  
  private generateReasoning(complexity: ComplexityDimensions, storyPoints: number): string[] {
    const reasoning = [];
    
    if (complexity.code_footprint > 7) {
      reasoning.push('Large code footprint - multiple files/modules affected');
    } else if (complexity.code_footprint > 4) {
      reasoning.push('Moderate code changes required');
    } else {
      reasoning.push('Small, localized code changes');
    }
    
    if (complexity.integration_depth > 6) {
      reasoning.push('Complex integrations with multiple systems');
    } else if (complexity.integration_depth > 3) {
      reasoning.push('Some external system integration required');
    }
    
    if (complexity.test_complexity > 6) {
      reasoning.push('Extensive testing required including edge cases');
    }
    
    if (complexity.uncertainty > 6) {
      reasoning.push('High uncertainty - research/exploration needed');
    }
    
    if (complexity.data_volume > 5) {
      reasoning.push('Significant data processing/migration involved');
    }
    
    reasoning.push(`Estimated at ${storyPoints} story points based on overall complexity`);
    
    return reasoning;
  }
  
  private suggestSubtasks(description: string, complexity: ComplexityDimensions): string[] {
    const subtasks = [];
    
    // Always suggest basic subtasks for larger tasks
    if (complexity.code_footprint > 5) {
      subtasks.push('Design and plan implementation approach');
      subtasks.push('Implement core functionality');
      subtasks.push('Add error handling and edge cases');
    }
    
    if (complexity.test_complexity > 4) {
      subtasks.push('Write unit tests');
      if (complexity.test_complexity > 6) {
        subtasks.push('Write integration tests');
      }
      if (complexity.test_complexity > 8) {
        subtasks.push('Write end-to-end tests');
      }
    }
    
    if (complexity.integration_depth > 4) {
      subtasks.push('Set up external service connections');
      subtasks.push('Implement API integration layer');
      subtasks.push('Add retry logic and error handling');
    }
    
    if (complexity.uncertainty > 5) {
      subtasks.push('Research and spike implementation options');
      subtasks.push('Create proof of concept');
    }
    
    if (complexity.data_volume > 5) {
      subtasks.push('Design data migration strategy');
      subtasks.push('Implement batch processing');
      subtasks.push('Add progress tracking and rollback capability');
    }
    
    // Always add these for any non-trivial task
    if (subtasks.length > 0) {
      subtasks.push('Code review and refactoring');
      subtasks.push('Update documentation');
    }
    
    return subtasks;
  }
  
  private identifyRisks(description: string, complexity: ComplexityDimensions): string[] {
    const risks = [];
    
    if (complexity.uncertainty > 7) {
      risks.push('High uncertainty may lead to scope creep');
    }
    
    if (complexity.integration_depth > 7) {
      risks.push('External dependencies could cause delays');
    }
    
    if (complexity.data_volume > 7) {
      risks.push('Data migration could impact performance');
    }
    
    if (complexity.code_footprint > 8) {
      risks.push('Large changes may introduce regressions');
    }
    
    if (description.includes('real-time') || description.includes('websocket')) {
      risks.push('Real-time features may have scalability challenges');
    }
    
    if (description.includes('security') || description.includes('auth')) {
      risks.push('Security implementation requires careful review');
    }
    
    return risks;
  }
  
  async analyzeSprintCapacity(
    availableHours: number,
    issues: Array<{ id: string; description: string; title?: string }>
  ): Promise<{
    recommended: string[];
    total_points: number;
    total_hours: number;
    confidence: number;
  }> {
    const estimations = await Promise.all(
      issues.map(issue => this.estimateTask(issue.description, issue.title))
    );
    
    // Sort by confidence and value (lower story points first for quick wins)
    const sortedIssues = issues.map((issue, i) => ({
      ...issue,
      estimation: estimations[i]
    })).sort((a, b) => {
      // Prioritize high confidence, low effort tasks
      const scoreA = a.estimation.confidence / a.estimation.story_points;
      const scoreB = b.estimation.confidence / b.estimation.story_points;
      return scoreB - scoreA;
    });
    
    const recommended = [];
    let totalHours = 0;
    let totalPoints = 0;
    
    for (const issue of sortedIssues) {
      if (totalHours + issue.estimation.estimated_hours <= availableHours) {
        recommended.push(issue.id);
        totalHours += issue.estimation.estimated_hours;
        totalPoints += issue.estimation.story_points;
      }
    }
    
    const avgConfidence = recommended.length > 0
      ? estimations.reduce((sum, e) => sum + e.confidence, 0) / estimations.length
      : 0;
    
    return {
      recommended,
      total_points: totalPoints,
      total_hours: totalHours,
      confidence: Math.round(avgConfidence)
    };
  }
}