'use client'

import { useState, KeyboardEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Loader2 } from 'lucide-react'
import { useChatStore } from '@/lib/store/chat'
import { chatApi } from '@/lib/api/client'

interface ChatInputProps {
  sourceType?: string
}

export function ChatInput({ sourceType }: ChatInputProps) {
  const [input, setInput] = useState('')
  const {
    currentConversationId,
    createConversation,
    addMessage,
    updateMessage,
    setLoading,
    setError,
  } = useChatStore()

  const handleSend = async () => {
    if (!input.trim() || useChatStore.getState().isLoading) return

    const messageContent = input.trim()
    setInput('')

    // Get or create conversation
    let conversationId = currentConversationId
    if (!conversationId) {
      conversationId = createConversation()
    }

    // Add user message
    addMessage(conversationId, {
      role: 'user',
      content: messageContent,
    })

    // Add placeholder assistant message
    const assistantMessageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    addMessage(conversationId, {
      role: 'assistant',
      content: '',
    })

    setLoading(true)
    setError(null)

    try {
      // Stream the response
      let fullContent = ''
      const stream = chatApi.streamMessage(messageContent, sourceType, conversationId)

      for await (const chunk of stream) {
        if (chunk.type === 'token') {
          fullContent += chunk.content
          // Update the last message with accumulated content
          const conversation = useChatStore.getState().conversations.get(conversationId!)
          if (conversation && conversation.messages.length > 0) {
            const lastMessage = conversation.messages[conversation.messages.length - 1]
            if (lastMessage.role === 'assistant') {
              updateMessage(conversationId!, lastMessage.id, {
                content: fullContent,
              })
            }
          }
        } else if (chunk.type === 'complete') {
          // Update with final content and sources
          const conversation = useChatStore.getState().conversations.get(conversationId!)
          if (conversation && conversation.messages.length > 0) {
            const lastMessage = conversation.messages[conversation.messages.length - 1]
            if (lastMessage.role === 'assistant') {
              updateMessage(conversationId!, lastMessage.id, {
                content: chunk.answer || fullContent,
                sources: chunk.sources,
              })
            }
          }
        } else if (chunk.type === 'error') {
          throw new Error(chunk.error || 'Unknown error')
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setError(error instanceof Error ? error.message : 'Failed to send message')
      
      // Update the assistant message with error
      const conversation = useChatStore.getState().conversations.get(conversationId!)
      if (conversation && conversation.messages.length > 0) {
        const lastMessage = conversation.messages[conversation.messages.length - 1]
        if (lastMessage.role === 'assistant' && !lastMessage.content) {
          updateMessage(conversationId!, lastMessage.id, {
            content: 'Sorry, I encountered an error. Please try again.',
          })
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isLoading = useChatStore((state) => state.isLoading)

  return (
    <div className="border-t bg-background p-4">
      <div className="max-w-4xl mx-auto flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          size="icon"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
