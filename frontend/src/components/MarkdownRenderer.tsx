// ABOUTME: Markdown renderer component with full GFM support and syntax highlighting
// ABOUTME: Renders markdown content with code blocks, tables, task lists, and more

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'
import rehypeHighlight from 'rehype-highlight'
import { Components } from 'react-markdown'
import 'highlight.js/styles/github-dark.css'

interface MarkdownRendererProps {
  content: string
  className?: string
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  // Custom components for markdown elements
  const components: Partial<Components> = {
    // Code blocks with syntax highlighting and copy button
    pre: ({ children, ...props }) => {
      const codeElement = React.Children.toArray(children)[0] as React.ReactElement
      const codeContent = codeElement?.props?.children?.[0] || ''
      
      const handleCopy = () => {
        navigator.clipboard.writeText(codeContent)
        // Show toast or feedback
        const button = document.getElementById('copy-btn')
        if (button) {
          button.textContent = 'Copied!'
          setTimeout(() => {
            button.textContent = 'Copy'
          }, 2000)
        }
      }

      return (
        <div className="relative group my-4">
          <button
            id="copy-btn"
            onClick={handleCopy}
            className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded opacity-0 group-hover:opacity-100 transition-opacity"
          >
            Copy
          </button>
          <pre className="bg-gray-900 border border-gray-700 rounded-lg overflow-x-auto p-4" {...props}>
            {children}
          </pre>
        </div>
      )
    },
    
    // Inline code
    code: ({ className, children, ...props }) => {
      const isInline = !className
      if (isInline) {
        return (
          <code className="px-1.5 py-0.5 bg-gray-800 text-purple-400 rounded text-sm" {...props}>
            {children}
          </code>
        )
      }
      return (
        <code className={className} {...props}>
          {children}
        </code>
      )
    },
    
    // Tables with styling
    table: ({ children }) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full divide-y divide-gray-700">
          {children}
        </table>
      </div>
    ),
    
    thead: ({ children }) => (
      <thead className="bg-gray-800">
        {children}
      </thead>
    ),
    
    tbody: ({ children }) => (
      <tbody className="bg-gray-900 divide-y divide-gray-700">
        {children}
      </tbody>
    ),
    
    th: ({ children }) => (
      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
        {children}
      </th>
    ),
    
    td: ({ children }) => (
      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-300">
        {children}
      </td>
    ),
    
    // Task lists with checkboxes
    input: ({ type, checked, disabled, ...props }) => {
      if (type === 'checkbox') {
        return (
          <input
            type="checkbox"
            checked={checked}
            disabled={disabled}
            className="mr-2 rounded border-gray-600 bg-gray-800 text-purple-500 focus:ring-purple-500"
            onChange={() => {}}
            {...props}
          />
        )
      }
      return <input type={type} {...props} />
    },
    
    // Lists
    ul: ({ children, className }) => {
      const isTaskList = className?.includes('contains-task-list')
      return (
        <ul className={`${isTaskList ? 'list-none' : 'list-disc'} list-inside space-y-1 my-2 text-gray-300`}>
          {children}
        </ul>
      )
    },
    
    ol: ({ children }) => (
      <ol className="list-decimal list-inside space-y-1 my-2 text-gray-300">
        {children}
      </ol>
    ),
    
    // Blockquotes
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-purple-500 pl-4 my-4 italic text-gray-400">
        {children}
      </blockquote>
    ),
    
    // Headings
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-white mb-4 mt-6">
        {children}
      </h1>
    ),
    
    h2: ({ children }) => (
      <h2 className="text-xl font-bold text-white mb-3 mt-5">
        {children}
      </h2>
    ),
    
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-white mb-2 mt-4">
        {children}
      </h3>
    ),
    
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-white mb-2 mt-3">
        {children}
      </h4>
    ),
    
    // Paragraphs
    p: ({ children }) => (
      <p className="text-gray-300 mb-3 leading-relaxed">
        {children}
      </p>
    ),
    
    // Links
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-purple-400 hover:text-purple-300 underline"
      >
        {children}
      </a>
    ),
    
    // Horizontal rules
    hr: () => (
      <hr className="my-6 border-gray-700" />
    ),
    
    // Images
    img: ({ src, alt }) => (
      <img
        src={src}
        alt={alt}
        className="max-w-full h-auto rounded-lg my-4"
      />
    ),
    
    // Strong/Bold
    strong: ({ children }) => (
      <strong className="font-bold text-white">
        {children}
      </strong>
    ),
    
    // Emphasis/Italic
    em: ({ children }) => (
      <em className="italic text-gray-300">
        {children}
      </em>
    ),
  }

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content || ''}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer