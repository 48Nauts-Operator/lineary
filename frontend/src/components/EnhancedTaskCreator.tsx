import React, { useState } from 'react';
import { 
  Plus, 
  Zap, 
  GitBranch, 
  Clock, 
  DollarSign,
  AlertCircle,
  CheckCircle,
  Hash,
  Target,
  Code,
  Database,
  Layers,
  FileQuestion
} from 'lucide-react';

interface TaskCreatorProps {
  onTaskCreated: (task: any) => void;
}

const EnhancedTaskCreator: React.FC<TaskCreatorProps> = ({ onTaskCreated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [taskData, setTaskData] = useState({
    task: '',
    description: '',
    acceptanceCriteria: [''],
    technicalNotes: '',
    dependencies: [''],
    priority: 3,
    enableGit: true,
    autoEstimate: true
  });
  
  const [estimation, setEstimation] = useState<any>(null);
  const [isEstimating, setIsEstimating] = useState(false);

  const complexityFactors = {
    code_footprint: { icon: Code, label: 'Code Complexity', color: 'blue' },
    integration_depth: { icon: Layers, label: 'Integration Depth', color: 'purple' },
    test_complexity: { icon: CheckCircle, label: 'Test Complexity', color: 'green' },
    uncertainty: { icon: FileQuestion, label: 'Uncertainty', color: 'yellow' },
    data_volume: { icon: Database, label: 'Data Volume', color: 'indigo' }
  };

  const fibonacciPoints = [1, 2, 3, 5, 8, 13];

  const handleEstimate = async () => {
    setIsEstimating(true);
    
    try {
      const response = await fetch('http://localhost:3034/api/enhanced-tasks/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskData.task,
          description: {
            description: taskData.description,
            acceptance_criteria: taskData.acceptanceCriteria.filter(c => c),
            technical_notes: taskData.technicalNotes,
            dependencies: taskData.dependencies.filter(d => d)
          }
        })
      });
      
      const estimate = await response.json();
      setEstimation(estimate);
    } catch (error) {
      console.error('Estimation failed:', error);
    } finally {
      setIsEstimating(false);
    }
  };

  const handleCreate = async () => {
    try {
      const response = await fetch('http://localhost:3034/api/enhanced-tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskData.task,
          priority: taskData.priority,
          description: {
            description: taskData.description,
            acceptance_criteria: taskData.acceptanceCriteria.filter(c => c),
            technical_notes: taskData.technicalNotes,
            dependencies: taskData.dependencies.filter(d => d)
          },
          sprint_estimate: estimation,
          git_integration: taskData.enableGit ? {} : null,
          initial_state: 'planning'
        })
      });
      
      const newTask = await response.json();
      onTaskCreated(newTask);
      
      // Reset form
      setTaskData({
        task: '',
        description: '',
        acceptanceCriteria: [''],
        technicalNotes: '',
        dependencies: [''],
        priority: 3,
        enableGit: true,
        autoEstimate: true
      });
      setEstimation(null);
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-full shadow-lg hover:scale-110 transition-transform"
      >
        <Plus className="w-6 h-6" />
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-6">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <Zap className="w-8 h-8 text-yellow-400" />
                Create Enhanced Task with AI Sprint Poker
              </h2>
            </div>

            <div className="p-6 space-y-6">
              {/* Task Title */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Task Title
                </label>
                <input
                  type="text"
                  value={taskData.task}
                  onChange={(e) => setTaskData({...taskData, task: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                  placeholder="e.g., Implement user authentication with OAuth2"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Description
                </label>
                <textarea
                  value={taskData.description}
                  onChange={(e) => setTaskData({...taskData, description: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white h-24"
                  placeholder="Detailed description of what needs to be done..."
                />
              </div>

              {/* Acceptance Criteria */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Acceptance Criteria
                </label>
                {taskData.acceptanceCriteria.map((criteria, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={criteria}
                      onChange={(e) => {
                        const newCriteria = [...taskData.acceptanceCriteria];
                        newCriteria[index] = e.target.value;
                        setTaskData({...taskData, acceptanceCriteria: newCriteria});
                      }}
                      className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                      placeholder="e.g., Users can login with Google account"
                    />
                    {index === taskData.acceptanceCriteria.length - 1 && (
                      <button
                        onClick={() => setTaskData({
                          ...taskData, 
                          acceptanceCriteria: [...taskData.acceptanceCriteria, '']
                        })}
                        className="px-3 py-2 bg-blue-600 rounded-lg hover:bg-blue-700"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Priority & Options */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Priority
                  </label>
                  <select
                    value={taskData.priority}
                    onChange={(e) => setTaskData({...taskData, priority: parseInt(e.target.value)})}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                  >
                    <option value="1">P1 - Critical</option>
                    <option value="2">P2 - High</option>
                    <option value="3">P3 - Medium</option>
                    <option value="4">P4 - Low</option>
                  </select>
                </div>

                <label className="flex items-center gap-2 text-gray-400">
                  <input
                    type="checkbox"
                    checked={taskData.enableGit}
                    onChange={(e) => setTaskData({...taskData, enableGit: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <GitBranch className="w-4 h-4" />
                  <span>Create Git Branch</span>
                </label>

                <label className="flex items-center gap-2 text-gray-400">
                  <input
                    type="checkbox"
                    checked={taskData.autoEstimate}
                    onChange={(e) => setTaskData({...taskData, autoEstimate: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <Zap className="w-4 h-4" />
                  <span>Auto-Estimate</span>
                </label>
              </div>

              {/* AI Estimation Button */}
              <div className="flex justify-center">
                <button
                  onClick={handleEstimate}
                  disabled={!taskData.task || !taskData.description || isEstimating}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-medium disabled:opacity-50 flex items-center gap-2"
                >
                  {isEstimating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                      Estimating...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Get AI Sprint Poker Estimate
                    </>
                  )}
                </button>
              </div>

              {/* Estimation Results */}
              {estimation && (
                <div className="bg-gray-800 rounded-xl p-6 space-y-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Target className="w-5 h-5 text-green-400" />
                    Sprint Poker Estimation Results
                  </h3>

                  {/* Story Points */}
                  <div className="flex items-center justify-center gap-4">
                    {fibonacciPoints.map(point => (
                      <div
                        key={point}
                        className={`w-16 h-16 rounded-lg flex items-center justify-center text-2xl font-bold transition-all ${
                          estimation.story_points === point
                            ? 'bg-blue-600 text-white scale-110'
                            : 'bg-gray-700 text-gray-400'
                        }`}
                      >
                        {point}
                      </div>
                    ))}
                  </div>

                  {/* Complexity Breakdown */}
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(estimation.analysis_factors?.scores || {}).map(([factor, score]) => {
                      const config = complexityFactors[factor as keyof typeof complexityFactors];
                      if (!config) return null;
                      const Icon = config.icon;
                      
                      return (
                        <div key={factor} className="flex items-center gap-3">
                          <Icon className={`w-5 h-5 text-${config.color}-400`} />
                          <div className="flex-1">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-400">{config.label}</span>
                              <span className="text-white font-medium">{(score as any)}/13</span>
                            </div>
                            <div className="bg-gray-700 rounded-full h-2 mt-1">
                              <div
                                className={`bg-${config.color}-500 h-2 rounded-full`}
                                style={{ width: `${(Number(score) / 13) * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Estimates */}
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-gray-700 rounded-lg p-3">
                      <Clock className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                      <div className="text-xl font-bold text-white">
                        {estimation.estimated_hours}h
                      </div>
                      <div className="text-xs text-gray-400">Estimated Time</div>
                    </div>

                    <div className="bg-gray-700 rounded-lg p-3">
                      <Hash className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                      <div className="text-xl font-bold text-white">
                        {(estimation.estimated_tokens / 1000).toFixed(1)}k
                      </div>
                      <div className="text-xs text-gray-400">Tokens</div>
                    </div>

                    <div className="bg-gray-700 rounded-lg p-3">
                      <DollarSign className="w-5 h-5 text-green-400 mx-auto mb-1" />
                      <div className="text-xl font-bold text-white">
                        ${estimation.estimated_cost.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-400">Est. Cost</div>
                    </div>
                  </div>

                  {/* Confidence Level */}
                  <div className="flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-400" />
                    <div className="flex-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Confidence Level</span>
                        <span className="text-white font-medium">
                          {(estimation.confidence_level * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="bg-gray-700 rounded-full h-2 mt-1">
                        <div
                          className="bg-yellow-500 h-2 rounded-full"
                          style={{ width: `${estimation.confidence_level * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Optimization Suggestions */}
                  {estimation.optimization_suggestions?.length > 0 && (
                    <div className="bg-gray-700 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-2">
                        Optimization Suggestions
                      </h4>
                      <ul className="space-y-1">
                        {estimation.optimization_suggestions.map((suggestion: string, i: number) => (
                          <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-blue-400">•</span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-6 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!taskData.task || !taskData.description}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Create Enhanced Task
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default EnhancedTaskCreator;