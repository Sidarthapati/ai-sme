'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    router.push('/chat')
  }, [router])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">AI SME Assistant</h1>
        <p className="text-xl text-muted-foreground">Redirecting to chat...</p>
      </div>
    </main>
  )
}
