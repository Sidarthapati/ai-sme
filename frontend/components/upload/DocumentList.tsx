'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Trash2, FileText, Calendar } from 'lucide-react'
import { documentsApi } from '@/lib/api/client'
import { toast } from 'sonner'
import { format } from 'date-fns'

export function DocumentList() {
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(),
  })

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document deleted successfully')
    },
    onError: (error: any) => {
      toast.error('Failed to delete document', {
        description: error.response?.data?.detail || error.message,
      })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-muted-foreground">Loading documents...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-destructive">
          Error loading documents: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </div>
    )
  }

  const documents = data?.documents || []

  if (documents.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground mb-2">
            {data?.total && data.total > 0
              ? 'Document list will be available soon'
              : 'Upload a document to get started'}
          </p>
          {data?.total && data.total > 0 && (
            <p className="text-xs text-muted-foreground">
              {data.total} document{data.total !== 1 ? 's' : ''} indexed in the knowledge base
            </p>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Uploaded Documents ({data?.total || 0})
        </h2>
      </div>

      <div className="grid gap-4">
        {documents.map((doc: any) => (
          <Card key={doc.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-base">{doc.title || doc.filename}</CardTitle>
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      {doc.filename}
                    </span>
                    {doc.uploaded_at && (
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {format(new Date(doc.uploaded_at), 'MMM d, yyyy')}
                      </span>
                    )}
                    <span className="text-xs bg-muted px-2 py-1 rounded">
                      {doc.chunks} chunks
                    </span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => deleteMutation.mutate(doc.id)}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  )
}
