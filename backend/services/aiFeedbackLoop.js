// ABOUTME: AI Feedback Loop service for improving task estimation accuracy
// ABOUTME: Learns from actual vs estimated times and review quality to improve future predictions

class AIFeedbackLoop {
  constructor(db) {
    this.db = db;
  }

  /**
   * Record feedback when an issue is completed
   */
  async recordCompletion(issueId, actualHours) {
    try {
      // Get the issue with its original estimate
      const issue = await this.db.oneOrNone(
        'SELECT * FROM issues WHERE id = $1',
        [issueId]
      );

      if (!issue) return;

      // Get any code reviews associated with this issue
      const reviews = await this.db.any(`
        SELECT cr.*, 
               (cr.insights->>'codeQualityScore')::float as quality_score
        FROM code_reviews cr
        WHERE cr.pr_number IN (
          SELECT github_pr_number FROM issues WHERE id = $1
        )
      `, [issueId]);

      // Calculate accuracy score
      const estimatedHours = issue.estimated_hours || 0;
      const accuracyScore = this.calculateAccuracyScore(estimatedHours, actualHours);
      
      // Calculate average review quality
      const avgQualityScore = reviews.length > 0 
        ? reviews.reduce((sum, r) => sum + (r.quality_score || 0), 0) / reviews.length
        : null;

      // Store feedback data
      await this.db.none(`
        INSERT INTO ai_feedback_loop 
        (issue_id, estimated_hours, actual_hours, ai_accuracy_score, review_quality_score, feedback_data)
        VALUES ($1, $2, $3, $4, $5, $6)
      `, [
        issueId,
        estimatedHours,
        actualHours,
        accuracyScore,
        avgQualityScore,
        JSON.stringify({
          issue_type: issue.type,
          issue_priority: issue.priority,
          issue_complexity: issue.story_points,
          had_security_issues: reviews.some(r => r.insights?.hasSecurityIssues),
          had_performance_issues: reviews.some(r => r.insights?.hasPerformanceIssues),
          review_count: reviews.length,
          completion_date: new Date().toISOString()
        })
      ]);

      // Update project-level metrics
      await this.updateProjectMetrics(issue.project_id);

      return {
        accuracyScore,
        avgQualityScore,
        feedback: 'Feedback recorded successfully'
      };
    } catch (error) {
      console.error('Error recording completion feedback:', error);
      throw error;
    }
  }

  /**
   * Calculate accuracy score based on estimated vs actual time
   */
  calculateAccuracyScore(estimated, actual) {
    if (!estimated || !actual) return 0;
    
    const difference = Math.abs(estimated - actual);
    const percentDiff = (difference / estimated) * 100;
    
    // Score from 0-100, where 100 is perfect accuracy
    if (percentDiff <= 10) return 100;
    if (percentDiff <= 20) return 90;
    if (percentDiff <= 30) return 80;
    if (percentDiff <= 50) return 60;
    if (percentDiff <= 75) return 40;
    return 20;
  }

  /**
   * Get improved estimate based on historical data
   */
  async getImprovedEstimate(projectId, issueType, complexity) {
    try {
      // Get historical data for similar issues
      const historicalData = await this.db.any(`
        SELECT 
          afl.actual_hours,
          afl.estimated_hours,
          afl.ai_accuracy_score,
          i.story_points,
          i.type
        FROM ai_feedback_loop afl
        JOIN issues i ON i.id = afl.issue_id
        WHERE i.project_id = $1
          AND ($2::text IS NULL OR i.type = $2)
          AND ($3::int IS NULL OR ABS(i.story_points - $3) <= 2)
        ORDER BY afl.created_at DESC
        LIMIT 20
      `, [projectId, issueType, complexity]);

      if (historicalData.length === 0) {
        // No historical data, return default estimate
        return {
          estimate: complexity * 2, // Simple heuristic
          confidence: 'low',
          basedOn: 0
        };
      }

      // Calculate weighted average based on accuracy scores
      let totalWeight = 0;
      let weightedSum = 0;

      historicalData.forEach(data => {
        const weight = (data.ai_accuracy_score || 50) / 100;
        totalWeight += weight;
        weightedSum += data.actual_hours * weight;
      });

      const improvedEstimate = weightedSum / totalWeight;

      // Calculate confidence based on data points and accuracy
      const avgAccuracy = historicalData.reduce((sum, d) => sum + (d.ai_accuracy_score || 0), 0) / historicalData.length;
      const confidence = this.getConfidenceLevel(historicalData.length, avgAccuracy);

      return {
        estimate: Math.round(improvedEstimate * 10) / 10, // Round to 1 decimal
        confidence,
        basedOn: historicalData.length,
        historicalAccuracy: Math.round(avgAccuracy)
      };
    } catch (error) {
      console.error('Error getting improved estimate:', error);
      return {
        estimate: complexity * 2,
        confidence: 'low',
        basedOn: 0
      };
    }
  }

  /**
   * Determine confidence level based on data points and accuracy
   */
  getConfidenceLevel(dataPoints, avgAccuracy) {
    if (dataPoints >= 10 && avgAccuracy >= 80) return 'high';
    if (dataPoints >= 5 && avgAccuracy >= 70) return 'medium';
    return 'low';
  }

  /**
   * Update project-level AI metrics
   */
  async updateProjectMetrics(projectId) {
    try {
      // Calculate overall project estimation accuracy
      const metrics = await this.db.one(`
        SELECT 
          AVG(ai_accuracy_score) as avg_accuracy,
          AVG(review_quality_score) as avg_quality,
          COUNT(*) as total_feedbacks,
          AVG(ABS(estimated_hours - actual_hours)) as avg_deviation
        FROM ai_feedback_loop afl
        JOIN issues i ON i.id = afl.issue_id
        WHERE i.project_id = $1
      `, [projectId]);

      // Store updated metrics
      await this.db.none(`
        INSERT INTO project_metrics 
        (project_id, metric_type, value, metadata, created_at)
        VALUES ($1, 'ai_accuracy', $2, $3, CURRENT_TIMESTAMP)
      `, [
        projectId,
        metrics.avg_accuracy || 0,
        JSON.stringify({
          avg_quality: metrics.avg_quality,
          total_feedbacks: metrics.total_feedbacks,
          avg_deviation: metrics.avg_deviation,
          last_updated: new Date().toISOString()
        })
      ]);

      return metrics;
    } catch (error) {
      console.error('Error updating project metrics:', error);
    }
  }

  /**
   * Get AI learning insights for a project
   */
  async getLearningInsights(projectId) {
    try {
      // Get recent accuracy trend
      const trend = await this.db.any(`
        SELECT 
          DATE_TRUNC('week', afl.created_at) as week,
          AVG(afl.ai_accuracy_score) as avg_accuracy,
          AVG(afl.review_quality_score) as avg_quality,
          COUNT(*) as data_points
        FROM ai_feedback_loop afl
        JOIN issues i ON i.id = afl.issue_id
        WHERE i.project_id = $1
          AND afl.created_at > NOW() - INTERVAL '3 months'
        GROUP BY week
        ORDER BY week DESC
        LIMIT 12
      `, [projectId]);

      // Get improvement by issue type
      const byType = await this.db.any(`
        SELECT 
          i.type,
          AVG(afl.ai_accuracy_score) as avg_accuracy,
          COUNT(*) as count,
          AVG(ABS(afl.estimated_hours - afl.actual_hours)) as avg_deviation
        FROM ai_feedback_loop afl
        JOIN issues i ON i.id = afl.issue_id
        WHERE i.project_id = $1
        GROUP BY i.type
      `, [projectId]);

      // Get common patterns in inaccurate estimates
      const patterns = await this.db.any(`
        SELECT 
          afl.feedback_data->>'issue_type' as issue_type,
          afl.feedback_data->>'had_security_issues' as had_security,
          AVG(afl.ai_accuracy_score) as avg_accuracy,
          COUNT(*) as occurrences
        FROM ai_feedback_loop afl
        JOIN issues i ON i.id = afl.issue_id
        WHERE i.project_id = $1
          AND afl.ai_accuracy_score < 60
        GROUP BY issue_type, had_security
        HAVING COUNT(*) > 2
        ORDER BY occurrences DESC
      `, [projectId]);

      return {
        trend,
        byType,
        patterns,
        summary: {
          isImproving: trend.length > 1 && trend[0].avg_accuracy > trend[1].avg_accuracy,
          currentAccuracy: trend.length > 0 ? trend[0].avg_accuracy : 0,
          totalDataPoints: trend.reduce((sum, t) => sum + t.data_points, 0)
        }
      };
    } catch (error) {
      console.error('Error getting learning insights:', error);
      return {
        trend: [],
        byType: [],
        patterns: [],
        summary: {
          isImproving: false,
          currentAccuracy: 0,
          totalDataPoints: 0
        }
      };
    }
  }
}

module.exports = AIFeedbackLoop;