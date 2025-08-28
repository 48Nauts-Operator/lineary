// ABOUTME: File upload component for issue attachments
// ABOUTME: Drag and drop support with progress indicators

import React, { useState, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { API_URL } from '../App';

interface FileUploadProps {
  issueId: string;
  onUploadComplete?: () => void;
}

interface FileWithProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  id: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ issueId, onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      handleFiles(selectedFiles);
    }
  };

  const handleFiles = (newFiles: File[]) => {
    const fileWithProgress = newFiles.map(file => ({
      file,
      progress: 0,
      status: 'pending' as const,
      id: Math.random().toString(36).substr(2, 9)
    }));
    
    setFiles(prev => [...prev, ...fileWithProgress]);
    
    // Upload each file
    fileWithProgress.forEach(uploadFile);
  };

  const uploadFile = async (fileItem: FileWithProgress) => {
    const formData = new FormData();
    formData.append('file', fileItem.file);

    try {
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'uploading' }
          : f
      ));

      const response = await axios.post(
        `${API_URL}/attachments/upload/${issueId}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            
            setFiles(prev => prev.map(f => 
              f.id === fileItem.id 
                ? { ...f, progress }
                : f
            ));
          },
        }
      );

      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'complete', progress: 100 }
          : f
      ));
      
      toast.success(`${fileItem.file.name} uploaded successfully`);
      onUploadComplete?.();
    } catch (error: any) {
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'error' }
          : f
      ));
      
      toast.error(`Failed to upload ${fileItem.file.name}: ${error.message}`);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (file: File) => {
    const type = file.type;
    if (type.startsWith('image/')) return '🖼️';
    if (type === 'application/pdf') return '📄';
    if (type.includes('word')) return '📝';
    if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
    if (type === 'application/zip') return '📦';
    return '📎';
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200
          ${isDragging 
            ? 'border-purple-500 bg-purple-500/10' 
            : 'border-gray-600 hover:border-purple-500/50 bg-gray-800/50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.json,.zip"
        />
        
        <div className="text-4xl mb-4">📁</div>
        <p className="text-white font-medium mb-2">
          {isDragging ? 'Drop files here' : 'Click or drag files to upload'}
        </p>
        <p className="text-gray-400 text-sm">
          Supports images, documents, and archives (max 10MB)
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map(fileItem => (
            <div
              key={fileItem.id}
              className="bg-gray-800/50 rounded-lg p-3 flex items-center space-x-3"
            >
              <div className="text-2xl">{getFileIcon(fileItem.file)}</div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-white font-medium truncate">
                    {fileItem.file.name}
                  </p>
                  <p className="text-gray-400 text-sm">
                    {formatFileSize(fileItem.file.size)}
                  </p>
                </div>
                
                {fileItem.status === 'uploading' && (
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${fileItem.progress}%` }}
                    />
                  </div>
                )}
                
                {fileItem.status === 'complete' && (
                  <p className="text-green-400 text-sm">✓ Uploaded</p>
                )}
                
                {fileItem.status === 'error' && (
                  <p className="text-red-400 text-sm">✗ Upload failed</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;