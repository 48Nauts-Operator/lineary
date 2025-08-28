// ABOUTME: Admin dashboard for managing Betty system configuration and API keys
// ABOUTME: Secure interface for storing and updating sensitive configuration

import React, { useState, useEffect } from 'react';
import { Save, Key, AlertTriangle, Check, Eye, EyeOff, RefreshCw, TestTube, Terminal, Shield, Play, AlertCircle, Clock, Settings, ListChecks, BarChart3 } from 'lucide-react';
import TaskManagementDashboard from './TaskManagementDashboard';

interface ApiConfig {
  anthropic_api_key: string;
  elevenlabs_api_key: string;
  betty_voice_id: string;
  openai_api_key?: string;
  betty_guardian_enabled: boolean;
  betty_voice_enabled: boolean;
}

interface CommandHistoryItem {
  id: string;
  command: string;
  tool: string;
  validationResult: 'approved' | 'blocked' | 'warning' | 'pending';
  timestamp: Date;
  output?: string;
  error?: string;
}

interface ValidationResult {
  status: 'approved' | 'blocked' | 'warning';
  reason: string;
  recommendations?: string[];
  validation_token?: string;
  expires_at?: string;
}

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'config' | 'tasks' | 'analytics'>('config');
  const [config, setConfig] = useState<ApiConfig>({
    anthropic_api_key: '',
    elevenlabs_api_key: '',
    betty_voice_id: '',
    openai_api_key: '',
    betty_guardian_enabled: false,
    betty_voice_enabled: false
  });

  const [showKeys, setShowKeys] = useState<{[key: string]: boolean}>({
    anthropic: false,
    elevenlabs: false,
    openai: false
  });

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [testResults, setTestResults] = useState<{[key: string]: string}>({});
  const [loading, setLoading] = useState(true);

  // Command execution state
  const [commandInput, setCommandInput] = useState('');
  const [selectedTool, setSelectedTool] = useState('Bash');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [commandOutput, setCommandOutput] = useState<string>('');
  const [commandHistory, setCommandHistory] = useState<CommandHistoryItem[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/admin/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  // Command execution functions
  const validateCommand = async () => {
    if (!commandInput.trim()) {
      setValidationResult({
        status: 'blocked',
        reason: 'Command cannot be empty'
      });
      return;
    }

    setIsValidating(true);
    setValidationResult(null);

    try {
      const response = await fetch('/api/admin/validate-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: commandInput,
          tool: selectedTool
        })
      });

      if (response.ok) {
        const result = await response.json();
        setValidationResult({
          status: result.decision === 'approve' ? 'approved' : 
                  result.decision === 'block' ? 'blocked' : 'warning',
          reason: result.reason,
          recommendations: result.recommendations
        });
      } else {
        setValidationResult({
          status: 'blocked',
          reason: 'Validation service unavailable'
        });
      }
    } catch (error) {
      console.error('Validation failed:', error);
      setValidationResult({
        status: 'blocked',
        reason: 'Network error during validation'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const executeCommand = async () => {
    if (!validationResult || validationResult.status !== 'approved') {
      return;
    }

    setIsExecuting(true);
    setCommandOutput('');

    try {
      const response = await fetch('/api/admin/execute-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: commandInput,
          tool: selectedTool,
          validation_token: validationResult?.validation_token || ''
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        setCommandOutput(result.output || 'Command executed successfully');
        addToHistory('approved', result.output, result.error);
      } else {
        setCommandOutput(`Error: ${result.error || 'Execution failed'}`);
        addToHistory('blocked', '', result.error);
      }
    } catch (error) {
      const errorMsg = `Network error: ${error}`;
      setCommandOutput(errorMsg);
      addToHistory('blocked', '', errorMsg);
    } finally {
      setIsExecuting(false);
    }
  };

  const addToHistory = (status: CommandHistoryItem['validationResult'], output?: string, error?: string) => {
    const newItem: CommandHistoryItem = {
      id: Date.now().toString(),
      command: commandInput,
      tool: selectedTool,
      validationResult: status,
      timestamp: new Date(),
      output,
      error
    };

    setCommandHistory(prev => [newItem, ...prev.slice(0, 9)]); // Keep last 10 items
  };

  const clearCommandForm = () => {
    setCommandInput('');
    setValidationResult(null);
    setCommandOutput('');
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      const response = await fetch('/api/admin/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 3000);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      setSaveStatus('error');
    }
  };

  const testApiKey = async (service: string) => {
    setTestResults({ ...testResults, [service]: 'testing...' });
    
    try {
      const response = await fetch(`/api/admin/test-api/${service}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          key: service === 'anthropic' ? config.anthropic_api_key :
               service === 'elevenlabs' ? config.elevenlabs_api_key :
               config.openai_api_key
        })
      });

      const result = await response.json();
      setTestResults({ 
        ...testResults, 
        [service]: result.success ? '✅ Valid' : `❌ ${result.error}` 
      });
    } catch (error) {
      setTestResults({ ...testResults, [service]: '❌ Test failed' });
    }
  };

  const maskKey = (key: string) => {
    if (!key) return '';
    if (key.length <= 10) return '••••••••';
    return `${key.substring(0, 10)}...${key.substring(key.length - 4)}`;
  };

  if (loading) {
    return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-white">Loading configuration...</div>
        </div>
    );
  }

  return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Betty Admin Dashboard</h1>
          <p className="text-white/70 text-lg">
            Manage system configuration, tasks, and analytics
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-6 bg-white/5 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('config')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              activeTab === 'config'
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <Settings className="w-4 h-4" />
            Configuration
          </button>
          <button
            onClick={() => setActiveTab('tasks')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              activeTab === 'tasks'
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <ListChecks className="w-4 h-4" />
            Task Management
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              activeTab === 'analytics'
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Analytics
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'config' && (
          <>
        {/* Security Warning */}
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-8">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-yellow-500" size={24} />
            <div className="text-yellow-200">
              <strong>Security Notice:</strong> API keys are stored encrypted in the database. 
              Never share these keys or commit them to version control.
            </div>
          </div>
        </div>

        {/* API Keys Section */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-6 flex items-center gap-3">
            <Key size={24} />
            API Keys Configuration
          </h2>

          <div className="space-y-6">
            {/* Anthropic API Key */}
            <div>
              <label className="block text-white/70 mb-2">
                Anthropic API Key (Claude)
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showKeys.anthropic ? 'text' : 'password'}
                    value={config.anthropic_api_key}
                    onChange={(e) => setConfig({ ...config, anthropic_api_key: e.target.value })}
                    className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white"
                    placeholder="sk-ant-api03-..."
                  />
                  <button
                    onClick={() => setShowKeys({ ...showKeys, anthropic: !showKeys.anthropic })}
                    className="absolute right-3 top-3 text-white/50 hover:text-white"
                  >
                    {showKeys.anthropic ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                <button
                  onClick={() => testApiKey('anthropic')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white flex items-center gap-2"
                >
                  <TestTube size={18} />
                  Test
                </button>
              </div>
              {testResults.anthropic && (
                <div className="mt-2 text-sm">{testResults.anthropic}</div>
              )}
            </div>

            {/* ElevenLabs API Key */}
            <div>
              <label className="block text-white/70 mb-2">
                ElevenLabs API Key (Voice)
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showKeys.elevenlabs ? 'text' : 'password'}
                    value={config.elevenlabs_api_key}
                    onChange={(e) => setConfig({ ...config, elevenlabs_api_key: e.target.value })}
                    className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white"
                    placeholder="sk_..."
                  />
                  <button
                    onClick={() => setShowKeys({ ...showKeys, elevenlabs: !showKeys.elevenlabs })}
                    className="absolute right-3 top-3 text-white/50 hover:text-white"
                  >
                    {showKeys.elevenlabs ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                <button
                  onClick={() => testApiKey('elevenlabs')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white flex items-center gap-2"
                >
                  <TestTube size={18} />
                  Test
                </button>
              </div>
              {testResults.elevenlabs && (
                <div className="mt-2 text-sm">{testResults.elevenlabs}</div>
              )}
            </div>

            {/* Betty Voice ID */}
            <div>
              <label className="block text-white/70 mb-2">
                ElevenLabs Voice ID (Your Jarvis Voice)
              </label>
              <input
                type="text"
                value={config.betty_voice_id}
                onChange={(e) => setConfig({ ...config, betty_voice_id: e.target.value })}
                className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white"
                placeholder="5sAejp8aFDtW5UwYcdWG"
              />
              <p className="text-white/50 text-sm mt-1">
                Voice ID for your preferred Jarvis voice
              </p>
            </div>

            {/* OpenAI API Key (Optional) */}
            <div>
              <label className="block text-white/70 mb-2">
                OpenAI API Key (Optional - for Orchestrator)
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showKeys.openai ? 'text' : 'password'}
                    value={config.openai_api_key || ''}
                    onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value })}
                    className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white"
                    placeholder="sk-..."
                  />
                  <button
                    onClick={() => setShowKeys({ ...showKeys, openai: !showKeys.openai })}
                    className="absolute right-3 top-3 text-white/50 hover:text-white"
                  >
                    {showKeys.openai ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                <button
                  onClick={() => testApiKey('openai')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white flex items-center gap-2"
                >
                  <TestTube size={18} />
                  Test
                </button>
              </div>
              {testResults.openai && (
                <div className="mt-2 text-sm">{testResults.openai}</div>
              )}
            </div>
          </div>
        </div>

        {/* Services Configuration */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-6">
            Services Configuration
          </h2>

          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.betty_guardian_enabled}
                onChange={(e) => setConfig({ ...config, betty_guardian_enabled: e.target.checked })}
                className="w-5 h-5 rounded border-white/20 bg-white/5 text-blue-600"
              />
              <span className="text-white">Enable Betty Guardian (Memory-aware gateway)</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.betty_voice_enabled}
                onChange={(e) => setConfig({ ...config, betty_voice_enabled: e.target.checked })}
                className="w-5 h-5 rounded border-white/20 bg-white/5 text-blue-600"
              />
              <span className="text-white">Enable Betty Voice (ElevenLabs TTS)</span>
            </label>
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-6">
            System Status
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/70 text-sm mb-1">Betty API</div>
              <div className="text-green-400 font-semibold">Active</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/70 text-sm mb-1">PostgreSQL</div>
              <div className="text-green-400 font-semibold">Connected</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/70 text-sm mb-1">Knowledge Items</div>
              <div className="text-blue-400 font-semibold">4,690</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/70 text-sm mb-1">Failed Attempts</div>
              <div className="text-orange-400 font-semibold">598</div>
            </div>
          </div>
        </div>

        {/* Command Execution & Pretool Validation */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-6 flex items-center gap-3">
            <Terminal size={24} />
            Command Execution & Pretool Validation
          </h2>

          <div className="space-y-6">
            {/* Command Input Section */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-3">
                  <label className="block text-white/70 mb-2">Command</label>
                  <textarea
                    value={commandInput}
                    onChange={(e) => setCommandInput(e.target.value)}
                    placeholder="Enter command to validate and execute..."
                    className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white resize-none"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-white/70 mb-2">Tool Type</label>
                  <select
                    value={selectedTool}
                    onChange={(e) => setSelectedTool(e.target.value)}
                    className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white"
                  >
                    <option value="Bash">Bash</option>
                    <option value="Write">Write</option>
                    <option value="Edit">Edit</option>
                    <option value="Read">Read</option>
                    <option value="LS">LS</option>
                    <option value="Grep">Grep</option>
                  </select>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={validateCommand}
                  disabled={isValidating || !commandInput.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white flex items-center gap-2"
                >
                  <Shield size={18} />
                  {isValidating ? 'Validating...' : 'Validate with Pretool'}
                </button>

                {validationResult && validationResult.status === 'approved' && (
                  <button
                    onClick={executeCommand}
                    disabled={isExecuting}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white flex items-center gap-2"
                  >
                    <Play size={18} />
                    {isExecuting ? 'Executing...' : 'Execute'}
                  </button>
                )}

                <button
                  onClick={clearCommandForm}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white"
                >
                  Clear
                </button>
              </div>
            </div>

            {/* Validation Results */}
            {validationResult && (
              <div className={`rounded-lg p-4 border ${
                validationResult.status === 'approved' ? 'bg-green-500/10 border-green-500/30' :
                validationResult.status === 'blocked' ? 'bg-red-500/10 border-red-500/30' :
                'bg-yellow-500/10 border-yellow-500/30'
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  {validationResult.status === 'approved' ? 
                    <Check className="text-green-400" size={20} /> :
                    validationResult.status === 'blocked' ? 
                    <AlertCircle className="text-red-400" size={20} /> :
                    <AlertTriangle className="text-yellow-400" size={20} />
                  }
                  <span className={`font-semibold ${
                    validationResult.status === 'approved' ? 'text-green-400' :
                    validationResult.status === 'blocked' ? 'text-red-400' :
                    'text-yellow-400'
                  }`}>
                    {validationResult.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-white/80 mb-2">{validationResult.reason}</p>
                {validationResult.recommendations && (
                  <div className="mt-2">
                    <p className="text-white/70 text-sm mb-1">Recommendations:</p>
                    <ul className="text-white/60 text-sm list-disc pl-5">
                      {validationResult.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Command Output */}
            {commandOutput && (
              <div className="bg-black/30 border border-white/10 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Terminal size={16} className="text-white/70" />
                  <span className="text-white/70 text-sm">Output</span>
                </div>
                <pre className="text-white/90 text-sm whitespace-pre-wrap overflow-x-auto">
                  {commandOutput}
                </pre>
              </div>
            )}

            {/* Command History */}
            {commandHistory.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock size={20} />
                  Recent Commands
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {commandHistory.map((item) => (
                    <div key={item.id} className="bg-white/5 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="text-white/70 text-sm">{item.tool}</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            item.validationResult === 'approved' ? 'bg-green-500/20 text-green-400' :
                            item.validationResult === 'blocked' ? 'bg-red-500/20 text-red-400' :
                            'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {item.validationResult}
                          </span>
                        </div>
                        <span className="text-white/50 text-xs">
                          {item.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <code className="text-white/90 text-sm bg-black/20 px-2 py-1 rounded block overflow-x-auto">
                        {item.command}
                      </code>
                      {item.error && (
                        <div className="mt-2 text-red-400 text-sm">
                          Error: {item.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end gap-4">
          <button
            onClick={fetchConfig}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg text-white flex items-center gap-2"
          >
            <RefreshCw size={20} />
            Reload
          </button>
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className={`px-6 py-3 rounded-lg text-white flex items-center gap-2 ${
              saveStatus === 'saved' ? 'bg-green-600' :
              saveStatus === 'error' ? 'bg-red-600' :
              saveStatus === 'saving' ? 'bg-gray-600' :
              'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {saveStatus === 'saved' ? <Check size={20} /> : <Save size={20} />}
            {saveStatus === 'saving' ? 'Saving...' :
             saveStatus === 'saved' ? 'Saved!' :
             saveStatus === 'error' ? 'Error' :
             'Save Configuration'}
          </button>
        </div>
          </>
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <div className="mt-4">
            <TaskManagementDashboard />
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-6">
            <h2 className="text-2xl font-bold text-white mb-4">System Analytics</h2>
            <p className="text-white/70">Analytics dashboard coming soon...</p>
          </div>
        )}
      </div>
  );
}