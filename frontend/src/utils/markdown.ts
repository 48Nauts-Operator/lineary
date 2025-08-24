// ABOUTME: Utility functions for markdown processing and text extraction
// ABOUTME: Provides helpers to strip markdown formatting and truncate text

/**
 * Strip markdown formatting from text
 * @param markdown - The markdown text to strip
 * @returns Plain text without markdown formatting
 */
export function stripMarkdown(markdown: string): string {
  if (!markdown) return ''
  
  let text = markdown
  
  // Remove code blocks
  text = text.replace(/```[\s\S]*?```/g, '')
  
  // Remove inline code
  text = text.replace(/`([^`]+)`/g, '$1')
  
  // Remove headers
  text = text.replace(/^#{1,6}\s+/gm, '')
  
  // Remove bold
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1')
  text = text.replace(/__([^_]+)__/g, '$1')
  
  // Remove italic
  text = text.replace(/\*([^*]+)\*/g, '$1')
  text = text.replace(/_([^_]+)_/g, '$1')
  
  // Remove links but keep text
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
  
  // Remove images
  text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
  
  // Remove blockquotes
  text = text.replace(/^>\s+/gm, '')
  
  // Remove horizontal rules
  text = text.replace(/^---+$/gm, '')
  text = text.replace(/^\*\*\*+$/gm, '')
  
  // Remove list markers
  text = text.replace(/^[\*\-\+]\s+/gm, '')
  text = text.replace(/^\d+\.\s+/gm, '')
  
  // Remove task list markers
  text = text.replace(/^- \[[x ]\]\s+/gmi, '')
  
  // Remove tables
  text = text.replace(/\|[^|]+\|/g, '')
  text = text.replace(/^\|[-\s]+\|$/gm, '')
  
  // Clean up multiple newlines
  text = text.replace(/\n{3,}/g, '\n\n')
  
  // Trim whitespace
  text = text.trim()
  
  return text
}

/**
 * Get a preview of markdown content
 * @param markdown - The markdown text
 * @param maxLength - Maximum length of preview (default: 150)
 * @returns Plain text preview without markdown formatting
 */
export function getMarkdownPreview(markdown: string, maxLength: number = 150): string {
  const plainText = stripMarkdown(markdown)
  
  if (plainText.length <= maxLength) {
    return plainText
  }
  
  // Try to break at a word boundary
  let preview = plainText.substring(0, maxLength)
  const lastSpaceIndex = preview.lastIndexOf(' ')
  
  if (lastSpaceIndex > maxLength * 0.8) {
    preview = preview.substring(0, lastSpaceIndex)
  }
  
  return preview + '...'
}

/**
 * Check if text contains markdown formatting
 * @param text - The text to check
 * @returns True if text contains markdown
 */
export function hasMarkdown(text: string): boolean {
  if (!text) return false
  
  const markdownPatterns = [
    /^#{1,6}\s+/m,           // Headers
    /\*\*[^*]+\*\*/,          // Bold
    /__[^_]+__/,              // Bold alt
    /\*[^*]+\*/,              // Italic
    /_[^_]+_/,                // Italic alt
    /\[[^\]]+\]\([^)]+\)/,    // Links
    /!\[[^\]]*\]\([^)]+\)/,   // Images
    /```[\s\S]*?```/,         // Code blocks
    /`[^`]+`/,                // Inline code
    /^>\s+/m,                 // Blockquotes
    /^[\*\-\+]\s+/m,          // Lists
    /^\d+\.\s+/m,             // Numbered lists
    /^- \[[x ]\]\s+/mi,       // Task lists
    /\|[^|]+\|/               // Tables
  ]
  
  return markdownPatterns.some(pattern => pattern.test(text))
}

/**
 * Count words in markdown text (excluding formatting)
 * @param markdown - The markdown text
 * @returns Word count
 */
export function countMarkdownWords(markdown: string): number {
  const plainText = stripMarkdown(markdown)
  const words = plainText.split(/\s+/).filter(word => word.length > 0)
  return words.length
}