'use client'

import { useGoogleLogin } from '@react-oauth/google'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/lib/store/auth'
import { authApi } from '@/lib/api/auth'
import { toast } from 'sonner'
import { LogIn, Loader2 } from 'lucide-react'
import { useState } from 'react'

interface GoogleSignInProps {
  onSuccess?: () => void
}

export function GoogleSignIn({ onSuccess }: GoogleSignInProps) {
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true)
      try {
        // Get user info from Google using access token
        const googleUserInfo = await fetch(
          'https://www.googleapis.com/oauth2/v2/userinfo',
          {
            headers: {
              Authorization: `Bearer ${tokenResponse.access_token}`,
            },
          }
        ).then((res) => res.json())

        // Now send user info to backend to create/get user and get our JWT
        // We'll modify backend to accept user info directly
        const response = await authApi.googleAuthWithUserInfo({
          email: googleUserInfo.email,
          name: googleUserInfo.name,
          picture: googleUserInfo.picture,
          google_id: googleUserInfo.id,
        })
        
        // Store auth state
        setAuth(response.user, response.access_token)
        
        toast.success('Signed in successfully!', {
          description: `Welcome, ${response.user.name || response.user.email}`,
        })
        
        onSuccess?.()
      } catch (error: any) {
        toast.error('Sign in failed', {
          description: error.response?.data?.detail || error.message || 'Unknown error',
        })
      } finally {
        setLoading(false)
      }
    },
    onError: () => {
      toast.error('Sign in cancelled or failed')
      setLoading(false)
    },
  })

  return (
    <Button
      onClick={() => handleGoogleLogin()}
      disabled={loading}
      className="w-full gap-2"
      size="lg"
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Signing in...
        </>
      ) : (
        <>
          <LogIn className="h-4 w-4" />
          Sign in with Google
        </>
      )}
    </Button>
  )
}
