// ABOUTME: Component for running sprints continuously without stopping
// ABOUTME: Feeds tasks to Claude one after another until sprint is complete

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Zap, CheckCircle, Clock, TrendingUp } from 'lucide-react';

interface Sprint {
  id: string;
  name: string;
  project_id: string;
  start_date: string;
  end_date: string;
  status: string;
}

interface ContinuousSession {
  sprintId: string;
  status: 'active' | 'completed' | 'paused';
  progress: {
    completed: number;
    total: number;
    percentage: number;
  };
  completedTasks: string[];
  currentTaskId: string | null;
}

interface Props {
  sprint: Sprint;
  onClose?: () => void;
}

const API_URL = 'https://ai-linear.blockonauts.io/api';

const ContinuousSprintRunner: React.FC<Props> = ({ sprint, onClose }) => {
  const [session, setSession] = useState<ContinuousSession | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [instructions, setInstructions] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);

  const startContinuousExecution = async () => {
    try {
      setIsRunning(true);
      const response = await axios.post(`${API_URL}/continuous/sprint/${sprint.id}/start`);
      
      if (response.data.success) {
        setInstructions(response.data.instructions);
        setLogs([
          `✅ Continuous execution started for sprint: ${sprint.name}`,
          `📋 Instructions generated and ready for Claude`,
          `🚀 Claude should now work through all tasks without stopping`
        ]);
        
        // Start polling for status
        pollStatus();
        
        // Display instructions for Claude
        displayClaudeInstructions(response.data.instructions);
      }
    } catch (error: any) {
      console.error('Failed to start continuous execution:', error);
      setIsRunning(false);
      setLogs(prev => [...prev, `❌ Error: ${error?.message || 'Failed to start'}`]);
    }
  };

  const pollStatus = async () => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/continuous/sprint/${sprint.id}/status`);
        if (response.data.success && response.data.status) {
          setSession(response.data.status);
          
          if (response.data.status.status === 'completed') {
            clearInterval(interval);
            setIsRunning(false);
            setLogs(prev => [...prev, `🎉 Sprint completed! All tasks done.`]);
          }
        }
      } catch (error) {
        console.error('Failed to poll status:', error);
      }
    }, 5000); // Poll every 5 seconds

    // Clean up on unmount
    return () => clearInterval(interval);
  };

  const displayClaudeInstructions = (instructions: string) => {
    // Create a special message box that Claude will see
    const instructionBox = document.createElement('div');
    instructionBox.id = 'claude-continuous-instructions';
    instructionBox.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      width: 500px;
      max-height: 80vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 10px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      z-index: 10000;
      overflow-y: auto;
      font-family: monospace;
    `;
    
    instructionBox.innerHTML = `
      <h2 style="margin: 0 0 10px 0; font-size: 18px;">🤖 CLAUDE: EXECUTE THIS SPRINT CONTINUOUSLY</h2>
      <pre style="white-space: pre-wrap; font-size: 12px; line-height: 1.4;">${instructions}</pre>
      <button onclick="this.parentElement.remove()" style="
        margin-top: 15px;
        padding: 8px 16px;
        background: white;
        color: #667eea;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
      ">Claude, I've started - Close this</button>
    `;
    
    document.body.appendChild(instructionBox);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          <Zap className="w-6 h-6 text-yellow-400" />
          Continuous Sprint Execution
        </h2>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            ✕
          </button>
        )}
      </div>

      <div className="bg-gray-700 rounded-lg p-4 mb-6">
        <h3 className="font-semibold mb-2">Sprint: {sprint.name}</h3>
        <p className="text-sm text-gray-400">
          This will execute ALL tasks in the sprint continuously without stopping.
          Claude will work through each task sequentially until the entire sprint is complete.
        </p>
      </div>

      {!isRunning && !session && (
        <button
          onClick={startContinuousExecution}
          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg flex items-center justify-center gap-3 transition-all transform hover:scale-105"
        >
          <Play className="w-5 h-5" />
          Start Continuous Execution
        </button>
      )}

      {isRunning && (
        <div className="space-y-4">
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Execution Progress</span>
              <span className="text-sm text-gray-400">
                {session?.progress.completed || 0} / {session?.progress.total || 0} tasks
              </span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-green-400 to-blue-500 h-3 rounded-full transition-all"
                style={{ width: `${session?.progress.percentage || 0}%` }}
              />
            </div>
          </div>

          {session?.currentTaskId && (
            <div className="bg-blue-900 bg-opacity-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-400">
                <Clock className="w-4 h-4 animate-spin" />
                <span className="text-sm font-medium">Claude is working on task:</span>
              </div>
              <p className="text-sm mt-1">{session.currentTaskId}</p>
            </div>
          )}

          <div className="bg-gray-900 rounded-lg p-4 max-h-60 overflow-y-auto">
            <h4 className="text-sm font-medium mb-2">Execution Log</h4>
            <div className="space-y-1">
              {logs.map((log, idx) => (
                <div key={idx} className="text-xs text-gray-400">
                  {log}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {session?.status === 'completed' && (
        <div className="bg-green-900 bg-opacity-50 rounded-lg p-6 text-center">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <h3 className="text-xl font-bold mb-2">Sprint Completed!</h3>
          <p className="text-gray-400">
            All {session.progress.total} tasks have been successfully executed.
          </p>
        </div>
      )}

      <div className="mt-6 p-4 bg-yellow-900 bg-opacity-30 rounded-lg">
        <p className="text-xs text-yellow-300">
          <strong>How it works:</strong> When you click "Start Continuous Execution", 
          Claude receives instructions to complete ALL tasks in this sprint without stopping. 
          Each task completion automatically triggers the next one until the entire sprint is done.
        </p>
      </div>
    </div>
  );
};

export default ContinuousSprintRunner;