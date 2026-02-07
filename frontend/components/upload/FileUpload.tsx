'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import { Upload, FileText, X, Loader2, CheckCircle2 } from 'lucide-react'
import { documentsApi } from '@/lib/api/client'
import { toast } from 'sonner'
import { cn } from '@/lib/utils/cn'

interface FileUploadProps {
  onUploadSuccess?: () => void
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [title, setTitle] = useState('')
  const [tags, setTags] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    setSelectedFile(acceptedFiles[0])
    setUploadSuccess(false)
  }, [])

  const handleUpload = async () => {
    if (!selectedFile || uploading) return

    setUploading(true)
    setProgress(0)

    try {
      // Simulate progress (since we don't have real upload progress from backend)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const response = await documentsApi.upload(
        selectedFile,
        title || undefined,
        tags || undefined
      )

      clearInterval(progressInterval)
      setProgress(100)

      toast.success('File uploaded successfully!', {
        description: `${response.filename} indexed with ${response.chunks_created} chunks`,
      })

      // Reset form
      setSelectedFile(null)
      setTitle('')
      setTags('')
      setUploadSuccess(true)
      onUploadSuccess?.()

      // Reset success state after 3 seconds
      setTimeout(() => {
        setUploadSuccess(false)
        setProgress(0)
      }, 3000)
    } catch (error: any) {
      toast.error('Upload failed', {
        description: error.response?.data?.detail || error.message || 'Unknown error',
      })
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  const removeFile = () => {
    setSelectedFile(null)
    setUploadSuccess(false)
    setProgress(0)
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
              isDragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-primary/50',
              uploading && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            {isDragActive ? (
              <p className="text-lg font-medium">Drop the file here...</p>
            ) : (
              <>
                <p className="text-lg font-medium mb-2">
                  Drag & drop a file here, or click to select
                </p>
                <p className="text-sm text-muted-foreground">
                  Supports: PDF, DOCX, TXT, MD (Max 10MB)
                </p>
              </>
            )}
          </div>

          {selectedFile && !uploading && !uploadSuccess && (
            <div className="mt-4 flex items-center justify-between p-3 bg-muted rounded-md">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <span className="text-sm font-medium">{selectedFile.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={removeFile}
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {uploadSuccess && (
            <div className="mt-4 flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950 rounded-md border border-green-200 dark:border-green-800">
              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-green-900 dark:text-green-100">
                File uploaded and indexed successfully!
              </span>
            </div>
          )}

          {uploading && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Uploading...</span>
                <span className="font-medium">{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}
        </CardContent>
      </Card>

      {selectedFile && !uploadSuccess && (
        <Card>
          <CardContent className="p-6 space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Title (optional)
              </label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Document title"
                disabled={uploading}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Tags (optional, comma-separated)
              </label>
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="tag1, tag2, tag3"
                disabled={uploading}
              />
            </div>

            <Button
              onClick={handleUpload}
              disabled={uploading || !selectedFile}
              className="w-full"
              size="lg"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload to Knowledge Base
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
