import { ChevronDown, ChevronRight, Mail, MessageSquare, FileText, Calendar, Bug } from 'lucide-react'
import { useState } from 'react'
import { Panel } from '../common/Panel'
import type { Observation } from '../../types/api'

interface InboxPanelProps {
  observation: Observation
}

export function InboxPanel({ observation }: InboxPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['inbox']))

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const getSectionIcon = (section: string) => {
    switch (section) {
      case 'inbox':
        return <Mail className="h-4 w-4" />
      case 'slack':
        return <MessageSquare className="h-4 w-4" />
      case 'drive':
        return <FileText className="h-4 w-4" />
      case 'calendar':
        return <Calendar className="h-4 w-4" />
      case 'jira':
        return <Bug className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  const getSectionTitle = (section: string) => {
    switch (section) {
      case 'inbox':
        return 'Email Inbox'
      case 'slack':
        return 'Slack Messages'
      case 'drive':
        return 'Drive Files'
      case 'calendar':
        return 'Calendar Events'
      case 'jira':
        return 'Jira Tickets'
      default:
        return section.charAt(0).toUpperCase() + section.slice(1)
    }
  }

  const renderEmail = (email: any) => (
    <div key={email.id} className="border border-slate-200 rounded-lg p-3 mb-2 last:mb-0">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="font-medium text-slate-900 truncate">{email.subject}</div>
          <div className="text-sm text-slate-600 truncate">From: {email.sender || email.from}</div>
        </div>
        <div className="text-xs text-slate-500 font-mono ml-2">
          {email.id}
        </div>
      </div>
      <div className="text-sm text-slate-700 line-clamp-2">
        {email.body?.substring(0, 100)}...
      </div>
      {email.timestamp && (
        <div className="text-xs text-slate-500 mt-1">
          {new Date(email.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )

  const renderSlackMessage = (message: any) => (
    <div key={message.id} className="border border-slate-200 rounded-lg p-3 mb-2 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-slate-900">#{message.channel}</div>
        <div className="text-xs text-slate-500 font-mono">{message.id}</div>
      </div>
      <div className="text-sm text-slate-700 mb-1">
        <span className="font-medium">{message.user}:</span> {message.text}
      </div>
      {message.timestamp && (
        <div className="text-xs text-slate-500">
          {new Date(message.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )

  const renderDriveFile = (file: any) => (
    <div key={file.id} className="border border-slate-200 rounded-lg p-3 mb-2 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-slate-900">{file.title}</div>
        <div className="text-xs text-slate-500 font-mono">{file.id}</div>
      </div>
      <div className="text-sm text-slate-700 mb-1">
        {file.content?.substring(0, 100)}...
      </div>
      <div className="text-xs text-slate-500">
        Type: {file.type} • Modified: {file.last_modified ? new Date(file.last_modified).toLocaleString() : 'Unknown'}
      </div>
    </div>
  )

  const renderCalendarEvent = (event: any) => (
    <div key={event.id} className="border border-slate-200 rounded-lg p-3 mb-2 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-slate-900">{event.title}</div>
        <div className="text-xs text-slate-500 font-mono">{event.id}</div>
      </div>
      <div className="text-sm text-slate-700 mb-1">
        {event.description || 'No description'}
      </div>
      <div className="text-xs text-slate-500">
        {event.start} - {event.end} • Attendees: {event.attendees?.join(', ') || 'None'}
      </div>
    </div>
  )

  const renderJiraTicket = (ticket: any) => (
    <div key={ticket.id} className="border border-slate-200 rounded-lg p-3 mb-2 last:mb-0">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-slate-900">{ticket.title}</div>
        <div className="text-xs text-slate-500 font-mono">{ticket.id}</div>
      </div>
      <div className="flex gap-2 mb-2">
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {ticket.severity}
        </span>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          {ticket.priority}
        </span>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          {ticket.status}
        </span>
      </div>
      <div className="text-sm text-slate-700 mb-1">
        {ticket.description?.substring(0, 100)}...
      </div>
      <div className="text-xs text-slate-500">
        Assignee: {ticket.assignee}
      </div>
    </div>
  )

  const renderSection = (section: string, data: any[]) => {
    const isExpanded = expandedSections.has(section)
    const itemCount = data?.length || 0

    return (
      <div key={section} className="border-b border-slate-200 last:border-b-0">
        <button
          onClick={() => toggleSection(section)}
          className="w-full flex items-center justify-between p-3 hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            {getSectionIcon(section)}
            <span className="font-medium text-slate-900">{getSectionTitle(section)}</span>
            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-full">
              {itemCount}
            </span>
          </div>
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
        </button>

        {isExpanded && (
          <div className="px-3 pb-3">
            {itemCount === 0 ? (
              <div className="text-sm text-slate-500 italic">No items in this section</div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {data?.map((item) => {
                  switch (section) {
                    case 'inbox':
                      return renderEmail(item)
                    case 'slack':
                      return renderSlackMessage(item)
                    case 'drive':
                      return renderDriveFile(item)
                    case 'calendar':
                      return renderCalendarEvent(item)
                    case 'jira':
                      return renderJiraTicket(item)
                    default:
                      return (
                        <div key={item.id} className="text-sm text-slate-600">
                          {JSON.stringify(item, null, 2)}
                        </div>
                      )
                  }
                })}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const sections = Object.keys(observation)

  return (
    <Panel title="Workspace Inbox">
      <div className="divide-y divide-slate-200">
        {sections.map((section) => renderSection(section, (observation as any)[section]))}
      </div>
    </Panel>
  )
}
