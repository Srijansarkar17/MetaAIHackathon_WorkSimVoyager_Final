import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '../common/Button'
import { Panel } from '../common/Panel'
import { useBackendAPI } from '../../hooks/useBackendAPI'
import type { Action } from '../../types/api'

interface ActionFormProps {
  onActionSubmitted: (action: Action) => void
  disabled?: boolean
}

export function ActionForm({ onActionSubmitted, disabled = false }: ActionFormProps) {
  const [actionType, setActionType] = useState<string>('')
  const [parameters, setParameters] = useState<Record<string, any>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { callStep } = useBackendAPI()

  const actionTypes = [
    { value: 'send_email', label: 'Send Email', description: 'Send an email to a recipient' },
    { value: 'read_email', label: 'Read Email', description: 'Read the content of an email' },
    { value: 'create_file', label: 'Create File', description: 'Create a new file in Drive' },
    { value: 'edit_file', label: 'Edit File', description: 'Edit an existing file in Drive' },
    { value: 'search_files', label: 'Search Files', description: 'Search for files in Drive' },
    { value: 'create_event', label: 'Create Event', description: 'Create a calendar event' },
    { value: 'list_events', label: 'List Events', description: 'List calendar events' },
    { value: 'send_message', label: 'Send Message', description: 'Send a Slack message' },
    { value: 'read_messages', label: 'Read Messages', description: 'Read Slack messages' },
    { value: 'create_ticket', label: 'Create Ticket', description: 'Create a Jira ticket' },
    { value: 'update_ticket', label: 'Update Ticket', description: 'Update a Jira ticket' },
    { value: 'search_tickets', label: 'Search Tickets', description: 'Search Jira tickets' },
  ]

  const getParameterFields = (actionType: string) => {
    switch (actionType) {
      case 'send_email':
        return [
          { name: 'to', label: 'To', type: 'email', required: true },
          { name: 'subject', label: 'Subject', type: 'text', required: true },
          { name: 'body', label: 'Body', type: 'textarea', required: true },
        ]
      case 'read_email':
        return [
          { name: 'email_id', label: 'Email ID', type: 'text', required: true },
        ]
      case 'create_file':
        return [
          { name: 'title', label: 'File Title', type: 'text', required: true },
          { name: 'content', label: 'Content', type: 'textarea', required: true },
          { name: 'type', label: 'File Type', type: 'select', options: ['document', 'spreadsheet', 'presentation'], required: true },
        ]
      case 'edit_file':
        return [
          { name: 'file_id', label: 'File ID', type: 'text', required: true },
          { name: 'content', label: 'New Content', type: 'textarea', required: true },
        ]
      case 'search_files':
        return [
          { name: 'query', label: 'Search Query', type: 'text', required: true },
        ]
      case 'create_event':
        return [
          { name: 'title', label: 'Event Title', type: 'text', required: true },
          { name: 'start', label: 'Start Time', type: 'datetime-local', required: true },
          { name: 'end', label: 'End Time', type: 'datetime-local', required: true },
          { name: 'attendees', label: 'Attendees (comma-separated)', type: 'text', required: false },
          { name: 'description', label: 'Description', type: 'textarea', required: false },
        ]
      case 'list_events':
        return [
          { name: 'start_date', label: 'Start Date', type: 'date', required: false },
          { name: 'end_date', label: 'End Date', type: 'date', required: false },
        ]
      case 'send_message':
        return [
          { name: 'channel', label: 'Channel', type: 'text', required: true },
          { name: 'text', label: 'Message', type: 'textarea', required: true },
        ]
      case 'read_messages':
        return [
          { name: 'channel', label: 'Channel', type: 'text', required: true },
          { name: 'limit', label: 'Limit', type: 'number', required: false },
        ]
      case 'create_ticket':
        return [
          { name: 'title', label: 'Ticket Title', type: 'text', required: true },
          { name: 'description', label: 'Description', type: 'textarea', required: true },
          { name: 'severity', label: 'Severity', type: 'select', options: ['low', 'medium', 'high', 'critical'], required: true },
          { name: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high'], required: true },
        ]
      case 'update_ticket':
        return [
          { name: 'ticket_id', label: 'Ticket ID', type: 'text', required: true },
          { name: 'status', label: 'New Status', type: 'select', options: ['open', 'in_progress', 'resolved', 'closed'], required: true },
        ]
      case 'search_tickets':
        return [
          { name: 'query', label: 'Search Query', type: 'text', required: true },
        ]
      default:
        return []
    }
  }

  const handleParameterChange = (name: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!actionType || disabled || isSubmitting) return

    setIsSubmitting(true)
    try {
      const action: Action = {
        action_type: actionType,
        parameters: parameters
      }

      const response = await callStep(action)
      if (response) {
        onActionSubmitted(action)
        // Reset form
        setActionType('')
        setParameters({})
      }
    } catch (error) {
      console.error('Failed to submit action:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const selectedActionType = actionTypes.find(type => type.value === actionType)
  const parameterFields = getParameterFields(actionType)

  return (
    <Panel title="Take Action">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Action Type
          </label>
          <select
            value={actionType}
            onChange={(e) => {
              setActionType(e.target.value)
              setParameters({})
            }}
            className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={disabled || isSubmitting}
          >
            <option value="">Select an action...</option>
            {actionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          {selectedActionType && (
            <p className="text-sm text-slate-600 mt-1">
              {selectedActionType.description}
            </p>
          )}
        </div>

        {parameterFields.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">Parameters</h4>
            {parameterFields.map((field) => (
              <div key={field.name}>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                {field.type === 'textarea' ? (
                  <textarea
                    value={parameters[field.name] || ''}
                    onChange={(e) => handleParameterChange(field.name, e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    rows={3}
                    disabled={disabled || isSubmitting}
                    required={field.required}
                  />
                ) : field.type === 'select' ? (
                  <select
                    value={parameters[field.name] || ''}
                    onChange={(e) => handleParameterChange(field.name, e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={disabled || isSubmitting}
                    required={field.required}
                  >
                    <option value="">Select...</option>
                    {field.options?.map((option) => (
                      <option key={option} value={option}>
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={field.type}
                    value={parameters[field.name] || ''}
                    onChange={(e) => handleParameterChange(field.name, e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={disabled || isSubmitting}
                    required={field.required}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        <Button
          type="submit"
          disabled={!actionType || disabled || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Submit Action
            </>
          )}
        </Button>
      </form>
    </Panel>
  )
}
