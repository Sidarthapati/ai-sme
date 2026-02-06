'use client'

import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { useChatStore } from '@/lib/store/chat'

export default function ChatPage() {
  const { createConversation, currentConversationId } = useChatStore()

  const handleNewChat = () => {
    createConversation()
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b bg-background px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold">AI SME Assistant</h1>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewChat}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>
      </header>

      {/* Messages */}
      <MessageList />

      {/* Input */}
      <ChatInput />
    </div>
  )
}
