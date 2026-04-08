export type ToolName = 'mail' | 'slack' | 'drive' | 'calendar' | 'jira'

export interface Action {
  action_type: string
  parameters: Record<string, any>
}

export interface Email {
  id: string
  from: string
  subject: string
  body: string
  timestamp: string
  thread_id?: string
}

export interface SlackMessage {
  id: string
  channel: string
  user: string
  text: string
  timestamp: string
}

export interface DriveFile {
  id: string
  title: string
  content: string
  type: string
  last_modified: string
}

export interface CalendarEvent {
  id: string
  title: string
  start: string
  end: string
  attendees: string[]
  location: string
  description: string
}

export interface JiraTicket {
  id: string
  title: string
  severity: string
  priority: string
  assignee: string
  status: string
  description: string
}

export interface Task {
  id: string
  name: string
  description: string
}

export interface Reward {
  task_completion?: number
  efficiency?: number
  correctness?: number
  creativity?: number
  communication?: number
  time_penalty?: number
  error_penalty?: number
  explanation?: string
  score_history?: Array<{ step: number; score: number }>
}

export interface Observation {
  inbox?: Email[]
  slack?: SlackMessage[]
  drive?: DriveFile[]
  calendar?: CalendarEvent[]
  jira?: JiraTicket[]
  [key: string]: unknown
}

export interface RewardBreakdown {
  grader_breakdown: Record<string, unknown>
  reward_breakdown: {
    grader_delta: number
    action_bonus: number
    penalty: number
    raw_reward: number
    capped_reward: number
    action_category: string
    is_duplicate: boolean
    was_capped: boolean
  }
}

export interface StepResponse {
  observation: Observation
  reward: number
  done: boolean
  info: RewardBreakdown
}

export interface ResetResponse extends StepResponse {}

export interface State {
  episode_id: string
  task_id: string
  steps: number
  score: number
  status: 'active' | 'completed' | 'failed'
  time_elapsed?: number
}

export interface StateResponse {
  episode_id: string
  task_id: string
  step_count: number
  done: boolean
  cumulative_reward: number
  observation: Observation
  grader_breakdown: Record<string, unknown>
  reward?: Reward
}

export interface SchemaResponse {
  action: Record<string, unknown>
  observation: Record<string, unknown>
  state: Record<string, unknown>
}

export interface EpisodeResult {
  episode_id: string
  total_score: number
  max_possible_score?: number
  steps_taken: number
  total_time: number
  task_results: Array<{
    task_name: string
    completed: boolean
    score: number
    time_taken: number
  }>
  performance_breakdown?: Record<string, number>
  feedback?: string
  achievements?: Array<{
    name: string
    description: string
  }>
}

export interface HealthResponse {
  status: 'healthy'
}
