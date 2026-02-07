'use client'

import { useChatStore } from '@/lib/store/chat'
import { chatApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { MessageSquare, Plus, Trash2, Calendar, Loader2 } from 'lucide-react'
import { format } from 'date-fns'
import { cn } from '@/lib/utils/cn'
import { toast } from 'sonner'

interface SidebarProps {
  isLoading?: boolean
}

export function Sidebar({ isLoading = false }: SidebarProps) {
  const {
    conversations,
    currentConversationId,
    setCurrentConversation,
    createConversation,
    deleteConversation,
  } = useChatStore()

  const handleDelete = async (conversationId: string) => {
    try {
      await chatApi.deleteConversation(conversationId)
      deleteConversation(conversationId)
      toast.success('Conversation deleted')
    } catch (error: any) {
      toast.error('Failed to delete conversation', {
        description: error.response?.data?.detail || error.message,
      })
    }
  }

  const conversationList = Array.from(conversations.values()).sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )

  return (
    <div className="w-64 border-r bg-background flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <Button
          onClick={() => createConversation()}
          className="w-full gap-2"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : conversationList.length === 0 ? (
          <div className="text-center text-muted-foreground text-sm p-4">
            No conversations yet
          </div>
        ) : (
          <div className="space-y-2">
            {conversationList.map((conv) => {
              const isActive = conv.id === currentConversationId
              const preview = conv.messages.length > 0
                ? conv.messages[0].content.slice(0, 50) + '...'
                : 'New conversation'

              return (
                <Card
                  key={conv.id}
                  className={cn(
                    'cursor-pointer transition-colors hover:bg-accent',
                    isActive && 'bg-accent border-primary'
                  )}
                  onClick={() => setCurrentConversation(conv.id)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <MessageSquare className="h-3 w-3 flex-shrink-0 text-muted-foreground" />
                          <span className="text-xs text-muted-foreground truncate">
                            {format(conv.updatedAt, 'MMM d, HH:mm')}
                          </span>
                        </div>
                        <p className="text-sm truncate">{preview}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {conv.messages.length} messages
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 flex-shrink-0"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(conv.id)
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
