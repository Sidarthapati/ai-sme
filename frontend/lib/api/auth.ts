/**
 * Authentication API client.
 */

import axios from 'axios'
import { useAuthStore } from '@/lib/store/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const authApi = {
  /**
   * Authenticate with Google token (ID token).
   */
  googleAuth: async (googleToken: string) => {
    const response = await axios.post(`${API_URL}/api/auth/google`, {
      token: googleToken,
    })
    return response.data
  },

  /**
   * Authenticate with Google user info (from access token).
   */
  googleAuthWithUserInfo: async (userInfo: {
    email: string
    name?: string
    picture?: string
    google_id: string
  }) => {
    const response = await axios.post(`${API_URL}/api/auth/google/userinfo`, userInfo)
    return response.data
  },

  /**
   * Get current user info.
   */
  getCurrentUser: async () => {
    const token = useAuthStore.getState().accessToken
    if (!token) {
      throw new Error('Not authenticated')
    }

    const response = await axios.get(`${API_URL}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  /**
   * Logout (client-side only for JWT).
   */
  logout: async () => {
    // JWT is stateless, so logout is handled client-side
    // But we can call the endpoint for consistency
    try {
      const token = useAuthStore.getState().accessToken
      if (token) {
        await axios.post(
          `${API_URL}/api/auth/logout`,
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )
      }
    } catch (error) {
      // Ignore errors on logout
      console.error('Logout error:', error)
    }
  },
}
