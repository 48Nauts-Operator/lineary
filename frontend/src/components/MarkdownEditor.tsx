// ABOUTME: Markdown editor with live preview and formatting toolbar
// ABOUTME: Provides rich editing experience with syntax helpers and preview toggle

import React, { useState, useRef } from 'react'
import MarkdownRenderer from './MarkdownRenderer'

interface MarkdownEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  minRows?: number
  className?: string
}

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({ 
  value, 
  onChange, 
  placeholder = 'Enter markdown content...',
  minRows = 6,
  className = ''
}) => {
  const [showPreview, setShowPreview] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Insert markdown formatting
  const insertFormatting = (before: string, after: string = '') => {
    const textarea = textareaRef.current
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = value.substring(start, end)
    
    const newText = value.substring(0, start) + 
                   before + selectedText + after + 
                   value.substring(end)
    
    onChange(newText)
    
    // Restore cursor position
    setTimeout(() => {
      textarea.focus()
      const newCursorPos = start + before.length + selectedText.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  // Formatting helpers
  const formatBold = () => insertFormatting('**', '**')
  const formatItalic = () => insertFormatting('_', '_')
  const formatCode = () => insertFormatting('`', '`')
  const formatLink = () => insertFormatting('[', '](url)')
  const formatHeading = (level: number) => {
    const hashes = '#'.repeat(level)
    insertFormatting(`${hashes} `, '')
  }
  const formatList = () => insertFormatting('- ', '')
  const formatNumberedList = () => insertFormatting('1. ', '')
  const formatBlockquote = () => insertFormatting('> ', '')
  const formatCodeBlock = () => insertFormatting('```\n', '\n```')
  const formatTable = () => {
    const table = '\n| Column 1 | Column 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n'
    insertFormatting(table, '')
  }
  const formatTaskList = () => insertFormatting('- [ ] ', '')

  return (
    <div className={`markdown-editor ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-gray-800 border border-gray-600 border-b-0 rounded-t-lg px-2 py-1">
        <div className="flex items-center gap-1">
          {/* Text formatting */}
          <button
            type="button"
            onClick={formatBold}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Bold (Ctrl+B)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12h9a4 4 0 014 4 4 4 0 01-4 4H6z" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatItalic}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Italic (Ctrl+I)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 4h4M14 4l-4 16m-4 0h4" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatCode}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Inline Code"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </button>
          
          <div className="w-px h-6 bg-gray-600 mx-1" />
          
          {/* Headings */}
          <button
            type="button"
            onClick={() => formatHeading(1)}
            className="px-2 py-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white text-sm"
            title="Heading 1"
          >
            H1
          </button>
          
          <button
            type="button"
            onClick={() => formatHeading(2)}
            className="px-2 py-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white text-sm"
            title="Heading 2"
          >
            H2
          </button>
          
          <button
            type="button"
            onClick={() => formatHeading(3)}
            className="px-2 py-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white text-sm"
            title="Heading 3"
          >
            H3
          </button>
          
          <div className="w-px h-6 bg-gray-600 mx-1" />
          
          {/* Lists */}
          <button
            type="button"
            onClick={formatList}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Bullet List"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatNumberedList}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Numbered List"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatTaskList}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Task List"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </button>
          
          <div className="w-px h-6 bg-gray-600 mx-1" />
          
          {/* Other elements */}
          <button
            type="button"
            onClick={formatLink}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Link"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatBlockquote}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Blockquote"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatCodeBlock}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Code Block"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
          
          <button
            type="button"
            onClick={formatTable}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
            title="Table"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
        
        {/* Preview toggle */}
        <button
          type="button"
          onClick={() => setShowPreview(!showPreview)}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            showPreview 
              ? 'bg-purple-600 text-white' 
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          {showPreview ? 'Edit' : 'Preview'}
        </button>
      </div>
      
      {/* Editor/Preview */}
      <div className="border border-gray-600 border-t-0 rounded-b-lg overflow-hidden">
        {showPreview ? (
          <div className="bg-gray-700/50 p-4 min-h-[150px]">
            <MarkdownRenderer content={value || '*No content yet*'} />
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={minRows}
            className="w-full px-4 py-3 bg-gray-700/50 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 resize-y"
            style={{ minHeight: `${minRows * 1.5}rem` }}
          />
        )}
      </div>
      
      {/* Help text */}
      <div className="mt-2 text-xs text-gray-500">
        Supports Markdown formatting. Use preview to see how it will look.
      </div>
    </div>
  )
}

export default MarkdownEditor