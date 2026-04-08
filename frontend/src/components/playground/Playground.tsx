import { useState } from 'react'
import { Code, Database, Wrench, Eye, FileText } from 'lucide-react'
import { Panel } from '../common/Panel'
import { ApiExplorer } from './ApiExplorer'
import { SchemaViewer } from './SchemaViewer'
import { ToolSandbox } from './ToolSandbox'

type PlaygroundSection = 'api-explorer' | 'schema-viewer' | 'tool-sandbox'

export function Playground() {
  const [activeSection, setActiveSection] = useState<PlaygroundSection>('api-explorer')

  const sections = [
    {
      id: 'api-explorer' as PlaygroundSection,
      title: 'API Explorer',
      description: 'Test all backend endpoints interactively',
      icon: Code,
      component: ApiExplorer
    },
    {
      id: 'schema-viewer' as PlaygroundSection,
      title: 'Schema Viewer',
      description: 'Explore action and observation schemas',
      icon: Database,
      component: SchemaViewer
    },
    {
      id: 'tool-sandbox' as PlaygroundSection,
      title: 'Tool Sandbox',
      description: 'Experiment with workplace tools safely',
      icon: Wrench,
      component: ToolSandbox
    }
  ]

  const ActiveComponent = sections.find(s => s.id === activeSection)?.component || ApiExplorer

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">WorkSim Voyager Playground</h1>
        <p className="text-slate-600">Explore, learn, and experiment with the workplace simulation environment</p>
      </div>

      {/* Section Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {sections.map((section) => {
          const Icon = section.icon
          const isActive = activeSection === section.id

          return (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`p-6 rounded-lg border-2 transition-all duration-200 text-left ${
                isActive
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={`p-2 rounded-lg ${isActive ? 'bg-blue-100' : 'bg-slate-100'}`}>
                  <Icon className={`h-6 w-6 ${isActive ? 'text-blue-600' : 'text-slate-600'}`} />
                </div>
                <h3 className={`font-semibold ${isActive ? 'text-blue-900' : 'text-slate-900'}`}>
                  {section.title}
                </h3>
              </div>
              <p className={`text-sm ${isActive ? 'text-blue-700' : 'text-slate-600'}`}>
                {section.description}
              </p>
            </button>
          )
        })}
      </div>

      {/* Active Section Content */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200">
        <ActiveComponent />
      </div>

      {/* Learning Tips */}
      <Panel title="Learning Tips" className="mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
              <Eye className="h-4 w-4 text-blue-600" />
              How to Use the Playground
            </h4>
            <ul className="text-sm text-slate-600 space-y-1">
              <li>• Start with the <strong>API Explorer</strong> to understand endpoint responses</li>
              <li>• Use the <strong>Schema Viewer</strong> to learn about valid actions and observations</li>
              <li>• Experiment in the <strong>Tool Sandbox</strong> to see how tools work</li>
              <li>• All playground actions are safe and don't affect real episodes</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
              <FileText className="h-4 w-4 text-green-600" />
              What You'll Learn
            </h4>
            <ul className="text-sm text-slate-600 space-y-1">
              <li>• How workplace tools interact and respond</li>
              <li>• The structure of actions and observations</li>
              <li>• Reward mechanics and scoring systems</li>
              <li>• Best practices for agent development</li>
            </ul>
          </div>
        </div>
      </Panel>
    </div>
  )
}
