export type Difficulty = 'easy' | 'medium' | 'hard' | 'original'

export interface TaskCard {
  id: string
  name: string
  description: string
  difficulty: Difficulty
  estimatedSteps: number
}

export const tasks: TaskCard[] = [
  {
    id: 'inbox_triage_001',
    name: 'Inbox Triage',
    description: 'Classify urgent emails and summarize key threads.',
    difficulty: 'easy',
    estimatedSteps: 10,
  },
  {
    id: 'meeting_coord_001',
    name: 'Meeting Coordination',
    description: 'Schedule a cross-functional review using mail, calendar, drive, and slack.',
    difficulty: 'medium',
    estimatedSteps: 15,
  },
  {
    id: 'project_rescue_001',
    name: 'Project Rescue',
    description: 'Stabilize a critical migration with Jira, calendar, mail, and slack.',
    difficulty: 'hard',
    estimatedSteps: 25,
  },
  {
    id: 'email_draft_001',
    name: 'Email Draft',
    description: 'Draft a polished response to a client incident email.',
    difficulty: 'original',
    estimatedSteps: 8,
  },
  {
    id: 'bug_triage_001',
    name: 'Bug Triage',
    description: 'Triage Jira tickets and assign priorities for fix planning.',
    difficulty: 'original',
    estimatedSteps: 12,
  },
  {
    id: 'meeting_schedule_001',
    name: 'Meeting Schedule',
    description: 'Schedule a global post-mortem meeting across time zones.',
    difficulty: 'original',
    estimatedSteps: 12,
  },
]
