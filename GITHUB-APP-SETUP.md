# GitHub App Setup - Complete Guide

## What You Need to Set Up

### ✅ Already Done (in the code):
- ✅ Backend webhook receiver (`/api/github/webhook`)
- ✅ Claude integration service
- ✅ Database schema for reviews
- ✅ AI feedback loop system
- ✅ Frontend dashboard component
- ✅ NPM dependencies installed

### 🔴 What YOU Need to Do:

## Step 1: Run Database Migrations

```bash
# Connect to your PostgreSQL database
psql postgresql://lineary:lineary_password@localhost:5432/lineary_db

# Run the GitHub integration migration
\i backend/migrations/008_add_github_integration.sql

# Verify tables were created
\dt code_reviews
\dt review_comments
\dt project_github_config
\dt ai_feedback_loop
```

## Step 2: Create GitHub App

### Go to GitHub Settings
1. Navigate to: https://github.com/settings/apps
2. Click "New GitHub App"

### Fill Out App Information
```yaml
GitHub App name: Lineary-AI-Reviewer-[YourName]  # Must be unique
Description: AI-powered code reviews for Lineary projects
Homepage URL: https://your-lineary-domain.com

Webhook:
  Active: ✅ Check this box
  Webhook URL: https://your-lineary-domain.com/api/github/webhook
  Webhook secret: [Generate a strong secret and save it]

Permissions (Repository):
  Contents: Read
  Issues: Write  
  Pull requests: Write
  Metadata: Read

Subscribe to events:
  ✅ Pull request
  ✅ Pull request review
  ✅ Pull request review comment
  ✅ Push

Where can this GitHub App be installed?: 
  ○ Only on this account (recommended for testing)
  ○ Any account (for production)
```

### After Creating the App
1. **Save the App ID** (you'll see it at the top of the app page)
2. **Generate a private key**:
   - Scroll to "Private keys" section
   - Click "Generate a private key"
   - A `.pem` file will download - SAVE THIS SECURELY
3. **Install the app**:
   - Click "Install App" in the left sidebar
   - Choose your repositories

## Step 3: Get Anthropic API Key

1. Go to: https://console.anthropic.com
2. Create an account if needed
3. Go to API Keys section
4. Create a new API key
5. Save it securely

## Step 4: Configure Lineary

### Create Configuration File
Save your GitHub App private key as:
```bash
cp ~/Downloads/your-app-name.*.private-key.pem backend/github-app-private-key.pem
chmod 600 backend/github-app-private-key.pem
```

### Update .env File
```bash
cd /home/jarvis/projects/Lineary
cp .env.example .env
```

Edit `.env` and add:
```env
# GitHub App Configuration
GITHUB_APP_ID=123456  # Your actual App ID
GITHUB_PRIVATE_KEY_PATH=./backend/github-app-private-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret-from-step-2

# Claude AI Configuration  
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx  # Your actual API key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Your domain
PUBLIC_URL=https://your-actual-domain.com
```

## Step 5: Restart Services

```bash
# If using Docker
docker-compose down
docker-compose up -d

# If running locally
# Restart backend
cd backend
npm run start

# Restart frontend
cd ../frontend
npm run start
```

## Step 6: Test the Integration

### Create a Test PR
1. Create a new issue in Lineary
2. Note the issue number (e.g., #123)
3. Create a branch and make changes:
```bash
git checkout -b test/123-github-app-test
echo "test" > test.js
git add test.js
git commit -m "test: Testing GitHub App integration #123"
git push origin test/123-github-app-test
```

4. Create a Pull Request on GitHub
   - Title: "Test GitHub App Integration #123"
   - The PR should automatically get a Claude review within 30 seconds

### Verify It's Working
Check for:
- ✅ Claude review comment appears on the PR
- ✅ Check Lineary database:
```sql
SELECT * FROM code_reviews ORDER BY created_at DESC LIMIT 1;
SELECT * FROM issues WHERE github_pr_number IS NOT NULL;
```
- ✅ Check webhook logs:
```bash
docker logs lineary-backend | grep "webhook"
```

## Step 7: Configure Projects

For each project in Lineary that should use GitHub integration:

```bash
# Via API
curl -X POST https://your-domain.com/api/github/configure \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "your-project-uuid",
    "repository": "owner/repo-name",
    "installationId": 12345678
  }'
```

## Troubleshooting

### Webhook Not Receiving Events
- Check GitHub App webhook settings - should show recent deliveries
- Verify webhook URL is publicly accessible
- Check webhook secret matches in both places
- Look at webhook delivery logs in GitHub

### Claude Reviews Not Appearing
- Verify Anthropic API key is valid
- Check backend logs: `docker logs lineary-backend`
- Ensure GitHub App has correct permissions
- Verify PR has issue reference (#123)

### Database Errors
- Ensure migration was run successfully
- Check PostgreSQL logs
- Verify database connection in .env

### No PR-to-Issue Linking
- Ensure commit messages include #123 reference
- PR title or description should mention issue
- Check `github_pr_number` column in issues table

## Security Checklist

- [ ] Private key file has restricted permissions (600)
- [ ] Webhook secret is strong and unique
- [ ] API keys are not committed to git
- [ ] .env file is in .gitignore
- [ ] HTTPS is enabled for webhook URL
- [ ] Database has proper access controls

## Monitoring

### Check Integration Health
```bash
# API endpoint
curl https://your-domain.com/api/github/insights/[project-id]

# Database metrics
psql -c "SELECT COUNT(*) as reviews, 
         AVG((insights->>'codeQualityScore')::float) as avg_quality 
         FROM code_reviews 
         WHERE created_at > NOW() - INTERVAL '7 days'"
```

### View AI Learning Progress
```bash
curl https://your-domain.com/api/ai/metrics/[project-id]
```

## Next Steps

Once everything is working:

1. **Train your team** on the #123 reference rule
2. **Monitor metrics** for the first week
3. **Adjust AI prompts** if needed in `backend/routes/github-app.js`
4. **Scale up** by installing on more repositories
5. **Track improvements** in estimation accuracy

## Support

If you encounter issues:
1. Check backend logs
2. Review GitHub webhook deliveries
3. Verify all environment variables
4. Check database migrations
5. Open an issue on GitHub with details