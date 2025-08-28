# LLM Integration Rules for Lineary

## Critical Rules for AI Agents Using Lineary

### 🔴 MANDATORY: Issue Linking in Git Commits and PRs

**RULE #1**: Every commit message and PR title MUST reference the Lineary issue number using one of these formats:
- `#123` - where 123 is the issue number
- `LIN-123` - where 123 is the issue number
- `Fixes #123` - to auto-close the issue when PR merges
- `Closes #123` - to auto-close the issue when PR merges

**Why This Is Critical:**
- Enables automatic PR-to-Issue synchronization
- Triggers Claude code reviews with context
- Tracks actual vs estimated time for AI learning
- Maintains complete development cycle traceability
- Feeds the AI improvement loop

### ✅ Correct Examples:

```bash
# Commit messages
git commit -m "feat: Add user authentication #45"
git commit -m "fix: Resolve memory leak in parser LIN-102"
git commit -m "docs: Update API documentation for #78"

# PR titles
"Add payment processing integration #234"
"Fix: Security vulnerability in auth flow - Fixes #156"
"Feature: Implement real-time notifications LIN-89"
```

### ❌ Incorrect Examples (BREAKS THE CYCLE):

```bash
# These break the automation!
git commit -m "Add new feature"  # No issue reference
git commit -m "Fix bug"  # No traceability
git commit -m "Update code"  # No context for AI
```

## Complete Workflow for LLM Agents

### 1. Creating Tasks in Lineary

When creating issues/tasks, always include:
```json
{
  "title": "Clear, actionable title",
  "description": "Detailed requirements with acceptance criteria",
  "estimated_hours": 8,  // AI will learn from this
  "story_points": 5,
  "type": "feature|bug|task|improvement",
  "priority": 1-5
}
```

### 2. Starting Development

```bash
# Create branch with issue reference
git checkout -b feature/123-add-authentication

# Or
git checkout -b fix/LIN-456-memory-leak
```

### 3. Committing Code

```bash
# ALWAYS reference the issue
git add .
git commit -m "feat: Implement OAuth2 authentication flow #123

- Add Google OAuth provider
- Implement JWT token generation
- Add session management

This addresses the requirements in issue #123"
```

### 4. Creating Pull Requests

```markdown
Title: Implement OAuth2 authentication #123

Description:
## Summary
This PR implements OAuth2 authentication as specified in #123

## Changes
- Added OAuth2 provider integration
- Implemented JWT tokens
- Added session management

## Testing
- Unit tests added
- Manual testing completed
- Security review passed

Fixes #123
```

### 5. Tracking Time

When completing work, record actual time:
```javascript
// Via API
POST /api/ai/feedback/completion
{
  "issueId": "123",
  "actualHours": 10.5
}
```

## Benefits of Following These Rules

### For AI/LLM:
1. **Learning Loop**: Every PR provides data to improve estimates
2. **Context Awareness**: Claude reviews have full issue context
3. **Pattern Recognition**: AI learns which types of issues take longer
4. **Quality Improvement**: Review feedback improves over time

### For Developers:
1. **Automatic Updates**: Issues update when PRs merge
2. **Time Tracking**: Automatic tracking via PR lifecycle
3. **Code Reviews**: Instant Claude AI reviews on every PR
4. **Traceability**: Complete history from idea to deployment

### For Project Managers:
1. **Accurate Estimates**: AI improves estimation over time
2. **Quality Metrics**: Track code quality trends
3. **Velocity Tracking**: Accurate sprint velocity data
4. **Risk Detection**: Early warning of security/performance issues

## Integration Points

### GitHub App Webhooks
- **PR Opened**: Triggers Claude review
- **PR Merged**: Updates issue status, records completion time
- **PR Commented**: Can trigger additional Claude analysis

### Claude Review Triggers
- Security-focused review: `@claude security`
- Performance analysis: `@claude performance`
- Code explanation: `@claude explain`

### AI Feedback Loop
- Estimation accuracy improves with each completion
- Review quality patterns inform future reviews
- Issue type patterns help categorization

## Automation Benefits

When rules are followed, these happen automatically:

1. **PR Created** → Claude reviews code
2. **Review Posted** → Insights stored in Lineary
3. **PR Merged** → Issue marked complete
4. **Completion** → Actual time recorded
5. **Learning** → Next estimate more accurate
6. **Improvement** → 5-10% accuracy gain per sprint

## API Endpoints for LLM Integration

### Creating Issues with Proper Metadata
```http
POST /api/issues
{
  "project_id": "uuid",
  "title": "Implement feature X",
  "description": "Detailed spec...",
  "estimated_hours": 8,
  "ai_confidence": "high|medium|low",
  "github_labels": ["enhancement", "backend"]
}
```

### Getting AI-Improved Estimates
```http
POST /api/ai/estimate
{
  "projectId": "uuid",
  "issueType": "feature",
  "complexity": 5
}

Response:
{
  "estimate": 12.5,
  "confidence": "high",
  "basedOn": 15,
  "historicalAccuracy": 87
}
```

### Recording Completions
```http
POST /api/ai/feedback/completion
{
  "issueId": "123",
  "actualHours": 10.5
}
```

### Getting Learning Insights
```http
GET /api/ai/insights/{projectId}

Response:
{
  "trend": [...],
  "byType": {...},
  "patterns": [...],
  "summary": {
    "isImproving": true,
    "currentAccuracy": 87,
    "totalDataPoints": 45
  }
}
```

## Best Practices for LLM Agents

### 1. Issue Creation
- Break large features into smaller, trackable issues
- Each issue should be completable in 1-3 days
- Include clear acceptance criteria
- Add relevant labels for categorization

### 2. Estimation
- Use historical data via `/api/ai/estimate`
- Factor in complexity, dependencies, and unknowns
- Update estimates as understanding improves

### 3. Progress Tracking
- Update issue status in real-time
- Add comments for significant decisions
- Link related issues and PRs

### 4. Learning Integration
- Always record actual time spent
- Note if estimate was significantly off and why
- Flag issues that had unexpected complexity

## Monitoring the AI Loop

### Health Metrics
- **Estimation Accuracy**: Target >80% within 20% margin
- **Review Quality**: Target >90% helpful reviews
- **Issue Linkage**: Target 100% PRs linked to issues
- **Learning Rate**: Expect 5-10% improvement per sprint

### Warning Signs
- PRs without issue references (breaks the loop)
- Issues closed without PRs (no learning data)
- Estimates not improving (feedback not recorded)
- Reviews not posting (webhook issues)

## Troubleshooting

### PR Not Linked to Issue
- Check commit messages for issue references
- Verify PR title includes #123 or LIN-123
- Ensure webhook is configured correctly

### Claude Review Not Appearing
- Verify GitHub App is installed on repository
- Check webhook logs for errors
- Ensure Anthropic API key is valid

### Estimates Not Improving
- Verify completions are being recorded
- Check that actual hours are being tracked
- Ensure sufficient data points (>10 completions)

## Summary

**THE GOLDEN RULE**: Every piece of code MUST be traceable to a Lineary issue via #123 or LIN-123 references. This enables the complete AI development cycle that makes the system smarter with every iteration.

Without issue references, you break:
- Automatic PR tracking
- Claude code reviews with context
- Time tracking automation
- AI learning loop
- Project metrics
- Sprint velocity calculations

**Follow the rules → System gets smarter → Better estimates → Higher quality code → Faster delivery**