import type { PropsWithChildren } from 'react'
import { cn } from '../../utils/formatters'

interface PanelProps {
  title: string
  className?: string
}

export function Panel({ title, className = '', children }: PropsWithChildren<PanelProps>) {
  return (
    <section className={cn('rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60', className)}>
      <div className="mb-5 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      </div>
      {children}
    </section>
  )
}
