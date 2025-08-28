// ABOUTME: Sprint creation component with ticket selection and AI estimations
// ABOUTME: Shows predicted time and token costs for selected tickets

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, Zap, DollarSign, AlertCircle, Check, ChevronDown } from 'lucide-react';

interface Issue {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: number;
  story_points: number;
  estimated_minutes?: number;
  token_cost?: number;
  ai_confidence?: number;
  tags?: string[];
}

interface Project {
  id: string;
  name: string;
  color: string;
}

interface Props {
  projects: Project[];
  onSprintCreated: () => void;
  onClose: () => void;
}

const API_URL = 'https://ai-linear.blockonauts.io/api';

const SprintCreator: React.FC<Props> = ({ projects, onSprintCreated, onClose }) => {
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [sprintName, setSprintName] = useState('');
  const [startDateTime, setStartDateTime] = useState('');
  const [availableIssues, setAvailableIssues] = useState<Issue[]>([]);
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (selectedProject) {
      fetchProjectIssues(selectedProject);
    }
  }, [selectedProject]);

  const fetchProjectIssues = async (projectId: string) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/issues?project_id=${projectId}`);
      const issues = response.data.filter((i: Issue) => 
        i.status === 'todo' || i.status === 'backlog'
      );
      
      // Estimate tokens for issues that don't have estimates
      const enrichedIssues = await Promise.all(
        issues.map(async (issue: Issue) => {
          if (!issue.token_cost) {
            try {
              const estimateResponse = await axios.post(
                `${API_URL}/issues/${issue.id}/estimate-tokens`
              );
              return {
                ...issue,
                ...estimateResponse.data
              };
            } catch (error) {
              console.error(`Failed to estimate tokens for issue ${issue.id}`);
              return issue;
            }
          }
          return issue;
        })
      );
      
      setAvailableIssues(enrichedIssues);
    } catch (error) {
      console.error('Failed to fetch issues:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleIssue = (issueId: string) => {
    setSelectedIssues(prev => 
      prev.includes(issueId) 
        ? prev.filter(id => id !== issueId)
        : [...prev, issueId]
    );
  };

  const selectAll = () => {
    setSelectedIssues(availableIssues.map(i => i.id));
  };

  const deselectAll = () => {
    setSelectedIssues([]);
  };

  const calculateTotals = () => {
    const selected = availableIssues.filter(i => selectedIssues.includes(i.id));
    
    const totalMinutes = selected.reduce((sum, i) => sum + (i.estimated_minutes || 0), 0);
    const totalTokens = selected.reduce((sum, i) => sum + (i.token_cost || 0), 0);
    const avgConfidence = selected.length > 0 
      ? selected.reduce((sum, i) => sum + (i.ai_confidence || 0), 0) / selected.length
      : 0;
    
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    
    // Rough cost estimate (GPT-4 pricing approximation)
    const estimatedCost = (totalTokens / 1000) * 0.03; // $0.03 per 1K tokens
    
    return {
      totalMinutes,
      timeString: `${hours}h ${minutes}m`,
      totalTokens,
      estimatedCost: estimatedCost.toFixed(2),
      avgConfidence: (avgConfidence * 100).toFixed(0)
    };
  };

  const createSprint = async () => {
    if (!sprintName || selectedIssues.length === 0) {
      alert('Please provide a sprint name and select at least one issue');
      return;
    }

    setCreating(true);
    try {
      // Create sprint without end date
      const sprintData = {
        name: sprintName,
        project_id: selectedProject,
        start_date: startDateTime || new Date().toISOString(),
        duration_hours: 8, // Default sprint duration
        issue_ids: selectedIssues
      };

      const response = await axios.post(`${API_URL}/sprints`, sprintData);
      
      if (response.data) {
        // Add issues to sprint
        await axios.post(`${API_URL}/sprints/${response.data.id}/issues`, {
          issue_ids: selectedIssues
        });
        
        onSprintCreated();
        onClose();
      }
    } catch (error) {
      console.error('Failed to create sprint:', error);
      alert('Failed to create sprint. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden border border-gray-700">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Create Continuous Execution Sprint</h2>
          <p className="text-gray-400 text-sm mt-1">
            Select tickets to run continuously until completion
          </p>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Sprint Configuration */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Sprint Name *
              </label>
              <input
                type="text"
                value={sprintName}
                onChange={(e) => setSprintName(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="e.g., Feature Sprint #1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project *
              </label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
              >
                <option value="">Select a project</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Start Date & Time (Optional - leave empty to start immediately)
            </label>
            <input
              type="datetime-local"
              value={startDateTime}
              onChange={(e) => setStartDateTime(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Ticket Selection */}
          {selectedProject && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  Select Tickets ({selectedIssues.length} selected)
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={selectAll}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                  >
                    Select All
                  </button>
                  <button
                    onClick={deselectAll}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                  >
                    Clear
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-8 text-gray-400">
                  Loading issues...
                </div>
              ) : availableIssues.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  No available issues in this project
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {availableIssues.map(issue => (
                    <div
                      key={issue.id}
                      onClick={() => toggleIssue(issue.id)}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedIssues.includes(issue.id)
                          ? 'bg-purple-900/30 border-purple-500'
                          : 'bg-gray-700/50 border-gray-600 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-5 h-5 rounded border-2 mt-0.5 flex items-center justify-center ${
                          selectedIssues.includes(issue.id)
                            ? 'bg-purple-500 border-purple-500'
                            : 'border-gray-400'
                        }`}>
                          {selectedIssues.includes(issue.id) && (
                            <Check className="w-3 h-3 text-white" />
                          )}
                        </div>
                        
                        <div className="flex-1">
                          <h4 className="font-medium text-white">{issue.title}</h4>
                          {issue.description && (
                            <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                              {issue.description}
                            </p>
                          )}
                          
                          <div className="flex items-center gap-4 mt-2 text-xs">
                            <div className="flex items-center gap-1 text-blue-400">
                              <Clock className="w-3 h-3" />
                              <span>~{Math.round((issue.estimated_minutes || 0) / 60)}h {(issue.estimated_minutes || 0) % 60}m</span>
                            </div>
                            
                            <div className="flex items-center gap-1 text-green-400">
                              <Zap className="w-3 h-3" />
                              <span>{((issue.token_cost || 0) / 1000).toFixed(0)}k tokens</span>
                            </div>
                            
                            <div className={`flex items-center gap-1 ${
                              (issue.ai_confidence || 0) > 0.8 ? 'text-green-400' : 
                              (issue.ai_confidence || 0) > 0.6 ? 'text-yellow-400' : 'text-orange-400'
                            }`}>
                              <AlertCircle className="w-3 h-3" />
                              <span>{((issue.ai_confidence || 0) * 100).toFixed(0)}% confidence</span>
                            </div>
                            
                            <div className="flex items-center gap-1 text-gray-400">
                              <span>{issue.story_points || 0} pts</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Summary Footer */}
        <div className="p-6 border-t border-gray-700 bg-gray-900/50">
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-xs text-gray-400 mb-1">Total Time</p>
              <p className="text-xl font-bold text-white">{totals.timeString}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Token Usage</p>
              <p className="text-xl font-bold text-white">{(totals.totalTokens / 1000).toFixed(0)}k</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Est. Cost</p>
              <p className="text-xl font-bold text-green-400">${totals.estimatedCost}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">AI Confidence</p>
              <p className="text-xl font-bold text-blue-400">{totals.avgConfidence}%</p>
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-medium"
            >
              Cancel
            </button>
            
            <button
              onClick={createSprint}
              disabled={!sprintName || selectedIssues.length === 0 || creating}
              className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 rounded-lg text-white font-medium flex items-center gap-2 disabled:cursor-not-allowed"
            >
              {creating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Create Sprint for Continuous Execution
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SprintCreator;