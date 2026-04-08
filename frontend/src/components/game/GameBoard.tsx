import { useState } from 'react'
import { RotateCcw, Loader2 } from 'lucide-react'
import { Button } from '../common/Button'
import { TaskSelection } from './TaskSelection'
import { StatePanel } from './StatePanel'
import { InboxPanel } from './InboxPanel'
import { ActionForm } from './ActionForm'
import { RewardBreakdown } from './RewardBreakdown'
import { EpisodeSummary } from './EpisodeSummary'
import { useBackendAPI } from '../../hooks/useBackendAPI'
import type { Task, State, Observation, Action, Reward, EpisodeResult } from '../../types/api'

type GamePhase = 'task-selection' | 'playing' | 'completed'

export function GameBoard() {
  const [phase, setPhase] = useState<GamePhase>('task-selection')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [currentState, setCurrentState] = useState<State | null>(null)
  const [currentObservation, setCurrentObservation] = useState<Observation | null>(null)
  const [currentReward, setCurrentReward] = useState<Reward | null>(null)
  const [episodeResult, setEpisodeResult] = useState<EpisodeResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const { callReset, callState, callStep } = useBackendAPI()

  const handleTaskSelect = async (task: Task) => {
    setIsLoading(true)
    try {
      setSelectedTask(task)
      const resetResponse = await callReset(task.id)
      if (resetResponse) {
        const stateResponse = await callState()
        if (stateResponse) {
          setCurrentState({
            episode_id: stateResponse.episode_id,
            task_id: stateResponse.task_id,
            steps: stateResponse.step_count,
            score: stateResponse.cumulative_reward,
            status: 'active',
            time_elapsed: 0
          })
          setCurrentObservation(stateResponse.observation)
          setCurrentReward(stateResponse.reward || null)
          setPhase('playing')
        }
      }
    } catch (error) {
      console.error('Failed to start episode:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleActionSubmit = async (action: Action) => {
    setIsLoading(true)
    try {
      const stepResponse = await callStep(action)
      if (stepResponse) {
        // After a step, we need to get the updated state
        const stateResponse = await callState()
        if (stateResponse) {
          setCurrentState({
            episode_id: stateResponse.episode_id,
            task_id: stateResponse.task_id,
            steps: stateResponse.step_count,
            score: stateResponse.cumulative_reward,
            status: stateResponse.done ? 'completed' : 'active',
            time_elapsed: 0 // Mock for now
          })
          setCurrentObservation(stepResponse.observation)
          setCurrentReward(stateResponse.reward || {
            task_completion: stepResponse.reward,
            explanation: 'Step completed'
          })

          // Check if episode is completed
          if (stateResponse.done) {
            // Create mock episode result
            const mockResult: EpisodeResult = {
              episode_id: stateResponse.episode_id,
              total_score: stateResponse.cumulative_reward,
              max_possible_score: 100,
              steps_taken: stateResponse.step_count,
              total_time: 300,
              task_results: [{
                task_name: selectedTask?.name || 'Unknown Task',
                completed: true,
                score: stateResponse.cumulative_reward,
                time_taken: 300
              }],
              performance_breakdown: {
                efficiency: 85,
                correctness: 90,
                creativity: 75,
                communication: 80
              },
              feedback: 'Great job completing the task!',
              achievements: [{
                name: 'Task Master',
                description: 'Successfully completed a workplace task'
              }]
            }
            setEpisodeResult(mockResult)
            setPhase('completed')
          }
        }
      }
    } catch (error) {
      console.error('Failed to submit action:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewEpisode = () => {
    setPhase('task-selection')
    setSelectedTask(null)
    setCurrentState(null)
    setCurrentObservation(null)
    setCurrentReward(null)
    setEpisodeResult(null)
  }

  const handleReset = async () => {
    if (!selectedTask) return

    setIsLoading(true)
    try {
      const resetResponse = await callReset(selectedTask.id)
      if (resetResponse) {
        const stateResponse = await callState()
        if (stateResponse) {
          setCurrentState({
            episode_id: stateResponse.episode_id,
            task_id: stateResponse.task_id,
            steps: stateResponse.step_count,
            score: stateResponse.cumulative_reward,
            status: 'active',
            time_elapsed: 0
          })
          setCurrentObservation(stateResponse.observation)
          setCurrentReward(stateResponse.reward || null)
          setPhase('playing')
        }
      }
    } catch (error) {
      console.error('Failed to reset episode:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (phase === 'task-selection') {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">WorkSim Voyager</h1>
          <p className="text-slate-600">Choose a task to begin your workplace simulation</p>
        </div>
        <TaskSelection onTaskSelect={handleTaskSelect} disabled={isLoading} />
        {isLoading && (
          <div className="flex items-center justify-center mt-8">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-slate-600">Starting episode...</span>
          </div>
        )}
      </div>
    )
  }

  if (phase === 'completed' && episodeResult) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <EpisodeSummary
          result={episodeResult}
          onNewEpisode={handleNewEpisode}
        />
      </div>
    )
  }

  // Playing phase
  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">WorkSim Voyager</h1>
          <p className="text-slate-600">{selectedTask?.name}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleReset} disabled={isLoading}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button variant="secondary" onClick={handleNewEpisode}>
            New Episode
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - State and Rewards */}
        <div className="space-y-6">
          {currentState && (
            <StatePanel state={currentState} />
          )}
          {currentReward && (
            <RewardBreakdown
              reward={currentReward}
              totalScore={currentState?.score || 0}
            />
          )}
        </div>

        {/* Center Column - Inbox */}
        <div className="lg:col-span-2">
          {currentObservation && (
            <InboxPanel observation={currentObservation} />
          )}
        </div>
      </div>

      {/* Action Form - Full Width */}
      <div className="mt-6">
        <ActionForm
          onActionSubmitted={handleActionSubmit}
          disabled={isLoading || currentState?.status === 'completed'}
        />
      </div>

      {isLoading && (
        <div className="flex items-center justify-center mt-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          <span className="ml-2 text-slate-600">Processing action...</span>
        </div>
      )}
    </div>
  )
}
