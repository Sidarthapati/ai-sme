/**
 * Zustand store for managing chat state.
 */

import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    id: string
    title: string
    url?: string
    source_type: string
    chunk_index?: number
  }>
  timestamp: Date
}

export interface Conversation {
  id: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

interface ChatState {
  currentConversationId: string | null
  conversations: Map<string, Conversation>
  isLoading: boolean
  error: string | null

  // Actions
  createConversation: () => string
  setCurrentConversation: (id: string | null) => void
  addMessage: (conversationId: string, message: Omit<Message, 'id' | 'timestamp'>) => void
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  deleteConversation: (id: string) => void
  loadConversation: (conversation: Conversation) => void
}

const generateId = () => {
  return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const generateMessageId = () => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export const useChatStore = create<ChatState>((set, get) => ({
  currentConversationId: null,
  conversations: new Map(),
  isLoading: false,
  error: null,

  createConversation: () => {
    const id = generateId()
    const conversation: Conversation = {
      id,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    }
    set((state) => {
      const newConversations = new Map(state.conversations)
      newConversations.set(id, conversation)
      return {
        conversations: newConversations,
        currentConversationId: id,
      }
    })
    return id
  },

  setCurrentConversation: (id) => {
    set({ currentConversationId: id })
  },

  addMessage: (conversationId, message) => {
    const newMessage: Message = {
      ...message,
      id: generateMessageId(),
      timestamp: new Date(),
    }
    set((state) => {
      const conversation = state.conversations.get(conversationId)
      if (!conversation) return state

      const updatedConversation: Conversation = {
        ...conversation,
        messages: [...conversation.messages, newMessage],
        updatedAt: new Date(),
      }

      const newConversations = new Map(state.conversations)
      newConversations.set(conversationId, updatedConversation)

      return { conversations: newConversations }
    })
  },

  updateMessage: (conversationId, messageId, updates) => {
    set((state) => {
      const conversation = state.conversations.get(conversationId)
      if (!conversation) return state

      const updatedMessages = conversation.messages.map((msg) =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      )

      const updatedConversation: Conversation = {
        ...conversation,
        messages: updatedMessages,
        updatedAt: new Date(),
      }

      const newConversations = new Map(state.conversations)
      newConversations.set(conversationId, updatedConversation)

      return { conversations: newConversations }
    })
  },

  setLoading: (loading) => {
    set({ isLoading: loading })
  },

  setError: (error) => {
    set({ error })
  },

  clearError: () => {
    set({ error: null })
  },

  deleteConversation: (id) => {
    set((state) => {
      const newConversations = new Map(state.conversations)
      newConversations.delete(id)
      const newCurrentId =
        state.currentConversationId === id ? null : state.currentConversationId
      return {
        conversations: newConversations,
        currentConversationId: newCurrentId,
      }
    })
  },

  loadConversation: (conversation) => {
    set((state) => {
      const newConversations = new Map(state.conversations)
      newConversations.set(conversation.id, conversation)
      return {
        conversations: newConversations,
        currentConversationId: conversation.id,
      }
    })
  },

  loadConversations: (conversations: Conversation[]) => {
    set((state) => {
      const newConversations = new Map(state.conversations)
      for (const conv of conversations) {
        newConversations.set(conv.id, conv)
      }
      return { conversations: newConversations }
    })
  },
}))
