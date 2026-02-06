'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/lib/store/chat'
import { Message } from './Message'
import { Loader2 } from 'lucide-react'

export function MessageList() {
  const { currentConversationId, conversations, isLoading } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const conversation = currentConversationId
    ? conversations.get(currentConversationId)
    : null

  const messages = conversation?.messages || []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <p>Start a new conversation to begin chatting</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>No messages yet. Send a message to get started!</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground mb-4">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  )
}
