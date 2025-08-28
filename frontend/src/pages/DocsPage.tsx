// ABOUTME: Beautiful documentation page with proper markdown rendering and export features
// ABOUTME: Features GitBook-style design, syntax highlighting, PDF/Markdown export

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import { Project, API_URL } from '../App'

interface Doc {
  id: string
  title: string
  content: string
  category: string
  project_id: string
  related_issues?: string[]
  created_at: string
  updated_at: string
}

interface Props {
  selectedProject: Project | null
  projects: Project[]
}

const DocsPage: React.FC<Props> = ({ selectedProject, projects }) => {
  const [docs, setDocs] = useState<Doc[]>([])
  const [selectedDoc, setSelectedDoc] = useState<Doc | null>(null)
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [localSelectedProject, setLocalSelectedProject] = useState<Project | null>(selectedProject)

  const categories = [
    { id: 'all', name: 'All Documents', icon: '📚' },
    { id: 'overview', name: 'Overview', icon: '📋' },
    { id: 'api', name: 'API Reference', icon: '🔗' },
    { id: 'guides', name: 'Guides', icon: '📖' },
    { id: 'architecture', name: 'Architecture', icon: '🏗️' },
    { id: 'deployment', name: 'Deployment', icon: '🚀' },
    { id: 'troubleshooting', name: 'Troubleshooting', icon: '🔧' }
  ]

  useEffect(() => {
    setLocalSelectedProject(selectedProject)
  }, [selectedProject])

  useEffect(() => {
    if (localSelectedProject) {
      fetchDocs()
      setSelectedDoc(null)
    } else {
      setDocs([])
      setSelectedDoc(null)
    }
  }, [localSelectedProject])

  const fetchDocs = async () => {
    if (!localSelectedProject) {
      setDocs([])
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      // Fetch docs - using direct path that nginx will proxy to local backend
      const response = await axios.get(`/api/docs/project/${localSelectedProject.id}`)
      
      if (response.data && response.data.length > 0) {
        setDocs(response.data)
        // Auto-select first doc
        if (response.data.length > 0 && !selectedDoc) {
          setSelectedDoc(response.data[0])
        }
      } else {
        // Create default documentation for the project
        await createDefaultDocs()
      }
    } catch (error) {
      console.error('Error fetching docs:', error)
      // Create default docs on error
      await createDefaultDocs()
    } finally {
      setLoading(false)
    }
  }

  const createDefaultDocs = async () => {
    if (!localSelectedProject) return

    const defaultDoc = {
      title: `${localSelectedProject.name} Documentation`,
      content: `# ${localSelectedProject.name}

## Overview

${localSelectedProject.description || 'Welcome to the project documentation.'}

## Getting Started

This documentation will help you understand and work with ${localSelectedProject.name}.

### Quick Start

1. Review the project overview
2. Check the architecture documentation
3. Follow the deployment guide
4. Refer to API documentation for integration

## Key Features

- Feature documentation coming soon
- API endpoints and integration guides
- Architecture decisions and patterns
- Deployment and operational procedures

## Need Help?

- Check the troubleshooting section
- Review common issues and solutions
- Contact the team for support

---

*Documentation is AI-generated and continuously updated*`,
      category: 'overview',
      project_id: localSelectedProject.id
    }

    try {
      const response = await axios.post('/api/docs', defaultDoc)
      setDocs([response.data])
      setSelectedDoc(response.data)
    } catch (error) {
      console.error('Error creating default docs:', error)
    }
  }


  const exportToPDF = async () => {
    if (!selectedDoc) return

    const element = document.getElementById('doc-content')
    if (!element) return

    try {
      const canvas = await html2canvas(element, {
        backgroundColor: '#1f2937',
        scale: 2
      })
      
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'px',
        format: [canvas.width, canvas.height]
      })
      
      pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height)
      pdf.save(`${selectedDoc.title}.pdf`)
      
      toast.success('PDF exported successfully')
    } catch (error) {
      console.error('Error exporting PDF:', error)
      toast.error('Failed to export PDF')
    }
  }

  const exportToMarkdown = () => {
    if (!selectedDoc) return

    const blob = new Blob([selectedDoc.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedDoc.title}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('Markdown exported successfully')
  }

  const filteredDocs = docs.filter(doc => {
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          doc.content.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  // No project selected state
  if (!localSelectedProject) {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-6">📚</div>
          <h2 className="text-3xl font-bold text-white mb-4">Select a Project</h2>
          <p className="text-gray-400 mb-8">Choose a project to view its documentation</p>
          
          <div className="space-y-3">
            {projects.map(project => (
              <button
                key={project.id}
                onClick={() => setLocalSelectedProject(project)}
                className="w-full px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-all duration-200 text-left flex items-center space-x-3"
              >
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: project.color }}></div>
                <span className="font-medium">{project.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full bg-gray-900">
      {/* Sidebar */}
      <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
        {/* Project Selector */}
        <div className="p-4 border-b border-gray-700">
          <select
            value={localSelectedProject?.id || ''}
            onChange={(e) => {
              const project = projects.find(p => p.id === e.target.value)
              setLocalSelectedProject(project || null)
            }}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
          >
            <option value="">Select Project</option>
            {projects.map(project => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-700">
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none placeholder-gray-400"
          />
        </div>

        {/* Categories */}
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Categories</h3>
          <div className="space-y-1">
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`w-full px-3 py-2 text-left rounded-lg transition-colors ${
                  selectedCategory === cat.id 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <span className="mr-2">{cat.icon}</span>
                {cat.name}
              </button>
            ))}
          </div>
        </div>

        {/* Document List */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {loading ? (
              <div className="text-gray-400 text-center py-8">Loading...</div>
            ) : filteredDocs.length === 0 ? (
              <div className="text-gray-400 text-center py-8">No documents found</div>
            ) : (
              filteredDocs.map(doc => (
                <button
                  key={doc.id}
                  onClick={() => {
                    setSelectedDoc(doc)
                  }}
                  className={`w-full px-3 py-3 text-left rounded-lg transition-all ${
                    selectedDoc?.id === doc.id
                      ? 'bg-purple-600 text-white shadow-lg'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="font-medium mb-1">{doc.title}</div>
                  <div className="text-xs opacity-75">
                    {categories.find(c => c.id === doc.category)?.name || doc.category}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-850 to-gray-900">
        {selectedDoc ? (
          <>
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-700 bg-gray-800/50 backdrop-blur">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <h1 className="text-2xl font-bold text-white">{selectedDoc.title}</h1>
                </div>
                
                <div className="flex items-center space-x-3">
                  {/* Export buttons */}
                  <button
                    onClick={exportToMarkdown}
                    className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
                    title="Export as Markdown"
                  >
                    📄 MD
                  </button>
                  <button
                    onClick={exportToPDF}
                    className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
                    title="Export as PDF"
                  >
                    📑 PDF
                  </button>
                  
                  
                  {/* Close button */}
                  <button
                    onClick={() => setSelectedDoc(null)}
                    className="p-1.5 text-gray-400 hover:text-white transition-colors"
                    title="Close document"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              <div id="doc-content" className="px-8 py-6 max-w-4xl mx-auto">
                <div className="prose prose-invert prose-lg max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({children}) => <h1 className="text-3xl font-bold text-gray-100 mb-6 mt-8 border-b border-gray-700 pb-3">{children}</h1>,
                        h2: ({children}) => <h2 className="text-2xl font-semibold text-gray-100 mb-4 mt-6">{children}</h2>,
                        h3: ({children}) => <h3 className="text-xl font-semibold text-gray-200 mb-3 mt-4">{children}</h3>,
                        h4: ({children}) => <h4 className="text-lg font-medium text-gray-300 mb-2 mt-3">{children}</h4>,
                        p: ({children}) => <p className="text-gray-300 mb-4 leading-relaxed">{children}</p>,
                        ul: ({children}) => <ul className="list-disc list-inside space-y-2 mb-4 text-gray-300">{children}</ul>,
                        ol: ({children}) => <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-300">{children}</ol>,
                        li: ({children}) => <li className="text-gray-300">{children}</li>,
                        code: ({className, children, ...props}) => {
                          const match = /language-(\w+)/.exec(className || '')
                          const language = match ? match[1] : ''
                          const inline = !match
                          
                          return inline ? (
                            <code className="bg-gray-800 text-purple-300 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
                          ) : (
                            <div className="my-4">
                              {language && (
                                <div className="bg-gray-800 text-gray-400 px-4 py-2 text-xs font-mono rounded-t-lg border border-gray-700 border-b-0 uppercase tracking-wider">
                                  {language}
                                </div>
                              )}
                              <div className={`rounded-${language ? 'b' : ''}lg border border-gray-700 overflow-hidden`}>
                                <SyntaxHighlighter
                                  language={language || 'text'}
                                  style={vscDarkPlus}
                                  customStyle={{
                                    margin: 0,
                                    padding: '1rem',
                                    fontSize: '0.875rem',
                                    backgroundColor: '#0d1117'
                                  }}
                                  codeTagProps={{
                                    style: {
                                      fontFamily: 'JetBrains Mono, Fira Code, Consolas, Monaco, monospace'
                                    }
                                  }}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              </div>
                            </div>
                          )
                        },
                        blockquote: ({children}) => {
                          // Check if this is a special callout box
                          let content = ''
                          if (typeof children === 'string') {
                            content = children
                          } else if (React.isValidElement(children)) {
                            content = String((children as any)?.props?.children || '')
                          } else if (Array.isArray(children)) {
                            content = children.map(child => 
                              typeof child === 'string' ? child : 
                              React.isValidElement(child) ? String((child as any)?.props?.children || '') : ''
                            ).join('')
                          }
                          const isInfo = content.toLowerCase().includes('[!info]') || content.toLowerCase().includes('[!note]')
                          const isWarning = content.toLowerCase().includes('[!warning]') || content.toLowerCase().includes('[!caution]')
                          const isError = content.toLowerCase().includes('[!error]') || content.toLowerCase().includes('[!danger]')
                          const isSuccess = content.toLowerCase().includes('[!success]') || content.toLowerCase().includes('[!tip]')
                          
                          // Clean the content by removing the markers
                          const cleanContent = content
                            .replace(/\[!\w+\]/gi, '')
                            .trim()
                          
                          if (isInfo) {
                            return (
                              <div className="my-6 rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
                                <div className="flex items-start">
                                  <span className="mr-3 text-2xl">ℹ️</span>
                                  <div className="flex-1">
                                    <div className="font-semibold text-blue-400 mb-1">Info</div>
                                    <div className="text-gray-300">{cleanContent}</div>
                                  </div>
                                </div>
                              </div>
                            )
                          }
                          
                          if (isWarning) {
                            return (
                              <div className="my-6 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
                                <div className="flex items-start">
                                  <span className="mr-3 text-2xl">⚠️</span>
                                  <div className="flex-1">
                                    <div className="font-semibold text-yellow-400 mb-1">Warning</div>
                                    <div className="text-gray-300">{cleanContent}</div>
                                  </div>
                                </div>
                              </div>
                            )
                          }
                          
                          if (isError) {
                            return (
                              <div className="my-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
                                <div className="flex items-start">
                                  <span className="mr-3 text-2xl">🚨</span>
                                  <div className="flex-1">
                                    <div className="font-semibold text-red-400 mb-1">Error</div>
                                    <div className="text-gray-300">{cleanContent}</div>
                                  </div>
                                </div>
                              </div>
                            )
                          }
                          
                          if (isSuccess) {
                            return (
                              <div className="my-6 rounded-lg border border-green-500/30 bg-green-500/10 p-4">
                                <div className="flex items-start">
                                  <span className="mr-3 text-2xl">✅</span>
                                  <div className="flex-1">
                                    <div className="font-semibold text-green-400 mb-1">Success Tip</div>
                                    <div className="text-gray-300">{cleanContent}</div>
                                  </div>
                                </div>
                              </div>
                            )
                          }
                          
                          // Default blockquote style
                          return (
                            <blockquote className="border-l-4 border-purple-500 pl-4 my-4 text-gray-300 italic">
                              {children}
                            </blockquote>
                          )
                        },
                        a: ({href, children}) => (
                          <a href={href} className="text-purple-400 hover:text-purple-300 underline" target="_blank" rel="noopener noreferrer">
                            {children}
                          </a>
                        ),
                        table: ({children}) => (
                          <table className="min-w-full divide-y divide-gray-700 my-4">
                            {children}
                          </table>
                        ),
                        th: ({children}) => (
                          <th className="px-4 py-2 bg-gray-800 text-left text-gray-200 font-semibold">
                            {children}
                          </th>
                        ),
                        td: ({children}) => (
                          <td className="px-4 py-2 border-t border-gray-700 text-gray-300">
                            {children}
                          </td>
                        ),
                        hr: () => <hr className="my-8 border-gray-700" />,
                        strong: ({children}) => <strong className="font-bold text-gray-100">{children}</strong>,
                        em: ({children}) => <em className="italic text-gray-200">{children}</em>,
                      }}
                    >
                      {selectedDoc.content}
                    </ReactMarkdown>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-5xl mb-4">📄</div>
              <h2 className="text-xl font-semibold text-gray-300 mb-2">No Document Selected</h2>
              <p className="text-gray-500">Select a document from the sidebar to view its content</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DocsPage