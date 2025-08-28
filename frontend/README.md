# Lineary Frontend

A comprehensive React frontend for the Lineary self-driving development platform.

## Features

### 🏗️ Navigation & Layout
- Modern glassmorphism design with dark theme
- Responsive navigation with routing
- Project selector in header
- Seamless page transitions

### 📁 Project Management
- Create and manage projects with custom colors
- Project overview cards with statistics
- Auto-selection and context management
- Project documentation integration

### 📋 Enhanced Issue Management
- **Dependencies**: Link issues to other issues
- **Parent/Sub-tasks**: Create hierarchical task structures
- **Dates**: Start and end date tracking with duration calculation
- **Token Cost**: Display and edit AI token usage costs
- **Completion Scope**: Progress bars showing 0-100% completion
- **Activity Timeline**: Complete activity history for each issue
- **AI Prompt**: Generated AI prompts and analysis
- **Add to Sprint**: Quick sprint assignment buttons

### 🏃 Sprint Planning
- Create sprints with date ranges
- Sprint planning modal with issue selection
- Burndown chart visualization
- Sprint statistics (velocity, completion rate)
- Sprint progress tracking
- Sprint status management (planning, active, completed)

### 📚 Project Documentation
- Rich text editor with TipTap
- Four documentation sections:
  - **Overview**: Project goals and summary
  - **Architecture**: System design and structure
  - **Requirements**: Functional and technical specs
  - **API**: Endpoint documentation
- Auto-save functionality
- Export and sharing options
- AI-assisted content generation

### 📊 Analytics Dashboard
- **Velocity Chart**: Story points over time with planned vs completed
- **Cycle Time Chart**: Average cycle time and lead time trends
- **Token Usage Chart**: AI token consumption and costs
- **Status Distribution**: Pie chart of issue statuses
- **Priority Distribution**: Issue priority breakdown
- **Burndown Charts**: Sprint progress visualization
- **AI Insights**: Automated recommendations and alerts

## Technical Features

### 🎨 Design System
- Dark theme with glassmorphism effects
- Tailwind CSS for styling
- Consistent component library
- Responsive grid layouts
- Smooth animations and transitions

### 🔧 State Management
- React Router for navigation
- Axios for API communication
- React Hot Toast for notifications
- Form state management
- Error handling and loading states

### 📈 Data Visualization
- Recharts for all charts and graphs
- Interactive tooltips and legends
- Responsive chart containers
- Custom styling for dark theme
- Real-time data updates

### ✨ User Experience
- Loading skeletons
- Error boundaries
- Optimistic updates
- Keyboard shortcuts
- Accessibility features
- Mobile-responsive design

## API Integration

The frontend integrates with the following API endpoints:

### Projects
- `GET/POST /api/projects`
- `GET/POST /api/projects/:id/documentation`

### Issues
- `GET/POST /api/issues`
- `PATCH /api/issues/:id`
- `GET/POST /api/issues/:id/activities`
- `GET /api/issues/:id/subtasks`

### Sprints
- `GET/POST /api/sprints`
- `GET /api/sprints/planning/issues`
- `POST /api/sprints/:id/issues`
- `GET /api/sprints/:id/burndown`

### Analytics
- `GET /api/analytics/velocity`
- `GET /api/analytics/cycle-time`
- `GET /api/analytics/token-usage`

### AI Features
- `GET /api/prompts/templates`
- `POST /api/prompts/generate`

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

## Environment

- React 18.2.0
- TypeScript 5.9.2
- Vite 4.5.14
- Tailwind CSS 3.3.5
- React Router 6.20.1

## Architecture

The application follows a modern React architecture with:

- **Component-based structure**: Reusable UI components
- **Page-based routing**: Separate pages for each major feature
- **Service layer**: API communication abstraction
- **Type safety**: Full TypeScript integration
- **Performance optimization**: Code splitting and lazy loading

## Components

### Pages
- `ProjectsPage`: Project overview and management
- `IssuesPage`: Issue listing and filtering
- `SprintsPage`: Sprint planning and management
- `AnalyticsPage`: Charts and metrics dashboard
- `ProjectDocumentationPage`: Rich text documentation editor

### Components
- `IssueModal`: Comprehensive issue creation/editing
- `ActivityTimeline`: Issue activity history
- `RichTextEditor`: TipTap-based rich text editing
- `Navigation`: Main navigation component

The frontend is production-ready with comprehensive error handling, loading states, and responsive design optimized for the Lineary development platform.