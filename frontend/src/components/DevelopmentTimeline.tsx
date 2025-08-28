// ABOUTME: Interactive development flow timeline visualization component
// ABOUTME: Shows project progress, milestones, and activity over time

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../App';

interface TimelineEvent {
  id: string;
  type: 'issue_created' | 'issue_completed' | 'sprint_start' | 'sprint_end' | 'version_release' | 'comment';
  title: string;
  description?: string;
  timestamp: string;
  user?: string;
  metadata?: any;
  icon: string;
  color: string;
}

interface Props {
  projectId: string;
}

const DevelopmentTimeline: React.FC<Props> = ({ projectId }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'grouped'>('list');

  useEffect(() => {
    fetchTimelineEvents();
  }, [projectId, filter]);

  const fetchTimelineEvents = async () => {
    setLoading(true);
    try {
      // Fetch all relevant data
      const [issuesRes, sprintsRes, versionsRes, activityRes] = await Promise.all([
        axios.get(`${API_URL}/issues?project_id=${projectId}`),
        axios.get(`${API_URL}/sprints?project_id=${projectId}`),
        axios.get(`${API_URL}/versions/project/${projectId}`),
        axios.get(`${API_URL}/analytics/dashboard/${projectId}?days=30`)
      ]);

      const timelineEvents: TimelineEvent[] = [];

      // Process issues
      issuesRes.data.forEach((issue: any) => {
        timelineEvents.push({
          id: `issue-created-${issue.id}`,
          type: 'issue_created',
          title: `Issue created: ${issue.title}`,
          description: issue.description,
          timestamp: issue.created_at,
          user: issue.assignee,
          metadata: { priority: issue.priority, status: issue.status },
          icon: '📝',
          color: 'bg-blue-500'
        });

        if (issue.status === 'done' && issue.completed_at) {
          timelineEvents.push({
            id: `issue-completed-${issue.id}`,
            type: 'issue_completed',
            title: `Issue completed: ${issue.title}`,
            timestamp: issue.completed_at,
            user: issue.assignee,
            icon: '✅',
            color: 'bg-green-500'
          });
        }
      });

      // Process sprints
      sprintsRes.data.forEach((sprint: any) => {
        if (sprint.start_date) {
          timelineEvents.push({
            id: `sprint-start-${sprint.id}`,
            type: 'sprint_start',
            title: `Sprint started: ${sprint.name}`,
            timestamp: sprint.start_date,
            icon: '🏃',
            color: 'bg-purple-500'
          });
        }

        if (sprint.end_date && sprint.status === 'completed') {
          timelineEvents.push({
            id: `sprint-end-${sprint.id}`,
            type: 'sprint_end',
            title: `Sprint completed: ${sprint.name}`,
            timestamp: sprint.end_date,
            icon: '🏁',
            color: 'bg-purple-600'
          });
        }
      });

      // Process versions
      versionsRes.data.forEach((version: any) => {
        if (version.status === 'released') {
          timelineEvents.push({
            id: `version-${version.id}`,
            type: 'version_release',
            title: `Version released: ${version.version_number}`,
            description: version.release_notes,
            timestamp: version.release_date,
            icon: '🚀',
            color: 'bg-yellow-500'
          });
        }
      });

      // Sort events by timestamp
      timelineEvents.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      // Apply filter
      let filteredEvents = timelineEvents;
      if (filter !== 'all') {
        filteredEvents = timelineEvents.filter(e => e.type === filter);
      }

      setEvents(filteredEvents);
    } catch (error) {
      console.error('Error fetching timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupEventsByDate = () => {
    const grouped: { [key: string]: TimelineEvent[] } = {};
    
    events.forEach(event => {
      const date = new Date(event.timestamp).toLocaleDateString();
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(event);
    });
    
    return grouped;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
      return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      return date.toLocaleString([], { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    }
  };

  const filterOptions = [
    { value: 'all', label: 'All Events', icon: '📅' },
    { value: 'issue_created', label: 'Issues Created', icon: '📝' },
    { value: 'issue_completed', label: 'Issues Completed', icon: '✅' },
    { value: 'sprint_start', label: 'Sprint Starts', icon: '🏃' },
    { value: 'sprint_end', label: 'Sprint Ends', icon: '🏁' },
    { value: 'version_release', label: 'Releases', icon: '🚀' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading timeline...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {filterOptions.map(option => (
              <button
                key={option.value}
                onClick={() => setFilter(option.value)}
                className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center space-x-2 ${
                  filter === option.value
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
                }`}
              >
                <span>{option.icon}</span>
                <span>{option.label}</span>
              </button>
            ))}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-all ${
                viewMode === 'list' 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
              }`}
            >
              📋
            </button>
            <button
              onClick={() => setViewMode('grouped')}
              className={`p-2 rounded-lg transition-all ${
                viewMode === 'grouped' 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
              }`}
            >
              📊
            </button>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-xl font-bold text-white mb-6">Development Timeline</h3>
        
        {events.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No events found for the selected filter</p>
        ) : viewMode === 'list' ? (
          <div className="space-y-4">
            {events.map((event, index) => (
              <div key={event.id} className="relative">
                {index < events.length - 1 && (
                  <div className="absolute left-6 top-12 w-0.5 h-full bg-gray-700" />
                )}
                
                <div className="flex items-start space-x-4">
                  <div className={`w-12 h-12 rounded-full ${event.color} flex items-center justify-center text-white text-xl flex-shrink-0`}>
                    {event.icon}
                  </div>
                  
                  <div className="flex-1 bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-white font-medium">{event.title}</h4>
                      <span className="text-gray-400 text-sm">
                        {formatTimestamp(event.timestamp)}
                      </span>
                    </div>
                    
                    {event.description && (
                      <p className="text-gray-300 text-sm mb-2">{event.description}</p>
                    )}
                    
                    {event.user && (
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500 text-sm">by</span>
                        <span className="text-purple-400 text-sm">{event.user}</span>
                      </div>
                    )}
                    
                    {event.metadata && (
                      <div className="flex items-center space-x-2 mt-2">
                        {event.metadata.priority && (
                          <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                            Priority: {event.metadata.priority}
                          </span>
                        )}
                        {event.metadata.status && (
                          <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                            Status: {event.metadata.status}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupEventsByDate()).map(([date, dateEvents]) => (
              <div key={date}>
                <h4 className="text-purple-400 font-medium mb-3 sticky top-0 bg-gray-800/90 backdrop-blur-sm py-2">
                  {date}
                </h4>
                <div className="space-y-3 ml-4">
                  {dateEvents.map(event => (
                    <div key={event.id} className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full ${event.color} flex items-center justify-center text-white text-sm flex-shrink-0`}>
                        {event.icon}
                      </div>
                      <div className="flex-1 bg-gray-900/50 rounded-lg px-4 py-2 border border-gray-700/50">
                        <span className="text-white text-sm">{event.title}</span>
                      </div>
                      <span className="text-gray-500 text-xs">
                        {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Stats Summary */}
        <div className="mt-8 pt-6 border-t border-gray-700">
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-white">
                {events.filter(e => e.type === 'issue_created').length}
              </p>
              <p className="text-gray-400 text-sm">Issues Created</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">
                {events.filter(e => e.type === 'issue_completed').length}
              </p>
              <p className="text-gray-400 text-sm">Issues Completed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-400">
                {events.filter(e => e.type.includes('sprint')).length}
              </p>
              <p className="text-gray-400 text-sm">Sprint Events</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-400">
                {events.filter(e => e.type === 'version_release').length}
              </p>
              <p className="text-gray-400 text-sm">Releases</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DevelopmentTimeline;