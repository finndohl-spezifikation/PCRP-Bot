import * as React from "react"
import { cn } from "@/lib/utils"

const Avatar = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { src?: string; fallback?: string; bgColor?: string }
>(({ className, src, fallback, bgColor, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full",
        className
      )}
      style={bgColor ? { backgroundColor: bgColor } : { backgroundColor: '#dfe5e7' }}
      {...props}
    >
      {src ? (
        <img
          src={src}
          alt="Avatar"
          className="aspect-square h-full w-full"
        />
      ) : (
        <span className="flex h-full w-full items-center justify-center font-medium text-white">
          {fallback}
        </span>
      )}
    </div>
  )
})
Avatar.displayName = "Avatar"

export { Avatar }
