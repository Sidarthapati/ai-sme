'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message as MessageType } from '@/lib/store/chat'
import { cn } from '@/lib/utils/cn'
import { Card, CardContent } from '@/components/ui/card'
import { ExternalLink, FileText } from 'lucide-react'
import { format } from 'date-fns'
import { useEffect, useState } from 'react'

interface MessageProps {
  message: MessageType
}

export function Message({ message }: MessageProps) {
  const [SyntaxHighlighter, setSyntaxHighlighter] = useState<any>(null)
  const [vscDarkPlus, setVscDarkPlus] = useState<any>(null)

  useEffect(() => {
    // Dynamic import for syntax highlighter to avoid SSR issues
    import('react-syntax-highlighter').then((mod) => {
      setSyntaxHighlighter(() => mod.Prism)
    })
    import('react-syntax-highlighter/dist/esm/styles/prism').then((mod) => {
      setVscDarkPlus(mod.vscDarkPlus)
    })
  }, [])

  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'flex w-full mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'flex flex-col max-w-[85%]',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'rounded-lg px-4 py-3',
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-foreground'
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    if (!inline && match && SyntaxHighlighter && vscDarkPlus) {
                      return (
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          className="rounded-md"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      )
                    }
                    return (
                      <code
                        className={cn(
                          'bg-muted px-1.5 py-0.5 rounded text-sm',
                          className
                        )}
                        {...props}
                      >
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.sources.map((source, idx) => (
              <Card key={idx} className="p-2">
                <CardContent className="p-0">
                  <a
                    href={source.url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <FileText className="h-3 w-3" />
                    <span className="truncate max-w-[200px]">
                      {source.title}
                    </span>
                    {source.url && (
                      <ExternalLink className="h-3 w-3 flex-shrink-0" />
                    )}
                  </a>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <span className="text-xs text-muted-foreground mt-1">
          {format(message.timestamp, 'HH:mm')}
        </span>
      </div>
    </div>
  )
}
