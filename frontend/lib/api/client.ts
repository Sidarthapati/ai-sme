/**
 * API client for communicating with the backend.
 */

import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

  streamMessage: async function* (message: string, sourceType?: string, conversationId?: string) {
    const response = await fetch(`${API_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        source_type: sourceType,
        conversation_id: conversationId,
        stream: true,
      }),
    })

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

  getConversation: async (conversationId: string) => {
    const response = await apiClient.get(`/api/chat/conversations/${conversationId}`)
    return response.data
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
