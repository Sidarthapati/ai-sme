/**
 * API client for communicating with the backend.
 */

import axios from 'axios'
import { useAuthStore } from '@/lib/store/auth'

// API URL from environment variable (set in Railway)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Debug: Log API URL (remove in production if needed)
if (typeof window !== 'undefined') {
  console.log('🔍 API_URL:', API_URL)
  console.log('🔍 NEXT_PUBLIC_API_URL env:', process.env.NEXT_PUBLIC_API_URL)
}

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle 401 errors (unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      useAuthStore.getState().clearAuth()
      // Don't redirect automatically - let components handle it
    }
    return Promise.reject(error)
  }
)

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message)
    }
    return Promise.reject(error)
  }
)

// Chat API
export const chatApi = {
  sendMessage: async (message: string, sourceType?: string, conversationId?: string) => {
    const response = await apiClient.post('/api/chat/', {
      message,
      source_type: sourceType,
      conversation_id: conversationId,
      stream: false,
    })
    return response.data
  },

  listConversations: async () => {
    const response = await apiClient.get('/api/chat/conversations')
    return response.data
  },

  getConversation: async (conversationId: string) => {
    const response = await apiClient.get(`/api/chat/conversations/${conversationId}`)
    return response.data
  },

  streamMessage: async function* (message: string, sourceType?: string, conversationId?: string) {
    // Get auth token from store
    const token = useAuthStore.getState().accessToken
    if (!token) {
      throw new Error('Not authenticated. Please sign in.')
    }

    const response = await fetch(`${API_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        source_type: sourceType,
        conversation_id: conversationId,
        stream: true,
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Stream error:', response.status, errorText)
      if (response.status === 403 || response.status === 401) {
        // Clear auth and force re-login
        useAuthStore.getState().clearAuth()
        throw new Error('Authentication failed. Please sign in again.')
      }
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('No response body')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data.trim()) {
              try {
                yield JSON.parse(data)
              } catch (e) {
                console.error('Failed to parse SSE data:', e)
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },

  deleteConversation: async (conversationId: string) => {
    const response = await apiClient.delete(`/api/chat/conversations/${conversationId}`)
    return response.data
  },
}

// Documents API
export const documentsApi = {
  upload: async (file: File, title?: string, tags?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    if (tags) formData.append('tags', tags)

    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  list: async (sourceType?: string) => {
    const params = sourceType ? { source_type: sourceType } : {}
    const response = await apiClient.get('/api/documents/', { params })
    return response.data
  },

  delete: async (documentId: string) => {
    const response = await apiClient.delete(`/api/documents/${documentId}`)
    return response.data
  },
}

// Health API
export const healthApi = {
  check: async () => {
    const response = await apiClient.get('/api/health/')
    return response.data
  },

  detailed: async () => {
    const response = await apiClient.get('/api/health/detailed')
    return response.data
  },
}

export default apiClient
