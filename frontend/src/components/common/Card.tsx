import type { PropsWithChildren } from 'react'
import { cn } from '../../utils/formatters'

interface CardProps {
  className?: string
}

export function Card({ className = '', children }: PropsWithChildren<CardProps>) {
  return (
    <div className={cn('rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60', className)}>
      {children}
    </div>
  )
}
