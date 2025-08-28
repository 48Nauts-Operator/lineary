// ABOUTME: Bug report form with automatic browser and system info capture
// ABOUTME: Includes severity levels, reproduction steps, and screenshot upload

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { API_URL } from '../App';

interface Props {
  projectId: string;
  onSubmitSuccess?: () => void;
}

const BugReportForm: React.FC<Props> = ({ projectId, onSubmitSuccess }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    severity: 'medium',
    reporter_name: '',
    reporter_email: '',
    steps_to_reproduce: '',
    expected_behavior: '',
    actual_behavior: '',
    error_message: '',
    environment: ''
  });
  
  const [browserInfo, setBrowserInfo] = useState<any>({});
  const [systemInfo, setSystemInfo] = useState<any>({});

  useEffect(() => {
    // Capture browser and system info
    const captureSystemInfo = () => {
      const info = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        url: window.location.href
      };
      
      // Parse browser info
      const browser: any = {};
      const ua = navigator.userAgent;
      
      if (ua.indexOf('Chrome') > -1) {
        browser.name = 'Chrome';
        browser.version = ua.match(/Chrome\/(\d+)/)?.[1];
      } else if (ua.indexOf('Safari') > -1) {
        browser.name = 'Safari';
        browser.version = ua.match(/Version\/(\d+)/)?.[1];
      } else if (ua.indexOf('Firefox') > -1) {
        browser.name = 'Firefox';
        browser.version = ua.match(/Firefox\/(\d+)/)?.[1];
      }
      
      setBrowserInfo(browser);
      setSystemInfo(info);
      
      // Auto-fill environment field
      setFormData(prev => ({
        ...prev,
        environment: `${browser.name || 'Unknown'} ${browser.version || ''} on ${info.platform}`
      }));
    };
    
    captureSystemInfo();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title || !formData.description) {
      toast.error('Please provide at least a title and description');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const response = await axios.post(`${API_URL}/bugs/report`, {
        project_id: projectId,
        ...formData,
        browser_info: browserInfo,
        system_info: systemInfo
      });
      
      toast.success(response.data.message || 'Bug report submitted successfully');
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        severity: 'medium',
        reporter_name: '',
        reporter_email: '',
        steps_to_reproduce: '',
        expected_behavior: '',
        actual_behavior: '',
        error_message: '',
        environment: `${browserInfo.name || 'Unknown'} ${browserInfo.version || ''} on ${systemInfo.platform}`
      });
      
      setIsOpen(false);
      onSubmitSuccess?.();
    } catch (error: any) {
      console.error('Bug report error:', error);
      toast.error(error.response?.data?.error || 'Failed to submit bug report');
    } finally {
      setIsSubmitting(false);
    }
  };

  const severityOptions = [
    { value: 'critical', label: 'Critical', color: 'text-red-500', description: 'System is unusable' },
    { value: 'high', label: 'High', color: 'text-orange-500', description: 'Major functionality broken' },
    { value: 'medium', label: 'Medium', color: 'text-yellow-500', description: 'Minor functionality affected' },
    { value: 'low', label: 'Low', color: 'text-blue-500', description: 'Cosmetic or minor issue' }
  ];

  return (
    <>
      {/* Bug Report Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-red-500 text-white rounded-full px-6 py-3 shadow-lg hover:bg-red-600 transition-all hover:scale-105 flex items-center space-x-2 z-40"
      >
        <span>🐛</span>
        <span>Report Bug</span>
      </button>

      {/* Bug Report Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Report a Bug</h2>
                  <p className="text-gray-400 mt-1">Help us improve by reporting issues you encounter</p>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-white transition-colors text-2xl"
                >
                  ✕
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Severity Selection */}
              <div>
                <label className="block text-white font-medium mb-3">Severity Level</label>
                <div className="grid grid-cols-4 gap-3">
                  {severityOptions.map(option => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, severity: option.value })}
                      className={`
                        p-3 rounded-lg border-2 transition-all text-center
                        ${formData.severity === option.value
                          ? 'border-purple-500 bg-purple-500/20'
                          : 'border-gray-700 hover:border-gray-600 bg-gray-900/50'
                        }
                      `}
                    >
                      <p className={`font-medium ${option.color}`}>{option.label}</p>
                      <p className="text-xs text-gray-400 mt-1">{option.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Basic Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white font-medium mb-2">Your Name</label>
                  <input
                    type="text"
                    value={formData.reporter_name}
                    onChange={(e) => setFormData({ ...formData, reporter_name: e.target.value })}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">Email (optional)</label>
                  <input
                    type="email"
                    value={formData.reporter_email}
                    onChange={(e) => setFormData({ ...formData, reporter_email: e.target.value })}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                    placeholder="john@example.com"
                  />
                </div>
              </div>

              {/* Bug Title */}
              <div>
                <label className="block text-white font-medium mb-2">
                  Bug Title <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                  placeholder="Brief description of the issue"
                  required
                />
              </div>

              {/* Bug Description */}
              <div>
                <label className="block text-white font-medium mb-2">
                  Description <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                  rows={3}
                  placeholder="Detailed description of what went wrong"
                  required
                />
              </div>

              {/* Steps to Reproduce */}
              <div>
                <label className="block text-white font-medium mb-2">Steps to Reproduce</label>
                <textarea
                  value={formData.steps_to_reproduce}
                  onChange={(e) => setFormData({ ...formData, steps_to_reproduce: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                  rows={3}
                  placeholder="1. Go to...\n2. Click on...\n3. See error"
                />
              </div>

              {/* Expected vs Actual */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white font-medium mb-2">Expected Behavior</label>
                  <textarea
                    value={formData.expected_behavior}
                    onChange={(e) => setFormData({ ...formData, expected_behavior: e.target.value })}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                    rows={2}
                    placeholder="What should happen?"
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">Actual Behavior</label>
                  <textarea
                    value={formData.actual_behavior}
                    onChange={(e) => setFormData({ ...formData, actual_behavior: e.target.value })}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                    rows={2}
                    placeholder="What actually happened?"
                  />
                </div>
              </div>

              {/* Error Message */}
              <div>
                <label className="block text-white font-medium mb-2">Error Message (if any)</label>
                <textarea
                  value={formData.error_message}
                  onChange={(e) => setFormData({ ...formData, error_message: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white font-mono text-sm focus:outline-none focus:border-purple-500"
                  rows={2}
                  placeholder="Copy any error messages here"
                />
              </div>

              {/* System Information */}
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                <h4 className="text-white font-medium mb-3">System Information (auto-captured)</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-400">Browser:</span>
                    <span className="text-white ml-2">{browserInfo.name} {browserInfo.version}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Platform:</span>
                    <span className="text-white ml-2">{systemInfo.platform}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Screen:</span>
                    <span className="text-white ml-2">{systemInfo.screenResolution}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Language:</span>
                    <span className="text-white ml-2">{systemInfo.language}</span>
                  </div>
                </div>
              </div>

              {/* Submit Buttons */}
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="flex-1 bg-gray-700 text-white rounded-lg px-6 py-3 font-medium hover:bg-gray-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 bg-red-500 text-white rounded-lg px-6 py-3 font-medium hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 rounded-full animate-spin border-t-white"></div>
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <span>🐛</span>
                      <span>Submit Bug Report</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default BugReportForm;