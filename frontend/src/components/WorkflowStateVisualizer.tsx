// Testing PostTool hooks v1
import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  Code,
  CheckCircle,
  Upload,
  TestTube,
  GitMerge,
  Archive,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight,
  Play,
  Pause
} from 'lucide-react';

interface WorkflowState {
  name: string;
  label: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  description: string;
  actions: string[];
}

const WORKFLOW_STATES: WorkflowState[] = [
  {
    name: 'planning',
    label: 'Planning',
    icon: GitBranch,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    description: 'Defining requirements and breaking down tasks',
    actions: ['Create branch', 'Define acceptance criteria']
  },
  {
    name: 'implementing',
    label: 'Implementing',
    icon: Code,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    description: 'Writing code and implementing features',
    actions: ['Write code', 'Run local tests']
  },
  {
    name: 'validating',
    label: 'Validating',
    icon: CheckCircle,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    description: 'Code review and validation checks',
    actions: ['Code review', 'Validate requirements']
  },
  {
    name: 'pushing',
    label: 'Pushing',
    icon: Upload,
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    description: 'Pushing changes to remote repository',
    actions: ['Push to branch', 'Create PR']
  },
  {
    name: 'testing',
    label: 'Testing',
    icon: TestTube,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/20',
    description: 'Running automated tests and QA',
    actions: ['Run CI/CD', 'QA testing']
  },
  {
    name: 'merging',
    label: 'Merging',
    icon: GitMerge,
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    description: 'Merging to main branch',
    actions: ['Merge PR', 'Deploy to production']
  },
  {
    name: 'closing',
    label: 'Closing',
    icon: Archive,
    color: 'text-gray-400',
    bgColor: 'bg-gray-500/20',
    description: 'Cleanup and documentation',
    actions: ['Close ticket', 'Update docs']
  },
  {
    name: 'done',
    label: 'Done',
    icon: CheckCircle2,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/20',
    description: 'Task completed successfully',
    actions: ['Archive branch', 'Celebrate!']
  }
];

interface Task {
  id: string;
  task: string;
  current_state: string;
  story_points?: number;
  estimated_hours?: number;
  branch_name?: string;
}

interface WorkflowStateVisualizerProps {
  tasks?: Task[];
  onStateChange?: (taskId: string, newState: string) => void;
}

const WorkflowStateVisualizer: React.FC<WorkflowStateVisualizerProps> = ({ 
  tasks = [], 
  onStateChange 
}) => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [tasksInStates, setTasksInStates] = useState<Record<string, Task[]>>({});
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    // Group tasks by state
    const grouped: Record<string, Task[]> = {};
    WORKFLOW_STATES.forEach(state => {
      grouped[state.name] = [];
    });
    
    tasks.forEach(task => {
      const state = task.current_state || 'planning';
      if (grouped[state]) {
        grouped[state].push(task);
      }
    });
    
    setTasksInStates(grouped);
  }, [tasks]);

  const handleStateTransition = async (taskId: string, newState: string) => {
    setIsTransitioning(true);
    
    try {
      // Call API to update task state
      const response = await fetch(`http://localhost:3034/api/enhanced-tasks/${taskId}/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          state: newState,
          notes: `Transitioned to ${newState}`,
          metadata: { timestamp: new Date().toISOString() }
        })
      });
      
      if (response.ok && onStateChange) {
        onStateChange(taskId, newState);
      }
    } catch (error) {
      console.error('Failed to update task state:', error);
    } finally {
      setIsTransitioning(false);
    }
  };

  const canTransition = (currentState: string, targetState: string): boolean => {
    const currentIndex = WORKFLOW_STATES.findIndex(s => s.name === currentState);
    const targetIndex = WORKFLOW_STATES.findIndex(s => s.name === targetState);
    
    // Can move forward one step or back to any previous state
    return targetIndex === currentIndex + 1 || targetIndex < currentIndex;
  };

  return (
    <div className="space-y-6">
      {/* Pipeline View */}
      <div className="bg-gray-900 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-blue-400" />
          Workflow Pipeline
        </h3>
        
        <div className="relative">
          {/* Connection Line */}
          <div className="absolute top-16 left-0 right-0 h-0.5 bg-gray-700" />
          
          {/* States */}
          <div className="grid grid-cols-4 lg:grid-cols-8 gap-4 relative">
            {WORKFLOW_STATES.map((state, index) => {
              const Icon = state.icon;
              const taskCount = tasksInStates[state.name]?.length || 0;
              
              return (
                <div key={state.name} className="relative group">
                  {/* State Node */}
                  <div className={`${state.bgColor} rounded-lg p-4 border-2 border-gray-700 hover:border-gray-600 transition-all cursor-pointer`}>
                    <div className="flex flex-col items-center">
                      <Icon className={`w-8 h-8 ${state.color} mb-2`} />
                      <span className="text-xs text-gray-300 font-medium">
                        {state.label}
                      </span>
                      {taskCount > 0 && (
                        <span className="mt-2 bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                          {taskCount}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                    <div className="bg-gray-800 text-white p-3 rounded-lg shadow-lg w-48">
                      <div className="text-sm font-medium mb-1">{state.label}</div>
                      <div className="text-xs text-gray-400 mb-2">{state.description}</div>
                      <div className="text-xs space-y-1">
                        {state.actions.map((action, i) => (
                          <div key={i} className="flex items-center gap-1">
                            <span className="text-blue-400">•</span>
                            {action}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {/* Arrow */}
                  {index < WORKFLOW_STATES.length - 1 && (
                    <ArrowRight className="absolute -right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-600" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tasks by State */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4">
        {WORKFLOW_STATES.map(state => {
          const Icon = state.icon;
          const stateTasks = tasksInStates[state.name] || [];
          
          return (
            <div key={state.name} className="bg-gray-900 rounded-xl p-4">
              <div className={`flex items-center gap-2 mb-3 pb-2 border-b border-gray-800`}>
                <Icon className={`w-5 h-5 ${state.color}`} />
                <h4 className="text-sm font-medium text-white">{state.label}</h4>
                <span className="ml-auto text-xs text-gray-500">
                  {stateTasks.length} tasks
                </span>
              </div>
              
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {stateTasks.length === 0 ? (
                  <div className="text-xs text-gray-600 text-center py-4">
                    No tasks in this state
                  </div>
                ) : (
                  stateTasks.map(task => (
                    <div
                      key={task.id}
                      onClick={() => setSelectedTask(task)}
                      className={`p-2 bg-gray-800 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors ${
                        selectedTask?.id === task.id ? 'ring-2 ring-blue-500' : ''
                      }`}
                    >
                      <div className="text-xs text-white truncate">
                        {task.task}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {task.story_points && (
                          <span className="text-xs text-gray-500">
                            {task.story_points} pts
                          </span>
                        )}
                        {task.estimated_hours && (
                          <span className="text-xs text-gray-500">
                            {task.estimated_hours}h
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Task Transition Panel */}
      {selectedTask && (
        <div className="bg-gray-900 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-4">
            Transition Task: {selectedTask.task}
          </h4>
          
          <div className="flex items-center gap-4 mb-4">
            <div className="text-sm text-gray-400">
              Current State:
            </div>
            <div className="flex items-center gap-2">
              {(() => {
                const currentState = WORKFLOW_STATES.find(s => s.name === selectedTask.current_state);
                const Icon = currentState?.icon || Clock;
                return (
                  <>
                    <Icon className={`w-4 h-4 ${currentState?.color}`} />
                    <span className="text-white font-medium">
                      {currentState?.label || 'Unknown'}
                    </span>
                  </>
                );
              })()}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {WORKFLOW_STATES.map(state => {
              const canMove = canTransition(selectedTask.current_state, state.name);
              const isCurrent = state.name === selectedTask.current_state;
              
              return (
                <button
                  key={state.name}
                  disabled={!canMove || isCurrent || isTransitioning}
                  onClick={() => handleStateTransition(selectedTask.id, state.name)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isCurrent
                      ? 'bg-blue-600 text-white cursor-default'
                      : canMove
                      ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                      : 'bg-gray-800/50 text-gray-600 cursor-not-allowed'
                  }`}
                >
                  {isTransitioning && canMove && !isCurrent ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  ) : (
                    <>
                      {state.label}
                      {isCurrent && ' (Current)'}
                    </>
                  )}
                </button>
              );
            })}
          </div>
          
          {selectedTask.branch_name && (
            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <div className="flex items-center gap-2 text-sm">
                <GitBranch className="w-4 h-4 text-blue-400" />
                <span className="text-gray-400">Branch:</span>
                <code className="text-blue-300 font-mono">
                  {selectedTask.branch_name}
                </code>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkflowStateVisualizer;