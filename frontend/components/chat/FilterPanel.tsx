'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Filter } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface FilterPanelProps {
  sourceType?: string | null
  onSourceTypeChange?: (sourceType: string | null) => void
}

export function FilterPanel({
  sourceType,
  onSourceTypeChange,
}: FilterPanelProps) {
  const filters = [
    { value: null, label: 'All Sources', description: 'Search both docs and code' },
    { value: 'confluence', label: 'Documentation', description: 'Confluence docs only' },
    { value: 'github', label: 'Code', description: 'GitHub code only' },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Filter className="h-4 w-4" />
          Source Filter
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {filters.map((filter) => (
          <Button
            key={filter.value || 'all'}
            variant={sourceType === filter.value ? 'default' : 'outline'}
            className={cn(
              'w-full justify-start text-left h-auto py-2',
              sourceType === filter.value && 'bg-primary text-primary-foreground'
            )}
            onClick={() => onSourceTypeChange?.(filter.value)}
          >
            <div className="flex flex-col items-start">
              <span className="font-medium">{filter.label}</span>
              <span className="text-xs opacity-80">{filter.description}</span>
            </div>
          </Button>
        ))}
      </CardContent>
    </Card>
  )
}
