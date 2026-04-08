import { Trophy, Target, Clock, CheckCircle, XCircle, AlertTriangle, MessageSquare } from 'lucide-react'
import { Panel } from '../common/Panel'
import type { Reward } from '../../types/api'

interface RewardBreakdownProps {
  reward: Reward
  totalScore: number
}

export function RewardBreakdown({ reward, totalScore }: RewardBreakdownProps) {
  const getScoreColor = (score: number) => {
    if (score > 0) return 'text-green-600'
    if (score < 0) return 'text-red-600'
    return 'text-slate-600'
  }

  const getScoreIcon = (score: number) => {
    if (score > 0) return <CheckCircle className="h-4 w-4 text-green-600" />
    if (score < 0) return <XCircle className="h-4 w-4 text-red-600" />
    return <AlertTriangle className="h-4 w-4 text-yellow-600" />
  }

  const formatScore = (score: number) => {
    return score > 0 ? `+${score}` : score.toString()
  }

  return (
    <Panel title="Reward Breakdown">
      <div className="space-y-4">
        {/* Total Score */}
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-600" />
            <span className="font-medium text-slate-900">Total Score</span>
          </div>
          <span className={`text-2xl font-bold ${getScoreColor(totalScore)}`}>
            {totalScore}
          </span>
        </div>

        {/* Reward Components */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-slate-700 flex items-center gap-2">
            <Target className="h-4 w-4" />
            Score Components
          </h4>

          {reward.task_completion !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                {getScoreIcon(reward.task_completion)}
                <span className="text-sm text-slate-700">Task Completion</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.task_completion)}`}>
                {formatScore(reward.task_completion)}
              </span>
            </div>
          )}

          {reward.efficiency !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-blue-600" />
                <span className="text-sm text-slate-700">Efficiency</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.efficiency)}`}>
                {formatScore(reward.efficiency)}
              </span>
            </div>
          )}

          {reward.correctness !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm text-slate-700">Correctness</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.correctness)}`}>
                {formatScore(reward.correctness)}
              </span>
            </div>
          )}

          {reward.creativity !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Trophy className="h-4 w-4 text-purple-600" />
                <span className="text-sm text-slate-700">Creativity</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.creativity)}`}>
                {formatScore(reward.creativity)}
              </span>
            </div>
          )}

          {reward.communication !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-indigo-600" />
                <span className="text-sm text-slate-700">Communication</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.communication)}`}>
                {formatScore(reward.communication)}
              </span>
            </div>
          )}

          {reward.time_penalty !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-600" />
                <span className="text-sm text-slate-700">Time Penalty</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.time_penalty)}`}>
                {formatScore(reward.time_penalty)}
              </span>
            </div>
          )}

          {reward.error_penalty !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm text-slate-700">Error Penalty</span>
              </div>
              <span className={`text-sm font-medium ${getScoreColor(reward.error_penalty)}`}>
                {formatScore(reward.error_penalty)}
              </span>
            </div>
          )}
        </div>

        {/* Reward Explanation */}
        {reward.explanation && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Explanation</h4>
            <p className="text-sm text-blue-800">{reward.explanation}</p>
          </div>
        )}

        {/* Score History */}
        {reward.score_history && reward.score_history.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-slate-700 mb-2">Score History</h4>
            <div className="space-y-1">
            {reward.score_history?.slice(-5).map((entry: { step: number; score: number }, index: number) => (
                <div key={index} className="flex items-center justify-between text-xs text-slate-600 py-1">
                  <span>Step {entry.step}</span>
                  <span className={getScoreColor(entry.score)}>
                    {formatScore(entry.score)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Panel>
  )
}
