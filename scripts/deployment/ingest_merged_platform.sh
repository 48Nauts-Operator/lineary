#!/bin/bash

# BETTY Integration Script: Merged Platform Authentication Work
# This script ingests all the merged platform authentication work into BETTY memory system

echo "🔧 BETTY Integration: Merged Platform Authentication Work"
echo "=================================================="

# Check if BETTY API is available
echo "🔍 Checking BETTY Memory API health..."
if ! curl -s http://localhost:8001/health/ > /dev/null; then
    echo "❌ BETTY Memory API is not available. Please start with: docker-compose up -d"
    exit 1
fi

echo "✅ BETTY Memory API is healthy"

# Generate project UUID
PROJECT_UUID="550e8400-e29b-41d4-a716-446655440123"
echo "📝 Using Project UUID: $PROJECT_UUID"

# 1. Main Project Architecture Record
echo "📊 Creating main project architecture record..."
cat > /tmp/main_project.json << EOF
{
  "title": "Merged Platform: 137docs + NautFinance Authentication Integration",
  "content": "# Merged Platform Authentication System\n\n## Overview\nSuccessfully merged 137docs document processing platform with NautFinance business intelligence, implementing unified authentication with dual-path onboarding.\n\n## Key Components\n- **Modular Authentication**: Reusable React components (AuthForm, PathSelector, useAuthState)\n- **AWS Cognito Integration**: Enterprise auth with custom attributes for user_path, sandbox_id\n- **Daytona Sandbox Provisioning**: Automated per-user sandbox creation and isolation\n- **Dual-Path Onboarding**: Personal vs Business registration flows\n- **Swiss GDPR Compliance**: Business data collection for Swiss requirements\n\n## Architecture Files\n- Frontend: /home/jarvis/projects/137docs/frontend/src/lib/auth/\n- Backend Services: /home/jarvis/projects/137docs/backend/services/\n- Documentation: /home/jarvis/projects/137docs/AUTH_MODULES.md, COGNITO_SETUP.md\n\n## Implementation Status\n✅ Modular authentication components\n✅ AWS Cognito User Pool with custom attributes\n✅ Daytona service for sandbox provisioning\n✅ Route protection and auth guards\n✅ Dual-path onboarding flow\n📋 Next: Full BETTY memory integration",
  "knowledge_type": "document",
  "source_type": "user_input",
  "project_id": null,
  "tags": ["merged-platform", "authentication", "aws-cognito", "daytona", "architecture", "137docs", "nautfinance"],
  "metadata": {
    "project_path": "/home/jarvis/projects/137docs",
    "technologies": ["React", "TypeScript", "FastAPI", "AWS Cognito", "Daytona", "PostgreSQL"],
    "status": "implemented",
    "complexity": "high"
  }
}
EOF

curl -X POST http://localhost:8001/api/knowledge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/main_project.json

if [ $? -eq 0 ]; then
    echo "✅ Main project record created"
else
    echo "❌ Failed to create main project record"
fi

# 2. AWS Cognito Implementation Pattern
echo "📊 Creating AWS Cognito implementation pattern..."
cat > /tmp/cognito_pattern.json << EOF
{
  "title": "AWS Cognito Dual-Path Authentication Pattern",
  "content": "# AWS Cognito Implementation Pattern\n\n## Pattern Overview\nEnterprise authentication with dual-path user onboarding using AWS Cognito User Pools.\n\n## Implementation Details\n- **File**: /home/jarvis/projects/137docs/backend/services/cognitoService.py (487 lines)\n- **Custom Attributes**: user_path, sandbox_id, onboarding_complete, company data\n- **Region**: eu-central-1 (Swiss compliance)\n- **Features**: Registration, verification, user management, server-side admin operations\n\n## Usage Pattern\n\`\`\`python\nfrom services.cognitoService import cognito_service, UserRegistrationData\n\n# Register user with path\nresult = await cognito_service.register_user(\n    UserRegistrationData(\n        email='user@example.com',\n        user_path='business',  # or 'personal'\n        # ... other fields\n    )\n)\n\`\`\`\n\n## Benefits\n- Enterprise-grade authentication\n- Custom attributes for business logic\n- Swiss GDPR compliance\n- Dual-path user flows\n- Server-side user management\n\n## Reusable For\n- Multi-tenant applications\n- Business/personal user segmentation\n- Swiss/EU compliance requirements\n- Enterprise authentication needs",
  "knowledge_type": "solution",
  "source_type": "user_input", 
  "project_id": null,
  "tags": ["aws-cognito", "authentication", "dual-path", "pattern", "enterprise"],
  "metadata": {
    "pattern_type": "authentication",
    "technologies": ["AWS Cognito", "Python", "FastAPI"],
    "success_rate": 1.0,
    "usage_count": 1
  }
}
EOF

curl -X POST http://localhost:8001/api/knowledge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/cognito_pattern.json

if [ $? -eq 0 ]; then
    echo "✅ AWS Cognito pattern record created"
else
    echo "❌ Failed to create Cognito pattern record"
fi

# 3. Daytona Sandbox Provisioning Pattern
echo "📊 Creating Daytona provisioning pattern..."
cat > /tmp/daytona_pattern.json << EOF
{
  "title": "Daytona Automated Sandbox Provisioning Pattern",
  "content": "# Daytona User Sandbox Provisioning\n\n## Pattern Overview\nAutomated per-user sandbox creation and management using Daytona platform.\n\n## Implementation Details\n- **File**: /home/jarvis/projects/137docs/backend/services/daytonaService.py (417 lines)\n- **Features**: Automated provisioning, template-based creation, resource management\n- **Templates**: Separate configurations for personal vs business users\n- **Region**: swiss-central (compliance)\n\n## Usage Pattern\n\`\`\`python\nfrom services.daytonaService import daytona_service\n\n# Provision sandbox for user\nsandbox = await daytona_service.provision_user_sandbox(\n    user_id=user_sub,\n    user_path='business',  # or 'personal'\n    email=user_email\n)\n\`\`\`\n\n## Template Configuration\n- **Personal**: Basic workspace with personal document features\n- **Business**: Enhanced workspace with compliance features\n- **Resources**: 2 CPU, 4Gi memory, 20Gi disk per sandbox\n- **Ports**: Frontend (3000), Backend (8000), PostgreSQL (5432), Qdrant (6333)\n\n## Benefits\n- Complete user isolation\n- Automated infrastructure provisioning\n- Template-based standardization\n- Resource management and cleanup\n- Swiss compliance (regional deployment)\n\n## Reusable For\n- Multi-tenant SaaS applications\n- User workspace isolation\n- Development environment provisioning\n- Resource management automation",
  "knowledge_type": "solution",
  "source_type": "user_input",
  "project_id": null, 
  "tags": ["daytona", "sandbox", "provisioning", "automation", "isolation"],
  "metadata": {
    "pattern_type": "infrastructure",
    "technologies": ["Daytona", "Python", "Docker"],
    "success_rate": 1.0,
    "usage_count": 1
  }
}
EOF

curl -X POST http://localhost:8001/api/knowledge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/daytona_pattern.json

if [ $? -eq 0 ]; then
    echo "✅ Daytona provisioning pattern record created"
else
    echo "❌ Failed to create Daytona pattern record"
fi

# 4. Modular Component Architecture Pattern
echo "📊 Creating modular component architecture pattern..."
cat > /tmp/modular_pattern.json << EOF
{
  "title": "React Modular Authentication Component Architecture",
  "content": "# Modular Authentication Components\n\n## Pattern Overview\nReusable, modular authentication components that prevent code duplication.\n\n## Components Created\n- **AuthForm.tsx** (88 lines): Generic form handler for all auth forms\n- **PathSelector.tsx** (65 lines): Reusable personal/business selection\n- **useAuthState.ts** (22 lines): Lightweight auth state management\n- **toast.ts** (68 lines): Consistent notification system\n\n## Directory Structure\n\`\`\`\nfrontend/src/lib/\n├── auth/\n│   ├── useAuthState.ts\n│   └── PathSelector.tsx\n├── forms/\n│   └── AuthForm.tsx\n└── notifications/\n    └── toast.ts\n\`\`\`\n\n## Usage Examples\n\`\`\`typescript\n// Reusable form for any auth operation\n<AuthForm\n  title=\"Sign In\"\n  fields={loginFields}\n  onSubmit={handleLogin}\n  submitLabel=\"Sign In\"\n/>\n\n// Path selection for onboarding\n<PathSelector\n  selectedPath={selectedPath}\n  onPathSelect={setSelectedPath}\n  showTrialInfo={true}\n/>\n\`\`\`\n\n## Benefits\n- **No Code Duplication**: One AuthForm handles all forms\n- **Consistent UX**: All auth flows look and behave the same\n- **Easy Testing**: Small, focused components\n- **Fast Development**: Reuse existing components for new features\n\n## Reusable For\n- Login/registration forms\n- Profile update forms\n- Settings pages\n- Any user input form\n- Personal/business selection flows",
  "knowledge_type": "solution",
  "source_type": "user_input",
  "project_id": null,
  "tags": ["react", "modular", "components", "authentication", "reusable"],
  "metadata": {
    "pattern_type": "frontend_architecture",
    "technologies": ["React", "TypeScript", "Tailwind CSS"],
    "success_rate": 1.0,
    "usage_count": 1
  }
}
EOF

curl -X POST http://localhost:8001/api/knowledge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/modular_pattern.json

if [ $? -eq 0 ]; then
    echo "✅ Modular component pattern record created"
else
    echo "❌ Failed to create modular pattern record"
fi

# Clean up temporary files
rm -f /tmp/main_project.json /tmp/cognito_pattern.json /tmp/daytona_pattern.json /tmp/modular_pattern.json

echo ""
echo "🎯 BETTY Integration Summary:"
echo "=========================================="
echo "✅ Main project architecture documented"
echo "✅ AWS Cognito implementation pattern stored"
echo "✅ Daytona sandbox provisioning pattern stored"  
echo "✅ Modular React component architecture stored"
echo ""
echo "📋 Next Steps:"
echo "- Verify ingestion with: curl http://localhost:8001/api/knowledge/search -d '{\"query\":\"merged platform\"}'"
echo "- Test BETTY search for 'merged platform authentication'"
echo "- Future Claude sessions will now have access to this architectural knowledge"
echo ""
echo "🚀 Integration Complete! Merged platform work is now available in BETTY memory."