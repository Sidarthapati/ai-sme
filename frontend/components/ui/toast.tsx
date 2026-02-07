'use client'

import * as React from "react"
import { cn } from "@/lib/utils/cn"

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "error" | "warning"
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all",
          {
            "bg-background text-foreground": variant === "default",
            "bg-green-50 text-green-900 border-green-200": variant === "success",
            "bg-red-50 text-red-900 border-red-200": variant === "error",
            "bg-yellow-50 text-yellow-900 border-yellow-200": variant === "warning",
          },
          className
        )}
        {...props}
      />
    )
  }
)
Toast.displayName = "Toast"

export { Toast }
