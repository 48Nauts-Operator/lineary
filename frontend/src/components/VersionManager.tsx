// ABOUTME: Version management component with auto-versioning controls
// ABOUTME: Displays version history, release notes, and version configuration

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { API_URL } from '../App';

interface VersionConfig {
  auto_version: boolean;
  version_pattern: string;
  current_major: number;
  current_minor: number;
  current_patch: number;
  prefix: string;
}

interface Version {
  id: string;
  version_number: string;
  release_type: string;
  release_notes: string;
  status: string;
  release_date: string;
  issues_fixed: number;
  issues_planned: number;
}

interface Props {
  projectId: string;
}

const VersionManager: React.FC<Props> = ({ projectId }) => {
  const [config, setConfig] = useState<VersionConfig | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [showReleaseModal, setShowReleaseModal] = useState(false);
  const [releaseType, setReleaseType] = useState<'major' | 'minor' | 'patch'>('patch');
  const [releaseNotes, setReleaseNotes] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVersionData();
  }, [projectId]);

  const fetchVersionData = async () => {
    try {
      const [configRes, versionsRes] = await Promise.all([
        axios.get(`${API_URL}/versions/config/${projectId}`),
        axios.get(`${API_URL}/versions/project/${projectId}`)
      ]);
      
      setConfig(configRes.data);
      setVersions(versionsRes.data);
    } catch (error) {
      console.error('Error fetching version data:', error);
      toast.error('Failed to load version information');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoVersion = async () => {
    if (!config) return;
    
    try {
      const response = await axios.post(
        `${API_URL}/versions/auto-generate/${projectId}`,
        { releaseType, releaseNotes }
      );
      
      toast.success(response.data.message);
      setShowReleaseModal(false);
      setReleaseNotes('');
      fetchVersionData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to create version');
    }
  };

  const toggleAutoVersion = async () => {
    if (!config) return;
    
    try {
      await axios.put(`${API_URL}/versions/config/${projectId}`, {
        auto_version: !config.auto_version
      });
      
      setConfig({ ...config, auto_version: !config.auto_version });
      toast.success(`Auto-versioning ${!config.auto_version ? 'enabled' : 'disabled'}`);
    } catch (error) {
      toast.error('Failed to update configuration');
    }
  };

  const getNextVersion = () => {
    if (!config) return 'v0.1.0';
    
    let major = config.current_major;
    let minor = config.current_minor;
    let patch = config.current_patch;
    
    switch (releaseType) {
      case 'major':
        major++;
        minor = 0;
        patch = 0;
        break;
      case 'minor':
        minor++;
        patch = 0;
        break;
      case 'patch':
        patch++;
        break;
    }
    
    return `${config.prefix}${major}.${minor}.${patch}`;
  };

  const getVersionBadgeColor = (status: string) => {
    switch (status) {
      case 'released': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'in_progress': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'planned': return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading version data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Version Configuration */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Version Configuration</h3>
          <button
            onClick={toggleAutoVersion}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              config?.auto_version
                ? 'bg-purple-500 text-white hover:bg-purple-600'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Auto-Versioning: {config?.auto_version ? 'ON' : 'OFF'}
          </button>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Current Version</p>
            <p className="text-2xl font-bold text-white">
              {config ? `${config.prefix}${config.current_major}.${config.current_minor}.${config.current_patch}` : 'v0.1.0'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Total Releases</p>
            <p className="text-2xl font-bold text-white">{versions.length}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Pattern</p>
            <p className="text-2xl font-bold text-white uppercase">{config?.version_pattern || 'semver'}</p>
          </div>
        </div>
        
        <button
          onClick={() => setShowReleaseModal(true)}
          className="w-full bg-purple-500 text-white rounded-lg px-4 py-3 font-medium hover:bg-purple-600 transition-colors"
        >
          🚀 Create New Release
        </button>
      </div>

      {/* Version History */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">Version History</h3>
        
        <div className="space-y-3">
          {versions.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No versions released yet</p>
          ) : (
            versions.map(version => (
              <div
                key={version.id}
                className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <h4 className="text-lg font-bold text-white">{version.version_number}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getVersionBadgeColor(version.status)}`}>
                      {version.status}
                    </span>
                    <span className="text-gray-400 text-sm">
                      {new Date(version.release_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="text-gray-400">
                      🔧 {version.issues_fixed} fixed
                    </span>
                    <span className="text-gray-400">
                      📋 {version.issues_planned} planned
                    </span>
                  </div>
                </div>
                {version.release_notes && (
                  <p className="text-gray-300 text-sm">{version.release_notes}</p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Release Modal */}
      {showReleaseModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">Create New Release</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-2">Release Type</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['major', 'minor', 'patch'] as const).map(type => (
                    <button
                      key={type}
                      onClick={() => setReleaseType(type)}
                      className={`px-4 py-2 rounded-lg font-medium capitalize transition-all ${
                        releaseType === type
                          ? 'bg-purple-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-2">Next Version</label>
                <div className="bg-gray-900 rounded-lg px-4 py-3 text-white font-mono text-lg">
                  {getNextVersion()}
                </div>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-2">Release Notes</label>
                <textarea
                  value={releaseNotes}
                  onChange={(e) => setReleaseNotes(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                  rows={4}
                  placeholder="What's new in this release?"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowReleaseModal(false)}
                className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 font-medium hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAutoVersion}
                className="flex-1 bg-purple-500 text-white rounded-lg px-4 py-2 font-medium hover:bg-purple-600 transition-colors"
              >
                Create Release
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VersionManager;