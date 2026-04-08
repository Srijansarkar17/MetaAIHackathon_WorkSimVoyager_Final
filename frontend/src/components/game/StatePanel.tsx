import { Clock, Target, Trophy, Zap } from 'lucide-react'
import { Panel } from '../common/Panel'
import type { State } from '../../types/api'

interface StatePanelProps {
  state: State
}

export function StatePanel({ state }: StatePanelProps) {
  const maxSteps = 40 // Could be made configurable
  const { episode_id, task_id, steps, score, status } = state
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getRewardColor = (reward: number) => {
    if (reward > 0.5) return 'text-green-600'
    if (reward > 0) return 'text-yellow-600'
    if (reward < -0.1) return 'text-red-600'
    return 'text-slate-600'
  }

  return (
    <Panel title="Episode State">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">Episode ID</div>
            <div className="font-mono text-sm text-slate-900">{episode_id}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">Task</div>
            <div className="font-mono text-sm text-slate-900">{task_id}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">Steps</div>
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-slate-400" />
              <span className="font-semibold text-slate-900">
                {steps} / {maxSteps}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-slate-900 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min((steps / maxSteps) * 100, 100)}%` }}
              />
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">Score</div>
            <div className="flex items-center gap-2">
              <Trophy className={`h-4 w-4 ${getRewardColor(score)}`} />
              <span className={`font-semibold ${getRewardColor(score)}`}>
                {score.toFixed(3)}
              </span>
            </div>
            <div className="text-xs text-slate-500">
              Cumulative reward
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">Status</div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${status === 'completed' ? 'bg-green-500' : status === 'failed' ? 'bg-red-500' : 'bg-blue-500'}`} />
              <span className={`text-sm font-medium ${status === 'completed' ? 'text-green-600' : status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">Time</div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-400" />
              <span className="font-mono text-sm text-slate-900">
                {formatTime(0)}
              </span>
            </div>
            <div className="text-xs text-slate-500">
              Elapsed time
            </div>
          </div>
        </div>

        {status === 'completed' && (
          <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center gap-2 text-slate-700">
              <Zap className="h-4 w-4" />
              <span className="text-sm font-medium">Episode completed!</span>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              Check the summary panel for detailed results and grader breakdown.
            </p>
          </div>
        )}
      </div>
    </Panel>
  )
}
