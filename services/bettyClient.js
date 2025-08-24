// ABOUTME: Betty API client for project integration
// ABOUTME: Handles HTTP communication with centralized Betty Memory System

const axios = require('axios');

class BettyApiClient {
  constructor(apiUrl = 'http://localhost:3034', userId = 'e8e3f2de-070d-4dbd-b899-e49745f1d29b', projectId = 'lineary-project') {
    this.apiUrl = apiUrl;
    this.userId = userId;
    this.projectId = projectId;
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
        'X-Project-ID': projectId
      }
    });
  }

  /**
   * Store development knowledge in Betty
   */
  async storeKnowledge(title, content, knowledgeType = 'development', tags = []) {
    try {
      const response = await this.client.post('/api/knowledge/create', {
        title,
        content,
        knowledge_type: knowledgeType,
        tags: ['lineary', ...tags],
        user_id: this.userId,
        project_id: this.projectId
      });
      return response.data;
    } catch (error) {
      console.error('Failed to store knowledge:', error.message);
      throw error;
    }
  }

  /**
   * Search Betty knowledge base
   */
  async searchKnowledge(query, k = 5, searchType = 'hybrid') {
    try {
      const response = await this.client.post('/api/knowledge/search', {
        query,
        user_id: this.userId,
        k,
        search_type: searchType,
        project_filter: this.projectId
      });
      return response.data;
    } catch (error) {
      console.error('Failed to search knowledge:', error.message);
      throw error;
    }
  }

  /**
   * Get cross-project insights
   */
  async getCrossProjectInsights(query) {
    try {
      const response = await this.client.post('/api/v2/cross-project/search', {
        query,
        user_id: this.userId,
        include_projects: 'all',
        similarity_threshold: 0.7
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get cross-project insights:', error.message);
      throw error;
    }
  }

  /**
   * Store development session summary
   */
  async storeSessionSummary(sessionTitle, accomplishments, challenges, decisions) {
    const content = `
Session: ${sessionTitle}

Accomplishments:
${accomplishments.map(item => `- ${item}`).join('\n')}

Challenges:
${challenges.map(item => `- ${item}`).join('\n')}

Key Decisions:
${decisions.map(item => `- ${item}`).join('\n')}
    `.trim();

    return this.storeKnowledge(
      `Lineary - ${sessionTitle}`,
      content,
      'session_summary',
      ['session', 'development']
    );
  }

  /**
   * Store bug fix details
   */
  async storeBugFix(issue, rootCause, solution, prevention) {
    const content = `
Issue: ${issue}
Root Cause: ${rootCause}
Solution: ${solution}
Prevention: ${prevention}
    `.trim();

    return this.storeKnowledge(
      `Lineary Bug Fix - ${issue}`,
      content,
      'bug_fix',
      ['bug', 'solution']
    );
  }

  /**
   * Store architecture decision
   */
  async storeArchitecturalDecision(decision, reasoning, tradeoffs, impact) {
    const content = `
Decision: ${decision}
Reasoning: ${reasoning}
Trade-offs: ${tradeoffs}
Future Impact: ${impact}
    `.trim();

    return this.storeKnowledge(
      `Lineary Architecture - ${decision}`,
      content,
      'architecture',
      ['architecture', 'decision']
    );
  }

  /**
   * Get development recommendations based on current task
   */
  async getRecommendations(currentTask) {
    try {
      // Search for similar tasks across projects
      const insights = await this.getCrossProjectInsights(currentTask);
      
      // Also search within current project
      const projectInsights = await this.searchKnowledge(currentTask);
      
      return {
        cross_project: insights,
        project_specific: projectInsights,
        recommendations: this.generateRecommendations(insights, projectInsights)
      };
    } catch (error) {
      console.error('Failed to get recommendations:', error.message);
      return null;
    }
  }

  /**
   * Generate actionable recommendations from insights
   */
  generateRecommendations(crossProject, projectSpecific) {
    const recommendations = [];
    
    // Analyze patterns and suggest improvements
    if (crossProject?.data?.results?.length > 0) {
      recommendations.push({
        type: 'cross_project_pattern',
        message: `Similar approach used in ${crossProject.data.results[0].project_id}`,
        confidence: crossProject.data.results[0].score
      });
    }
    
    if (projectSpecific?.data?.length > 0) {
      recommendations.push({
        type: 'project_history',
        message: `Previous work on similar task: ${projectSpecific.data[0].title}`,
        confidence: projectSpecific.data[0].relevance_score || 0.8
      });
    }
    
    return recommendations;
  }

  /**
   * Check Betty system health
   */
  async checkHealth() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Betty health check failed:', error.message);
      return { status: 'unhealthy', error: error.message };
    }
  }
}

module.exports = BettyApiClient;