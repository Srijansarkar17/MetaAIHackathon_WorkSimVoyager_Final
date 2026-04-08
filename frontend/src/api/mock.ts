import type { Observation, SchemaResponse, StateResponse } from '../types/api'

export const mockObservation: Observation = {
  inbox: [
    {
      id: 'it-e01',
      from: 'alice.chen@acme.com',
      subject: 'Urgent: Payment outage detected',
      body: 'The payment gateway is still failing for 20% of requests. Please prioritize.',
      timestamp: '2026-04-08T09:10:00Z',
      thread_id: 'thread-payment-502',
    },
    {
      id: 'it-e02',
      from: 'hr@acme.com',
      subject: 'Benefits enrollment reminder',
      body: 'Please complete your enrollment by Friday.',
      timestamp: '2026-04-08T08:00:00Z',
    },
  ],
  slack: [
    {
      id: 'sl-m01',
      channel: '#engineering',
      user: 'bob.kumar',
      text: 'We should sync on the Phoenix migration today.',
      timestamp: '2026-04-08T09:12:00Z',
    },
  ],
  drive: [
    {
      id: 'doc-001',
      title: 'Platform v2 design spec',
      content: 'Design overview for cross-functional review.',
      type: 'document',
      last_modified: '2026-04-07T18:20:00Z',
    },
  ],
  calendar: [
    {
      id: 'evt-001',
      title: 'Blocked by engineering review',
      start: '2026-04-08T14:00:00Z',
      end: '2026-04-08T15:00:00Z',
      attendees: ['alice.chen@acme.com', 'grace.li@acme.com'],
      location: 'Video call',
      description: 'Existing conflict for the design review meeting.',
    },
  ],
  jira: [
    {
      id: 'PHOENIX-102',
      title: 'ETL rewrite failure',
      severity: 'major',
      priority: 'critical',
      assignee: 'bob.kumar@acme.com',
      status: 'In Progress',
      description: 'ETL rewrite is blocked by missing validation.',
    },
  ],
}

export const mockState: StateResponse = {
  episode_id: 'ep-mock-001',
  task_id: 'inbox_triage_001',
  step_count: 0,
  done: false,
  cumulative_reward: 0,
  observation: mockObservation,
  grader_breakdown: {},
}

export const mockSchema: SchemaResponse = {
  action: {
    'mail/classify_email': {
      description: 'Classify an email as urgent or non-urgent',
      required: ['email_id', 'category'],
    },
  },
  observation: {},
  state: {},
}
