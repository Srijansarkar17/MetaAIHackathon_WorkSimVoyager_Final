import { useState } from 'react'
import { CheckCircle2, Clock, Target, Zap } from 'lucide-react'
import { Button } from '../common/Button'
import { Card } from '../common/Card'
import { Panel } from '../common/Panel'
import { tasks, type TaskCard } from '../../types/game'
import { useBackendAPI } from '../../hooks/useBackendAPI'

interface TaskSelectionProps {
  onTaskSelect: (task: TaskCard) => void
  disabled?: boolean
}

export function TaskSelection({ onTaskSelect, disabled = false }: TaskSelectionProps) {
  const [selectedTask, setSelectedTask] = useState<TaskCard | null>(null)
  const { callHealth, loading, error } = useBackendAPI()

  const getDifficultyColor = (difficulty: TaskCard['difficulty']) => {
    switch (difficulty) {
      case 'easy':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'hard':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'original':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getDifficultyIcon = (difficulty: TaskCard['difficulty']) => {
    switch (difficulty) {
      case 'easy':
        return <CheckCircle2 className="h-4 w-4" />
      case 'medium':
        return <Target className="h-4 w-4" />
      case 'hard':
        return <Zap className="h-4 w-4" />
      case 'original':
        return <Clock className="h-4 w-4" />
      default:
        return <Target className="h-4 w-4" />
    }
  }

  const handleTaskSelect = (task: TaskCard) => {
    setSelectedTask(task)
    onTaskSelect(task)
  }

  const handleTestConnection = async () => {
    await callHealth()
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-slate-900 mb-4">WorkSim Voyager</h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Choose a workplace simulation task and test your agent capabilities across email, Slack, Drive, Calendar, and Jira tools.
        </p>
      </div>

      <Panel title="Available Tasks">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tasks.map((task) => (
            <button
              key={task.id}
              onClick={() => handleTaskSelect(task)}
              disabled={disabled}
              className="w-full text-left disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Card className={`transition-all duration-200 ${
                selectedTask?.id === task.id
                  ? 'ring-2 ring-blue-500 bg-blue-50'
                  : 'hover:shadow-md'
              }`}>
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {getDifficultyIcon(task.difficulty)}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getDifficultyColor(task.difficulty)}`}>
                      {task.difficulty}
                    </span>
                  </div>
                  <span className="text-sm text-slate-500">
                    ~{task.estimatedSteps} steps
                  </span>
                </div>

                <div>
                  <h3 className="font-semibold text-slate-900 mb-2">{task.name}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{task.description}</p>
                </div>

                <div className="text-xs text-slate-500 font-mono">
                  Task ID: {task.id}
                </div>
              </div>
            </Card>
            </button>
          ))}
        </div>
      </Panel>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={handleTestConnection}
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Test Backend Connection'}
          </Button>
          {error && (
            <span className="text-sm text-red-600">{error}</span>
          )}
        </div>

        <Button
          variant="primary"
          onClick={() => selectedTask && handleTaskSelect(selectedTask)}
          disabled={!selectedTask}
          className="min-w-[120px]"
        >
          {selectedTask ? `Start ${selectedTask.name}` : 'Select a Task'}
        </Button>
      </div>
    </div>
  )
}
