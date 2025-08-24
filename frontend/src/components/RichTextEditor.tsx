// ABOUTME: Rich text editor component using TipTap for project documentation
// ABOUTME: Provides formatting options, markdown support, and collaborative editing features

import React from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'

interface Props {
  content: string
  onChange: (content: string) => void
  placeholder?: string
}

const RichTextEditor: React.FC<Props> = ({ content, onChange, placeholder }) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        openOnClick: false,
      }),
      Image,
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'prose prose-invert max-w-none focus:outline-none min-h-[400px] px-4 py-3',
      },
    },
  })

  React.useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content)
    }
  }, [content, editor])

  if (!editor) {
    return (
      <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-600 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-600 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-600 rounded w-5/6"></div>
        </div>
      </div>
    )
  }

  const addLink = () => {
    const url = window.prompt('Enter URL:')
    if (url) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    }
  }

  const addImage = () => {
    const url = window.prompt('Enter image URL:')
    if (url) {
      editor.chain().focus().setImage({ src: url }).run()
    }
  }

  return (
    <div className="border border-gray-600 rounded-lg overflow-hidden bg-gray-700/50">
      {/* Toolbar */}
      <div className="flex items-center space-x-1 p-3 bg-gray-800/50 border-b border-gray-600">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('bold') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          <strong>B</strong>
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('italic') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          <em>I</em>
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleStrike().run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('strike') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          <s>S</s>
        </button>
        
        <div className="w-px h-6 bg-gray-600 mx-1"></div>
        
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('heading', { level: 1 }) ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          H1
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('heading', { level: 2 }) ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          H2
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('heading', { level: 3 }) ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          H3
        </button>
        
        <div className="w-px h-6 bg-gray-600 mx-1"></div>
        
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('bulletList') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          •
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('orderedList') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          1.
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('codeBlock') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          {'</>'}
        </button>
        
        <div className="w-px h-6 bg-gray-600 mx-1"></div>
        
        <button
          onClick={addLink}
          className={`p-2 rounded hover:bg-gray-600 transition-colors ${
            editor.isActive('link') ? 'bg-purple-600 text-white' : 'text-gray-400'
          }`}
        >
          🔗
        </button>
        
        <button
          onClick={addImage}
          className="p-2 rounded hover:bg-gray-600 transition-colors text-gray-400"
        >
          🖼️
        </button>
        
        <div className="w-px h-6 bg-gray-600 mx-1"></div>
        
        <button
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          className="p-2 rounded hover:bg-gray-600 transition-colors text-gray-400 disabled:opacity-50"
        >
          ↶
        </button>
        
        <button
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          className="p-2 rounded hover:bg-gray-600 transition-colors text-gray-400 disabled:opacity-50"
        >
          ↷
        </button>
      </div>

      {/* Editor Content */}
      <div className="min-h-[400px]">
        <EditorContent 
          editor={editor} 
          className="text-white"
          placeholder={placeholder}
        />
      </div>
    </div>
  )
}

export default RichTextEditor