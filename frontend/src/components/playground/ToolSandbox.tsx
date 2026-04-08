import { useState, useEffect } from 'react'
import { Wrench, Play, RotateCcw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { Button } from '../common/Button'
import { Panel } from '../common/Panel'
import { useBackendAPI } from '../../hooks/useBackendAPI'

interface ToolCommand {
  tool: string
  command: string
  description: string
  inputSchema: any
  exampleInput: any
}

const AVAILABLE_TOOLS: Record<string, ToolCommand[]> = {
  mail: [
    {
      tool: 'mail',
      command: 'list_inbox',
      description: 'List all emails in the inbox',
      inputSchema: {},
      exampleInput: {}
    },
    {
      tool: 'mail',
      command: 'read_email',
      description: 'Read the content of a specific email',
      inputSchema: { email_id: 'string' },
      exampleInput: { email_id: 'it-e01' }
    },
    {
      tool: 'mail',
      command: 'classify_email',
      description: 'Classify an email as urgent or non-urgent',
      inputSchema: { email_id: 'string', classification: 'urgent|non-urgent' },
      exampleInput: { email_id: 'it-e01', classification: 'urgent' }
    },
    {
      tool: 'mail',
      command: 'send_email',
      description: 'Send a new email',
      inputSchema: { to: 'string', subject: 'string', body: 'string' },
      exampleInput: { to: 'user@company.com', subject: 'Test email', body: 'This is a test message.' }
    }
  ],
  slack: [
    {
      tool: 'slack',
      command: 'list_channels',
      description: 'List all Slack channels',
      inputSchema: {},
      exampleInput: {}
    },
    {
      tool: 'slack',
      command: 'read_channel',
      description: 'Read messages from a specific channel',
      inputSchema: { channel: 'string' },
      exampleInput: { channel: 'general' }
    },
    {
      tool: 'slack',
      command: 'send_message',
      description: 'Send a message to a channel',
      inputSchema: { channel: 'string', text: 'string' },
      exampleInput: { channel: 'general', text: 'Hello from the sandbox!' }
    }
  ],
  drive: [
    {
      tool: 'drive',
      command: 'list_files',
      description: 'List all files in Drive',
      inputSchema: {},
      exampleInput: {}
    },
    {
      tool: 'drive',
      command: 'read_file',
      description: 'Read the content of a specific file',
      inputSchema: { file_id: 'string' },
      exampleInput: { file_id: 'doc-001' }
    },
    {
      tool: 'drive',
      command: 'create_file',
      description: 'Create a new file',
      inputSchema: { title: 'string', content: 'string', type: 'document|spreadsheet|presentation' },
      exampleInput: { title: 'New Document', content: 'This is a new document.', type: 'document' }
    }
  ],
  calendar: [
    {
      tool: 'calendar',
      command: 'list_events',
      description: 'List all calendar events',
      inputSchema: {},
      exampleInput: {}
    },
    {
      tool: 'calendar',
      command: 'check_availability',
      description: 'Check availability for attendees on a date',
      inputSchema: { date: 'string', attendees: 'string[]' },
      exampleInput: { date: '2026-04-08', attendees: ['alice.chen@acme.com'] }
    },
    {
      tool: 'calendar',
      command: 'create_event',
      description: 'Create a new calendar event',
      inputSchema: { title: 'string', start: 'string', end: 'string', attendees: 'string[]' },
      exampleInput: {
        title: 'Team Meeting',
        start: '2026-04-08T10:00:00Z',
        end: '2026-04-08T11:00:00Z',
        attendees: ['alice.chen@acme.com']
      }
    }
  ],
  jira: [
    {
      tool: 'jira',
      command: 'list_tickets',
      description: 'List all Jira tickets',
      inputSchema: {},
      exampleInput: {}
    },
    {
      tool: 'jira',
      command: 'get_ticket',
      description: 'Get details of a specific ticket',
      inputSchema: { ticket_id: 'string' },
      exampleInput: { ticket_id: 'PHOENIX-101' }
    },
    {
      tool: 'jira',
      command: 'update_ticket',
      description: 'Update a ticket\'s properties',
      inputSchema: { ticket_id: 'string', status: 'string', assignee: 'string' },
      exampleInput: { ticket_id: 'PHOENIX-101', status: 'in_progress', assignee: 'bob.kumar@acme.com' }
    }
  ]
}

export function ToolSandbox() {
  const [selectedTool, setSelectedTool] = useState<string>('mail')
  const [selectedCommand, setSelectedCommand] = useState<string>('')
  const [inputData, setInputData] = useState<string>('')
  const [result, setResult] = useState<any>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [episodeStarted, setEpisodeStarted] = useState(false)

  const { callReset, callStep } = useBackendAPI()

  useEffect(() => {
    // Reset to first command when tool changes
    const toolCommands = AVAILABLE_TOOLS[selectedTool]
    if (toolCommands && toolCommands.length > 0) {
      setSelectedCommand(toolCommands[0].command)
      setInputData(JSON.stringify(toolCommands[0].exampleInput, null, 2))
    }
  }, [selectedTool])

  const handleToolChange = (tool: string) => {
    setSelectedTool(tool)
    setResult(null)
  }

  const handleCommandChange = (command: string) => {
    setSelectedCommand(command)
    const toolCommands = AVAILABLE_TOOLS[selectedTool]
    const commandData = toolCommands.find(c => c.command === command)
    if (commandData) {
      setInputData(JSON.stringify(commandData.exampleInput, null, 2))
    }
    setResult(null)
  }

  const startEpisode = async () => {
    try {
      setIsExecuting(true)
      const response = await callReset('inbox_triage_001')
      if (response) {
        setEpisodeStarted(true)
        setResult({ type: 'success', message: 'Episode started successfully', data: response })
      }
    } catch (error: any) {
      setResult({ type: 'error', message: error.message || 'Failed to start episode' })
    } finally {
      setIsExecuting(false)
    }
  }

  const executeCommand = async () => {
    if (!episodeStarted) {
      setResult({ type: 'error', message: 'Please start an episode first' })
      return
    }

    try {
      setIsExecuting(true)
      const action = {
        action_type: `${selectedTool}.${selectedCommand}`,
        parameters: JSON.parse(inputData)
      }

      const response = await callStep(action)
      if (response) {
        setResult({
          type: 'success',
          message: 'Command executed successfully',
          data: response,
          action: action
        })
      }
    } catch (error: any) {
      setResult({
        type: 'error',
        message: error.message || 'Command execution failed',
        action: {
          tool: selectedTool,
          command: selectedCommand,
          input: JSON.parse(inputData)
        }
      })
    } finally {
      setIsExecuting(false)
    }
  }

  const resetSandbox = () => {
    setResult(null)
    setEpisodeStarted(false)
  }

  const toolCommands = AVAILABLE_TOOLS[selectedTool] || []
  const selectedCommandData = toolCommands.find(c => c.command === selectedCommand)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Tool Sandbox</h2>
        <p className="text-slate-600">Experiment with workplace tools in a safe environment</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tool Configuration */}
        <Panel title="Tool Configuration">
          <div className="space-y-4">
            {/* Episode Status */}
            <div className="flex items-center justify-between p-3 rounded-md border">
              <div className="flex items-center gap-2">
                {episodeStarted ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                )}
                <span className="text-sm font-medium">
                  {episodeStarted ? 'Episode Active' : 'No Active Episode'}
                </span>
              </div>
              <div className="flex gap-2">
                {!episodeStarted ? (
                  <Button
                    onClick={startEpisode}
                    disabled={isExecuting}
                    className="text-xs px-3 py-1"
                  >
                    Start Episode
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    onClick={resetSandbox}
                    disabled={isExecuting}
                    className="text-xs px-3 py-1"
                  >
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Reset
                  </Button>
                )}
              </div>
            </div>

            {/* Tool Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Workplace Tool
              </label>
              <select
                value={selectedTool}
                onChange={(e) => handleToolChange(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {Object.keys(AVAILABLE_TOOLS).map((tool) => (
                  <option key={tool} value={tool}>
                    {tool.charAt(0).toUpperCase() + tool.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Command Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Command
              </label>
              <select
                value={selectedCommand}
                onChange={(e) => handleCommandChange(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {toolCommands.map((cmd) => (
                  <option key={cmd.command} value={cmd.command}>
                    {cmd.command}
                  </option>
                ))}
              </select>
            </div>

            {/* Command Description */}
            {selectedCommandData && (
              <div className="p-3 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">{selectedCommandData.description}</p>
              </div>
            )}

            {/* Input Parameters */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Input Parameters (JSON)
              </label>
              <textarea
                value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                rows={6}
                placeholder="Enter JSON input parameters..."
              />
            </div>

            {/* Execute Button */}
            <Button
              onClick={executeCommand}
              disabled={!episodeStarted || isExecuting}
              className="w-full"
            >
              {isExecuting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Executing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Execute Command
                </>
              )}
            </Button>
          </div>
        </Panel>

        {/* Results */}
        <Panel title="Execution Results">
          <div className="space-y-4">
            {result ? (
              <>
                {/* Result Status */}
                <div className="flex items-center gap-2">
                  {result.type === 'success' ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                  <span className={`text-sm font-medium ${
                    result.type === 'success' ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {result.type === 'success' ? 'Success' : 'Error'}
                  </span>
                </div>

                {/* Result Message */}
                <div className="p-3 rounded-md bg-slate-50">
                  <p className="text-sm text-slate-700">{result.message}</p>
                </div>

                {/* Action Details */}
                {result.action && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-2">Executed Action</h4>
                    <pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto">
                      {JSON.stringify(result.action, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Response Data */}
                {result.data && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-2">Response Data</h4>
                    <div className="max-h-64 overflow-y-auto">
                      <pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-slate-500">
                <Wrench className="h-8 w-8 mx-auto mb-4 opacity-50" />
                <p className="text-sm mb-2">No execution results yet</p>
                <p className="text-xs">Start an episode and execute a command to see results</p>
              </div>
            )}
          </div>
        </Panel>
      </div>

      {/* Tool Information */}
      <Panel title="Available Tools" className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(AVAILABLE_TOOLS).map(([toolName, commands]) => (
            <div key={toolName} className="p-4 border border-slate-200 rounded-lg">
              <h4 className="font-medium text-slate-900 mb-2 capitalize">{toolName}</h4>
              <ul className="text-sm text-slate-600 space-y-1">
                {commands.slice(0, 3).map((cmd) => (
                  <li key={cmd.command} className="flex items-center gap-2">
                    <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
                    {cmd.command}
                  </li>
                ))}
                {commands.length > 3 && (
                  <li className="text-xs text-slate-500">
                    +{commands.length - 3} more commands
                  </li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
