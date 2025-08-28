// ABOUTME: Project color selector component with preset colors and custom picker
// ABOUTME: Updates project color in real-time with visual feedback

import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { API_URL, Project } from '../App';

interface Props {
  project: Project;
  onColorUpdate: (color: string) => void;
}

const ProjectColorPicker: React.FC<Props> = ({ project, onColorUpdate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedColor, setSelectedColor] = useState(project.color || '#8B5CF6');
  const [customColor, setCustomColor] = useState(project.color || '#8B5CF6');
  const [isUpdating, setIsUpdating] = useState(false);

  const presetColors = [
    { name: 'Purple', value: '#8B5CF6' },
    { name: 'Blue', value: '#3B82F6' },
    { name: 'Green', value: '#10B981' },
    { name: 'Yellow', value: '#F59E0B' },
    { name: 'Red', value: '#EF4444' },
    { name: 'Pink', value: '#EC4899' },
    { name: 'Indigo', value: '#6366F1' },
    { name: 'Cyan', value: '#06B6D4' },
    { name: 'Orange', value: '#FB923C' },
    { name: 'Teal', value: '#14B8A6' },
    { name: 'Rose', value: '#F43F5E' },
    { name: 'Lime', value: '#84CC16' },
    { name: 'Emerald', value: '#10B981' },
    { name: 'Sky', value: '#0EA5E9' },
    { name: 'Violet', value: '#8B5CF6' },
    { name: 'Fuchsia', value: '#D946EF' }
  ];

  const updateProjectColor = async (color: string) => {
    setIsUpdating(true);
    try {
      await axios.put(`${API_URL}/projects/${project.id}`, { color });
      
      setSelectedColor(color);
      onColorUpdate(color);
      toast.success('Project color updated!');
      setIsOpen(false);
    } catch (error) {
      console.error('Error updating project color:', error);
      toast.error('Failed to update project color');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCustomColorSubmit = () => {
    if (/^#[0-9A-F]{6}$/i.test(customColor)) {
      updateProjectColor(customColor);
    } else {
      toast.error('Please enter a valid hex color (e.g., #8B5CF6)');
    }
  };

  return (
    <div className="relative">
      {/* Color Display Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:bg-gray-700/50 transition-all"
      >
        <div 
          className="w-6 h-6 rounded-full border-2 border-gray-600"
          style={{ backgroundColor: selectedColor }}
        />
        <span className="text-white font-medium">Project Color</span>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Color Picker Dropdown */}
      {isOpen && (
        <div className="absolute top-full mt-2 right-0 z-50 w-80 bg-gray-800 rounded-xl shadow-2xl border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold">Choose Project Color</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Current Color Display */}
          <div className="mb-4 p-3 bg-gray-900 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">Current Color</span>
              <div className="flex items-center space-x-2">
                <div 
                  className="w-20 h-8 rounded-lg border border-gray-600"
                  style={{ backgroundColor: selectedColor }}
                />
                <span className="text-white font-mono text-sm">{selectedColor}</span>
              </div>
            </div>
          </div>

          {/* Preset Colors Grid */}
          <div className="mb-4">
            <p className="text-gray-400 text-sm mb-2">Preset Colors</p>
            <div className="grid grid-cols-8 gap-2">
              {presetColors.map((color) => (
                <button
                  key={color.value}
                  onClick={() => updateProjectColor(color.value)}
                  disabled={isUpdating}
                  className={`
                    w-8 h-8 rounded-lg border-2 transition-all hover:scale-110
                    ${selectedColor === color.value 
                      ? 'border-white shadow-lg' 
                      : 'border-transparent hover:border-gray-500'
                    }
                  `}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                />
              ))}
            </div>
          </div>

          {/* Custom Color Input */}
          <div>
            <p className="text-gray-400 text-sm mb-2">Custom Color</p>
            <div className="flex space-x-2">
              <div className="flex-1 flex items-center space-x-2 bg-gray-900 rounded-lg px-3 py-2">
                <input
                  type="color"
                  value={customColor}
                  onChange={(e) => setCustomColor(e.target.value)}
                  className="w-8 h-8 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={customColor}
                  onChange={(e) => setCustomColor(e.target.value)}
                  placeholder="#8B5CF6"
                  className="flex-1 bg-transparent text-white font-mono text-sm focus:outline-none"
                />
              </div>
              <button
                onClick={handleCustomColorSubmit}
                disabled={isUpdating}
                className="px-4 py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors disabled:opacity-50"
              >
                Apply
              </button>
            </div>
          </div>

          {/* Color Theory Tips */}
          <div className="mt-4 p-3 bg-gray-900/50 rounded-lg">
            <p className="text-purple-400 text-xs font-medium mb-1">💡 Color Tips</p>
            <ul className="text-gray-400 text-xs space-y-1">
              <li>• Use bright colors for high-priority projects</li>
              <li>• Cool colors (blue, green) for long-term projects</li>
              <li>• Warm colors (red, orange) for urgent work</li>
            </ul>
          </div>
        </div>
      )}

      {/* Color Preview Bar */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-1 rounded-full transition-all duration-300"
        style={{ backgroundColor: selectedColor }}
      />
    </div>
  );
};

export default ProjectColorPicker;