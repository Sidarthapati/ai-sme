'use client'

import { useState, useEffect } from 'react'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { Sidebar } from '@/components/layout/Sidebar'
import { FilterPanel } from '@/components/chat/FilterPanel'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { Button } from '@/components/ui/button'
import { Settings, Menu, X, LogOut, User } from 'lucide-react'
import { useChatStore } from '@/lib/store/chat'
import { useAuthStore } from '@/lib/store/auth'
import { authApi } from '@/lib/api/auth'
import { chatApi } from '@/lib/api/client'
import Link from 'next/link'
import { toast } from 'sonner'

export default function ChatPage() {
  const [sourceType, setSourceType] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [filterPanelOpen, setFilterPanelOpen] = useState(false)
  const [loadingConversations, setLoadingConversations] = useState(false)
  const { user, clearAuth } = useAuthStore()
  const { loadConversations } = useChatStore()

  // Load conversations from backend on mount
  useEffect(() => {
    const loadConversationsFromBackend = async () => {
      try {
        setLoadingConversations(true)
        const response = await chatApi.listConversations()
        
        // Only show loader if there are conversations to load
        if (response.conversations.length > 0) {
          // Fetch all conversations in parallel
          const conversationPromises = response.conversations.map((conv: any) =>
            chatApi.getConversation(conv.id)
          )
          const fullConversations = await Promise.all(conversationPromises)
          
          // Convert backend format to frontend format
          const formattedConversations = fullConversations.map((fullConv: any) => ({
            id: fullConv.id,
            messages: fullConv.messages.map((msg: any) => ({
              id: msg.id,
              role: msg.role,
              content: msg.content,
              sources: msg.sources,
              timestamp: new Date(msg.timestamp),
            })),
            createdAt: new Date(fullConv.created_at),
            updatedAt: new Date(fullConv.updated_at),
          }))
          
          // Load all conversations at once
          loadConversations(formattedConversations)
        }
      } catch (error) {
        console.error('Failed to load conversations:', error)
      } finally {
        setLoadingConversations(false)
      }
    }

    loadConversationsFromBackend()
  }, [loadConversations])

  const handleLogout = async () => {
    await authApi.logout()
    clearAuth()
    toast.success('Logged out successfully')
  }

  return (
    <AuthGuard>
      <div className="flex h-screen">
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="hidden md:block">
          <Sidebar isLoading={loadingConversations} />
        </div>
      )}

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-40">
          <div className="fixed inset-0 bg-background/80" onClick={() => setSidebarOpen(false)} />
          <div className="fixed left-0 top-0 bottom-0 w-64 bg-background border-r">
            <Sidebar isLoading={loadingConversations} />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b bg-background px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden"
              >
                {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </Button>
              <h1 className="text-xl font-semibold">AI SME Assistant</h1>
            </div>
            <div className="flex items-center gap-2">
              <Link href="/upload">
                <Button variant="outline" size="sm">
                  Upload
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFilterPanelOpen(!filterPanelOpen)}
              >
                Filter
              </Button>
              {user && (
                <div className="flex items-center gap-2 px-2 text-sm text-muted-foreground">
                  {user.picture && (
                    <img
                      src={user.picture}
                      alt={user.name || user.email}
                      className="h-6 w-6 rounded-full"
                    />
                  )}
                  <span className="hidden md:inline">{user.name || user.email}</span>
                </div>
              )}
              <Link href="/settings">
                <Button variant="ghost" size="icon">
                  <Settings className="h-4 w-4" />
                </Button>
              </Link>
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Logout">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </header>

        {/* Filter Panel */}
        {filterPanelOpen && (
          <div className="border-b bg-muted/50 p-4">
            <FilterPanel
              sourceType={sourceType}
              onSourceTypeChange={setSourceType}
            />
          </div>
        )}

        {/* Messages */}
        <MessageList />

        {/* Input */}
        <ChatInput sourceType={sourceType || undefined} />
      </div>
    </div>
    </AuthGuard>
  )
}
