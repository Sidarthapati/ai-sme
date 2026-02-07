'use client'

import { useQueryClient } from '@tanstack/react-query'
import { FileUpload } from '@/components/upload/FileUpload'
import { DocumentList } from '@/components/upload/DocumentList'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function UploadPage() {
  const queryClient = useQueryClient()

  const handleUploadSuccess = () => {
    // Refresh the document list after successful upload
    queryClient.invalidateQueries({ queryKey: ['documents'] })
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <Link href="/chat">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Chat
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">Upload Documents</h1>
        <p className="text-muted-foreground">
          Upload PDF, DOCX, TXT, or MD files to add them to the knowledge base
        </p>
      </div>

      <div className="space-y-8">
        <FileUpload onUploadSuccess={handleUploadSuccess} />
        <DocumentList />
      </div>
    </div>
  )
}
