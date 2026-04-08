import { Trophy, Target, Clock, Star, Award, TrendingUp } from 'lucide-react'
import { Button } from '../common/Button'
import { Panel } from '../common/Panel'
import type { EpisodeResult } from '../../types/api'

interface EpisodeSummaryProps {
  result: EpisodeResult
  onNewEpisode: () => void
  onViewDetails?: () => void
}

export function EpisodeSummary({ result, onNewEpisode, onViewDetails }: EpisodeSummaryProps) {
  const getPerformanceLevel = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100
    if (percentage >= 90) return { level: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-100' }
    if (percentage >= 75) return { level: 'Good', color: 'text-blue-600', bgColor: 'bg-blue-100' }
    if (percentage >= 60) return { level: 'Fair', color: 'text-yellow-600', bgColor: 'bg-yellow-100' }
    return { level: 'Needs Improvement', color: 'text-red-600', bgColor: 'bg-red-100' }
  }

  const performance = getPerformanceLevel(result.total_score, result.max_possible_score || 100)

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <Panel title="Episode Complete!">
      <div className="space-y-6">
        {/* Performance Badge */}
        <div className="text-center">
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${performance.bgColor} ${performance.color} mb-4`}>
            <Award className="h-4 w-4 mr-2" />
            {performance.level} Performance
          </div>
          <div className="text-4xl font-bold text-slate-900 mb-2">
            {result.total_score}
          </div>
          <div className="text-sm text-slate-600">
            out of {result.max_possible_score || 100} possible points
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-slate-50 rounded-lg">
            <Target className="h-6 w-6 text-blue-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">{result.steps_taken}</div>
            <div className="text-sm text-slate-600">Steps Taken</div>
          </div>
          <div className="text-center p-4 bg-slate-50 rounded-lg">
            <Clock className="h-6 w-6 text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">{formatTime(result.total_time)}</div>
            <div className="text-sm text-slate-600">Total Time</div>
          </div>
        </div>

        {/* Task Completion */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-slate-700 flex items-center gap-2">
            <Trophy className="h-4 w-4" />
            Task Completion
          </h4>
          <div className="space-y-2">
            {result.task_results?.map((taskResult, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${taskResult.completed ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-sm font-medium text-slate-900">{taskResult.task_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-600">{taskResult.score} pts</span>
                  {taskResult.completed && <Star className="h-4 w-4 text-yellow-500" />}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Performance Breakdown */}
        {result.performance_breakdown && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Performance Breakdown
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(result.performance_breakdown).map(([key, value]) => (
                <div key={key} className="text-center p-3 bg-slate-50 rounded-lg">
                  <div className="text-lg font-bold text-slate-900">{value}</div>
                  <div className="text-xs text-slate-600 capitalize">
                    {key.replace('_', ' ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feedback */}
        {result.feedback && (
          <div className="p-4 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Feedback</h4>
            <p className="text-sm text-blue-800">{result.feedback}</p>
          </div>
        )}

        {/* Achievements */}
        {result.achievements && result.achievements.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700 flex items-center gap-2">
              <Award className="h-4 w-4" />
              Achievements Unlocked
            </h4>
            <div className="space-y-2">
              {result.achievements.map((achievement, index) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                  <Trophy className="h-5 w-5 text-yellow-600" />
                  <div>
                    <div className="text-sm font-medium text-yellow-900">{achievement.name}</div>
                    <div className="text-xs text-yellow-700">{achievement.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4 border-t border-slate-200">
          <Button onClick={onNewEpisode} className="flex-1">
            Start New Episode
          </Button>
          {onViewDetails && (
            <Button variant="secondary" onClick={onViewDetails} className="flex-1">
              View Details
            </Button>
          )}
        </div>
      </div>
    </Panel>
  )
}
