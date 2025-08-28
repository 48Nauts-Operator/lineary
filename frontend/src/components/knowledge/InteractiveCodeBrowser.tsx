import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Code,
  File,
  Folder,
  Search,
  Eye,
  Copy,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Hash,
  Zap,
  Package
} from 'lucide-react'
import { useCodeRepositories, useRepositoryFiles, useFileContent } from '../../hooks/useKnowledgeVisualization'

interface InteractiveCodeBrowserProps {
  searchQuery: string
  languageFilter?: string
}

const InteractiveCodeBrowser: React.FC<InteractiveCodeBrowserProps> = ({
  searchQuery,
  languageFilter
}) => {
  const [selectedRepository, setSelectedRepository] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  const {
    data: repositories,
    isLoading: isLoadingRepos
  } = useCodeRepositories(languageFilter)

  const {
    data: files,
    isLoading: isLoadingFiles
  } = useRepositoryFiles(selectedRepository, undefined, 1, 50)

  const {
    data: fileContent,
    isLoading: isLoadingContent
  } = useFileContent(selectedFile || '')

  const filteredRepositories = repositories?.filter(repo =>
    repo.repository_name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const filteredFiles = files?.filter(file =>
    file.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.programming_language.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const getLanguageColor = (language: string): string => {
    const colors: Record<string, string> = {
      'python': 'text-green-400',
      'javascript': 'text-yellow-400',
      'typescript': 'text-blue-400',
      'java': 'text-red-400',
      'cpp': 'text-purple-400',
      'csharp': 'text-indigo-400',
      'go': 'text-cyan-400',
      'rust': 'text-orange-400',
      'sql': 'text-pink-400'
    }
    return colors[language.toLowerCase()] || 'text-white'
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Interactive Code Browser</h2>
          <p className="text-white/70">
            Browse and explore {repositories?.length || 0} code repositories
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[700px]">
        {/* Repository List */}
        <div className="glass-morphism border border-white/10 rounded-lg p-4 overflow-hidden">
          <h3 className="text-white font-semibold mb-4 flex items-center">
            <Package className="w-4 h-4 mr-2 text-betty-400" />
            Repositories
          </h3>

          <div className="space-y-2 overflow-y-auto h-full pb-16">
            {isLoadingRepos ? (
              [...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-white/5 rounded-lg animate-pulse"></div>
              ))
            ) : (
              filteredRepositories.map((repo) => (
                <motion.div
                  key={repo.repository_name}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedRepository(repo.repository_name)}
                  className={`p-3 rounded-lg cursor-pointer transition-all border ${
                    selectedRepository === repo.repository_name
                      ? 'bg-betty-500/20 border-betty-400'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Folder className="w-4 h-4 text-betty-400" />
                      <span className="text-white text-sm font-medium truncate">
                        {repo.repository_name}
                      </span>
                    </div>
                    <ChevronRight className="w-3 h-3 text-white/40" />
                  </div>
                  <div className="flex items-center space-x-3 mt-1 text-xs text-white/60">
                    <span>{repo.total_files} files</span>
                    <span>{repo.total_lines.toLocaleString()} lines</span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* File List */}
        <div className="glass-morphism border border-white/10 rounded-lg p-4 overflow-hidden">
          <h3 className="text-white font-semibold mb-4 flex items-center">
            <File className="w-4 h-4 mr-2 text-betty-400" />
            Files
            {selectedRepository && (
              <span className="ml-2 text-xs text-white/60">({selectedRepository})</span>
            )}
          </h3>

          <div className="space-y-2 overflow-y-auto h-full pb-16">
            {!selectedRepository ? (
              <div className="text-center py-8 text-white/40">
                Select a repository to view files
              </div>
            ) : isLoadingFiles ? (
              [...Array(8)].map((_, i) => (
                <div key={i} className="h-10 bg-white/5 rounded-lg animate-pulse"></div>
              ))
            ) : (
              filteredFiles.map((file, index) => (
                <motion.div
                  key={`${file.file_path}-${index}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.02 }}
                  onClick={() => setSelectedFile(file.file_path)}
                  className={`p-3 rounded-lg cursor-pointer transition-all border ${
                    selectedFile === file.file_path
                      ? 'bg-purple-500/20 border-purple-400'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <Code className={`w-3 h-3 ${getLanguageColor(file.programming_language)}`} />
                      <span className="text-white text-sm font-medium truncate">
                        {file.file_name}
                      </span>
                    </div>
                    <Eye className="w-3 h-3 text-white/40" />
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className={`${getLanguageColor(file.programming_language)} font-medium`}>
                      {file.programming_language}
                    </span>
                    <div className="flex items-center space-x-2 text-white/60">
                      <span>{file.lines_of_code} lines</span>
                      <span>•</span>
                      <span>{file.functions.length} funcs</span>
                    </div>
                  </div>

                  {file.complexity_score > 0 && (
                    <div className="mt-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-white/50">Complexity</span>
                        <span className="text-white/70">{file.complexity_score.toFixed(1)}</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-1 mt-1">
                        <div
                          className="bg-gradient-to-r from-green-400 to-red-400 h-1 rounded-full"
                          style={{ width: `${Math.min(file.complexity_score * 10, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Code Viewer */}
        <div className="glass-morphism border border-white/10 rounded-lg p-4 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold flex items-center">
              <Code className="w-4 h-4 mr-2 text-betty-400" />
              Code Viewer
            </h3>
            {fileContent && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(fileContent.content)}
                  className="p-1 text-white/60 hover:text-white transition-colors"
                  title="Copy code"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  className="p-1 text-white/60 hover:text-white transition-colors"
                  title="Open in new tab"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          <div className="h-full overflow-y-auto pb-16">
            {!selectedFile ? (
              <div className="text-center py-8 text-white/40">
                Select a file to view its content
              </div>
            ) : isLoadingContent ? (
              <div className="space-y-2">
                {[...Array(20)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-2">
                    <div className="w-6 h-4 bg-white/10 rounded"></div>
                    <div className="flex-1 h-4 bg-white/5 rounded"></div>
                  </div>
                ))}
              </div>
            ) : fileContent ? (
              <div>
                {/* File Info */}
                <div className="bg-white/5 rounded-lg p-3 mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium">{fileContent.file_path}</span>
                    <span className={`text-sm font-medium ${getLanguageColor(fileContent.programming_language)}`}>
                      {fileContent.programming_language}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs text-white/60">
                    <div className="flex items-center">
                      <Zap className="w-3 h-3 mr-1" />
                      {fileContent.functions.length} functions
                    </div>
                    <div className="flex items-center">
                      <Package className="w-3 h-3 mr-1" />
                      {fileContent.classes.length} classes
                    </div>
                  </div>
                </div>

                {/* Code Content */}
                <div className="bg-black/30 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                  <pre className="text-white/90 whitespace-pre-wrap">
                    {fileContent.content.split('\n').map((line, index) => (
                      <div key={index} className="flex items-start">
                        <span className="text-white/30 w-8 text-right mr-3 select-none shrink-0">
                          {index + 1}
                        </span>
                        <span className="flex-1">{line}</span>
                      </div>
                    ))}
                  </pre>
                </div>

                {/* Functions List */}
                {fileContent.functions.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-white font-medium mb-2 flex items-center">
                      <Zap className="w-4 h-4 mr-2 text-betty-400" />
                      Functions ({fileContent.functions.length})
                    </h4>
                    <div className="space-y-1">
                      {fileContent.functions.slice(0, 10).map((func: any, index) => (
                        <div key={index} className="bg-white/5 rounded p-2 text-sm">
                          <span className="text-betty-400 font-medium">{func.name}</span>
                          {func.line_number && (
                            <span className="text-white/40 ml-2">Line {func.line_number}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-red-400">
                Failed to load file content
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InteractiveCodeBrowser