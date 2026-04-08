import { useState, useEffect } from 'react'
import { Database, ChevronRight, ChevronDown, Search, FileText, Settings } from 'lucide-react'
import { Panel } from '../common/Panel'
import { useBackendAPI } from '../../hooks/useBackendAPI'

interface SchemaData {
  action: any
  observation: any
  state: any
}

export function SchemaViewer() {
  const [schema, setSchema] = useState<SchemaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['action']))

  const { callSchema } = useBackendAPI()

  useEffect(() => {
    loadSchema()
  }, [])

  const loadSchema = async () => {
    try {
      setLoading(true)
      const schemaData = await callSchema()
      setSchema(schemaData)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load schema')
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const renderSchemaObject = (obj: any, path: string = '', level: number = 0): React.ReactElement => {
    if (!obj || typeof obj !== 'object') {
      return (
        <span className="text-slate-600">
          {typeof obj === 'string' ? `"${obj}"` : String(obj)}
        </span>
      )
    }

    const indent = '  '.repeat(level)
    const entries = Object.entries(obj)

    // Filter entries based on search term
    const filteredEntries = searchTerm
      ? entries.filter(([key, value]) =>
          key.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (typeof value === 'string' && value.toLowerCase().includes(searchTerm.toLowerCase()))
        )
      : entries

    return (
      <div className="font-mono text-sm">
        {'{'}
        {filteredEntries.map(([key, value], index) => {
          const isLast = index === filteredEntries.length - 1
          const currentPath = path ? `${path}.${key}` : key
          const shouldHighlight = searchTerm &&
            (key.toLowerCase().includes(searchTerm.toLowerCase()) ||
             (typeof value === 'string' && value.toLowerCase().includes(searchTerm.toLowerCase())))

          return (
            <div key={key} className={`${indent}  pl-4 ${shouldHighlight ? 'bg-yellow-100' : ''}`}>
              <span className="text-blue-600">"{key}"</span>
              <span className="text-slate-500">:</span>{' '}
              {typeof value === 'object' && value !== null ? (
                <div className="inline">
                  {Array.isArray(value) ? (
                    <>
                      [
                      {value.map((item, i) => (
                        <div key={i} className={`${indent}    pl-4`}>
                          {renderSchemaObject(item, `${currentPath}[${i}]`, level + 2)}
                          {i < value.length - 1 && ','}
                        </div>
                      ))}
                      {indent}  ]
                    </>
                  ) : (
                    renderSchemaObject(value, currentPath, level + 1)
                  )}
                </div>
              ) : (
                <>
                  {renderSchemaObject(value, currentPath, level)}
                  {!isLast && ','}
                </>
              )}
            </div>
          )
        })}
        {indent}{'}'}
      </div>
    )
  }

  const getSectionIcon = (section: string) => {
    switch (section) {
      case 'action':
        return <Settings className="h-4 w-4" />
      case 'observation':
        return <Database className="h-4 w-4" />
      case 'state':
        return <FileText className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  const getSectionDescription = (section: string) => {
    switch (section) {
      case 'action':
        return 'Defines the structure of actions agents can take'
      case 'observation':
        return 'Describes the data returned after each action'
      case 'state':
        return 'Shows the current state of the environment'
      default:
        return ''
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <Database className="h-8 w-8 animate-pulse text-slate-400 mx-auto mb-4" />
          <p className="text-slate-600">Loading schema...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <Panel title="Schema Viewer">
          <div className="text-center py-8">
            <div className="text-red-600 font-medium mb-2">Failed to load schema</div>
            <div className="text-sm text-slate-600 mb-4">{error}</div>
            <button
              onClick={loadSchema}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </Panel>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Schema Viewer</h2>
        <p className="text-slate-600">Explore the complete API schema for actions, observations, and state</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search schema..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Schema Sections */}
      <div className="space-y-4">
        {schema && Object.entries(schema).map(([sectionName, sectionData]) => {
          const isExpanded = expandedSections.has(sectionName)

          return (
            <Panel key={sectionName} title={`${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)} Schema`}>
              <div className="space-y-3">
                {/* Section Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getSectionIcon(sectionName)}
                    <span className="font-medium text-slate-900 capitalize">{sectionName}</span>
                  </div>
                  <button
                    onClick={() => toggleSection(sectionName)}
                    className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        Collapse
                      </>
                    ) : (
                      <>
                        <ChevronRight className="h-4 w-4" />
                        Expand
                      </>
                    )}
                  </button>
                </div>

                {/* Section Description */}
                <p className="text-sm text-slate-600">{getSectionDescription(sectionName)}</p>

                {/* Schema Content */}
                {isExpanded && (
                  <div className="border border-slate-200 rounded-md p-4 bg-slate-50 overflow-x-auto">
                    {renderSchemaObject(sectionData)}
                  </div>
                )}
              </div>
            </Panel>
          )
        })}
      </div>

      {/* Schema Tips */}
      <Panel title="Understanding the Schema" className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-slate-900 mb-2">Action Schema</h4>
            <ul className="text-sm text-slate-600 space-y-1">
              <li>• <strong>tool</strong>: Which workplace tool to use (mail, slack, drive, calendar, jira)</li>
              <li>• <strong>command</strong>: Specific action within the tool</li>
              <li>• <strong>input</strong>: Parameters required for the command</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-slate-900 mb-2">Observation Schema</h4>
            <ul className="text-sm text-slate-600 space-y-1">
              <li>• Contains data from all 5 workplace tools</li>
              <li>• <strong>emails</strong>, <strong>slack_messages</strong>, etc.</li>
              <li>• Updated after each action is taken</li>
            </ul>
          </div>
        </div>
      </Panel>
    </div>
  )
}
