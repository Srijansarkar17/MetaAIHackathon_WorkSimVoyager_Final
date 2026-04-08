import { useState } from 'react'
import { Send, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react'
import { Button } from '../common/Button'
import { Panel } from '../common/Panel'
import { useBackendAPI } from '../../hooks/useBackendAPI'

type EndpointType = 'health' | 'schema' | 'reset' | 'state' | 'step'

interface Endpoint {
  id: EndpointType
  method: 'GET' | 'POST'
  path: string
  description: string
  requiresBody?: boolean
  bodyTemplate?: any
}

export function ApiExplorer() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<EndpointType>('health')
  const [requestBody, setRequestBody] = useState('')
  const [response, setResponse] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [lastRequestTime, setLastRequestTime] = useState<number | null>(null)

  const { callHealth, callSchema, callReset, callState, callStep } = useBackendAPI()

  const endpoints: Endpoint[] = [
    {
      id: 'health',
      method: 'GET',
      path: '/health',
      description: 'Check if the server is running and healthy'
    },
    {
      id: 'schema',
      method: 'GET',
      path: '/schema',
      description: 'Get the complete API schema for actions and observations'
    },
    {
      id: 'reset',
      method: 'POST',
      path: '/reset',
      description: 'Reset the environment with a new task',
      requiresBody: true,
      bodyTemplate: { task_id: 'inbox_triage_001' }
    },
    {
      id: 'state',
      method: 'GET',
      path: '/state',
      description: 'Get the current episode state'
    },
    {
      id: 'step',
      method: 'POST',
      path: '/step',
      description: 'Take an action in the current episode',
      requiresBody: true,
      bodyTemplate: {
        action: {
          tool: 'mail',
          command: 'classify_email',
          input: { email_id: 'it-e01', classification: 'urgent' }
        }
      }
    }
  ]

  const selectedEndpointData = endpoints.find(e => e.id === selectedEndpoint)!

  const handleSendRequest = async () => {
    setIsLoading(true)
    setLastRequestTime(Date.now())

    try {
      let result
      switch (selectedEndpoint) {
        case 'health':
          result = await callHealth()
          break
        case 'schema':
          result = await callSchema()
          break
        case 'reset':
          const resetBody = requestBody ? JSON.parse(requestBody) : selectedEndpointData.bodyTemplate
          result = await callReset(resetBody?.task_id || 'inbox_triage_001')
          break
        case 'state':
          result = await callState()
          break
        case 'step':
          const stepBody = requestBody ? JSON.parse(requestBody) : selectedEndpointData.bodyTemplate
          result = await callStep(stepBody.action)
          break
        default:
          throw new Error('Unknown endpoint')
      }
      setResponse({ success: true, data: result })
    } catch (error: any) {
      setResponse({
        success: false,
        error: error.message || 'Request failed',
        details: error.response?.data || error
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = () => {
    if (isLoading) return <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
    if (!response) return <Clock className="h-5 w-5 text-slate-400" />
    return response.success
      ? <CheckCircle className="h-5 w-5 text-green-600" />
      : <XCircle className="h-5 w-5 text-red-600" />
  }

  const getStatusText = () => {
    if (isLoading) return 'Sending request...'
    if (!response) return 'Ready to send'
    return response.success ? 'Success' : 'Error'
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">API Explorer</h2>
        <p className="text-slate-600">Test and explore all WorkSim Voyager API endpoints</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Panel */}
        <Panel title="Request">
          <div className="space-y-4">
            {/* Endpoint Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Endpoint
              </label>
              <select
                value={selectedEndpoint}
                onChange={(e) => {
                  setSelectedEndpoint(e.target.value as EndpointType)
                  setRequestBody('')
                  setResponse(null)
                }}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {endpoints.map((endpoint) => (
                  <option key={endpoint.id} value={endpoint.id}>
                    {endpoint.method} {endpoint.path}
                  </option>
                ))}
              </select>
            </div>

            {/* Endpoint Description */}
            <div className="p-3 bg-slate-50 rounded-md">
              <p className="text-sm text-slate-700">{selectedEndpointData.description}</p>
            </div>

            {/* Request Body */}
            {selectedEndpointData.requiresBody && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Request Body (JSON)
                </label>
                <textarea
                  value={requestBody || JSON.stringify(selectedEndpointData.bodyTemplate, null, 2)}
                  onChange={(e) => setRequestBody(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  rows={8}
                  placeholder="Enter JSON request body..."
                />
              </div>
            )}

            {/* Send Button */}
            <Button
              onClick={handleSendRequest}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Request
                </>
              )}
            </Button>
          </div>
        </Panel>

        {/* Response Panel */}
        <Panel title="Response">
          <div className="space-y-4">
            {/* Status */}
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="text-sm font-medium text-slate-700">{getStatusText()}</span>
              {lastRequestTime && (
                <span className="text-xs text-slate-500 ml-auto">
                  {new Date(lastRequestTime).toLocaleTimeString()}
                </span>
              )}
            </div>

            {/* Response Content */}
            {response && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">Response</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    response.success
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {response.success ? 'Success' : 'Error'}
                  </span>
                </div>

                <div className="max-h-96 overflow-y-auto">
                  <pre className={`text-xs p-3 rounded-md ${
                    response.success
                      ? 'bg-green-50 text-green-900'
                      : 'bg-red-50 text-red-900'
                  }`}>
                    {JSON.stringify(response.success ? response.data : response, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {!response && !isLoading && (
              <div className="text-center py-8 text-slate-500">
                <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Send a request to see the response</p>
              </div>
            )}
          </div>
        </Panel>
      </div>

      {/* Quick Actions */}
      <Panel title="Quick Actions" className="mt-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              setSelectedEndpoint('health')
              setTimeout(() => handleSendRequest(), 100)
            }}
            disabled={isLoading}
            className="text-xs"
          >
            Health Check
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              setSelectedEndpoint('schema')
              setTimeout(() => handleSendRequest(), 100)
            }}
            disabled={isLoading}
            className="text-xs"
          >
            Get Schema
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              setSelectedEndpoint('reset')
              setRequestBody(JSON.stringify({ task_id: 'inbox_triage_001' }, null, 2))
              setTimeout(() => handleSendRequest(), 100)
            }}
            disabled={isLoading}
            className="text-xs"
          >
            Reset Episode
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              setSelectedEndpoint('state')
              setTimeout(() => handleSendRequest(), 100)
            }}
            disabled={isLoading}
            className="text-xs"
          >
            Get State
          </Button>
        </div>
      </Panel>
    </div>
  )
}
