# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
Task registry — 6 deterministic tasks with full seed data for all 5 tools.

Phase 1 tasks (original):
  1. email_draft_001      — Email Draft
  2. bug_triage_001       — Bug / Jira Triage
  3. meeting_schedule_001  — Meeting Scheduling

Phase 3 tasks (difficulty-tiered, with noise):
  4. inbox_triage_001      — Inbox Triage (Easy,   ~10 steps)
  5. meeting_coord_001     — Meeting Coordination (Medium, ~15 steps)
  6. project_rescue_001    — Project Rescue (Hard,  15–30 steps)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from server.models import (
    CalendarEvent, DriveFile, Email, JiraTicket, Priority, BugSeverity,
    SlackChannel, SlackMessage, TaskSpec, TaskType, TeamMember,
)

@dataclass
class TaskDefinition:
    spec: TaskSpec
    emails: List[Email] = field(default_factory=list)
    slack_channels: List[SlackChannel] = field(default_factory=list)
    slack_messages: List[SlackMessage] = field(default_factory=list)
    drive_files: List[DriveFile] = field(default_factory=list)
    jira_tickets: List[JiraTicket] = field(default_factory=list)
    calendar_events: List[CalendarEvent] = field(default_factory=list)
    team_members: List[TeamMember] = field(default_factory=list)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SHARED DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_TEAM = [
    TeamMember(email="alice.chen@acme.com", name="Alice Chen",
               role="Engineering Manager", department="Engineering",
               timezone="America/New_York", available_hours="09:00-17:00"),
    TeamMember(email="bob.kumar@acme.com", name="Bob Kumar",
               role="Senior Backend Engineer", department="Engineering",
               timezone="America/Chicago", available_hours="08:00-16:00"),
    TeamMember(email="carol.martinez@acme.com", name="Carol Martinez",
               role="Product Manager", department="Product",
               timezone="America/Los_Angeles", available_hours="09:00-17:00"),
    TeamMember(email="david.wright@acme.com", name="David Wright",
               role="QA Lead", department="Quality Assurance",
               timezone="America/New_York", available_hours="09:00-17:00"),
    TeamMember(email="eve.johnson@acme.com", name="Eve Johnson",
               role="Frontend Engineer", department="Engineering",
               timezone="America/New_York", available_hours="10:00-18:00"),
    TeamMember(email="frank.liu@acme.com", name="Frank Liu",
               role="DevOps Engineer", department="Infrastructure",
               timezone="America/New_York", available_hours="08:00-16:00"),
    TeamMember(email="grace.park@acme.com", name="Grace Park",
               role="Data Engineer", department="Engineering",
               timezone="America/Chicago", available_hours="09:00-17:00"),
]

_CHANNELS = [
    SlackChannel(id="ch-eng", name="engineering", topic="Engineering discussion",
                 members=["alice.chen@acme.com", "bob.kumar@acme.com",
                          "eve.johnson@acme.com", "frank.liu@acme.com",
                          "grace.park@acme.com"]),
    SlackChannel(id="ch-general", name="general", topic="Company-wide",
                 members=[m.email for m in _TEAM]),
    SlackChannel(id="ch-incidents", name="incidents", topic="Production incidents",
                 members=["alice.chen@acme.com", "bob.kumar@acme.com",
                          "david.wright@acme.com", "frank.liu@acme.com"]),
    SlackChannel(id="ch-product", name="product", topic="Product updates",
                 members=["carol.martinez@acme.com", "alice.chen@acme.com",
                          "eve.johnson@acme.com"]),
    SlackChannel(id="ch-random", name="random", topic="Water cooler",
                 members=[m.email for m in _TEAM]),
]


# ═══════════════════════════════════════════════════════════════════════
#  Phase 1 — Task 1: Email Draft (kept for backward compat)
# ═══════════════════════════════════════════════════════════════════════
_EMAIL_TASK = TaskDefinition(
    spec=TaskSpec(
        task_type=TaskType.EMAIL_DRAFT, task_id="email_draft_001",
        description=(
            "A client (Globex Corp) reported that their monthly analytics export "
            "has been showing zero values since March 15. Draft a professional "
            "reply email acknowledging the issue, providing a preliminary root-cause "
            "hypothesis, and proposing a remediation timeline. CC the engineering "
            "manager (Alice Chen)."),
        context={"client_name": "Globex Corp", "client_contact": "pat.riley@globex.com",
                 "your_email": "agent@acme.com"},
        expected_outcomes={
            "to": ["pat.riley@globex.com"], "cc": ["alice.chen@acme.com"],
            "subject_must_contain": ["analytics", "export"],
            "body_must_contain": ["March 15", "zero", "apolog", "pipeline", "remediation"],
            "body_forbidden": ["TODO", "PLACEHOLDER", "[INSERT"],
            "min_body_length": 120, "max_body_length": 2000},
        max_steps=20),
    emails=[
        Email(id="email-001", sender="pat.riley@globex.com",
              recipients=["support@acme.com"],
              subject="Urgent: Analytics export broken",
              body="Hi team,\n\nOur monthly analytics export has been returning all zeros since "
                   "March 15. This is impacting our board reporting. Please investigate ASAP."
                   "\n\nBest,\nPat Riley\nGlobex Corp",
              timestamp="2026-03-28T14:23:00Z", thread_id="thread-globex-analytics"),
    ],
    slack_channels=_CHANNELS,
    slack_messages=[
        SlackMessage(id="sl-001", channel="engineering", sender="bob.kumar",
                     text="Heads up — the data pipeline migration on March 14 might have broken partition filters.",
                     timestamp="2026-03-28T15:00:00Z"),
        SlackMessage(id="sl-002", channel="incidents", sender="david.wright",
                     text="Seeing zero-value reports from Globex. Likely related to the warehouse migration.",
                     timestamp="2026-03-28T15:30:00Z"),
    ],
    drive_files=[
        DriveFile(id="doc-001", name="Pipeline Migration Runbook",
                  content="Migration steps:\n1. Switch warehouse endpoint\n2. Update partition filters\n"
                          "3. Validate output — NOTE: step 3 was skipped due to time pressure.",
                  owner="bob.kumar@acme.com", created_at="2026-03-14T09:00:00Z",
                  modified_at="2026-03-14T18:00:00Z"),
    ],
    team_members=_TEAM,
)

# ═══════════════════════════════════════════════════════════════════════
#  Phase 1 — Task 2: Bug / Jira Triage (kept for backward compat)
# ═══════════════════════════════════════════════════════════════════════
_BUG_TASK = TaskDefinition(
    spec=TaskSpec(
        task_type=TaskType.BUG_TRIAGE, task_id="bug_triage_001",
        description=(
            "Three new Jira tickets have been filed. Triage each one by assigning the "
            "correct severity, priority, component label, and assignee based on "
            "the ticket details and team expertise."),
        context={"team_roster": {
            "bob.kumar@acme.com": ["backend", "payments", "data-pipeline"],
            "eve.johnson@acme.com": ["frontend", "ui", "settings"],
            "david.wright@acme.com": ["qa", "testing", "data-pipeline"]}},
        expected_outcomes={
            "BUG-101": {"severity": "blocker", "priority": "critical",
                        "assigned_to": "bob.kumar@acme.com", "component": "payments",
                        "labels": ["production", "crash"]},
            "BUG-102": {"severity": "trivial", "priority": "low",
                        "assigned_to": "eve.johnson@acme.com", "component": "frontend",
                        "labels": ["ui", "alignment"]},
            "BUG-103": {"severity": "major", "priority": "high",
                        "assigned_to": "bob.kumar@acme.com", "component": "data-pipeline",
                        "labels": ["data-loss", "export"]}},
        max_steps=25),
    jira_tickets=[
        JiraTicket(id="BUG-101", title="Payment service crash on checkout",
                   description="Production payment service crashes with OOM error during peak checkout.",
                   reporter="david.wright@acme.com", created_at="2026-03-30T10:00:00Z",
                   steps_to_reproduce="1. Add items\n2. Checkout\n3. Click Pay Now",
                   expected_behavior="Payment succeeds", actual_behavior="500 OOM-killed"),
        JiraTicket(id="BUG-102", title="Settings page button misalignment",
                   description="Save button offset ~4px on Chrome 124+. Non-functional.",
                   reporter="carol.martinez@acme.com", created_at="2026-03-30T11:30:00Z"),
        JiraTicket(id="BUG-103", title="Export pipeline drops rows silently",
                   description="Nightly CSV export drops rows with NULL region. ~2% records affected.",
                   reporter="alice.chen@acme.com", created_at="2026-03-30T12:15:00Z"),
    ],
    slack_channels=_CHANNELS,
    slack_messages=[
        SlackMessage(id="sl-b1", channel="incidents", sender="david.wright",
                     text="CRITICAL: Payment service OOM in prod. Users can't checkout.",
                     timestamp="2026-03-30T10:05:00Z"),
        SlackMessage(id="sl-b2", channel="engineering", sender="alice.chen",
                     text="Export pipeline data-loss issue found. Bob, can you take a look?",
                     timestamp="2026-03-30T12:20:00Z"),
    ],
    team_members=_TEAM,
)

# ═══════════════════════════════════════════════════════════════════════
#  Phase 1 — Task 3: Meeting Scheduling (kept for backward compat)
# ═══════════════════════════════════════════════════════════════════════
_MEETING_TASK = TaskDefinition(
    spec=TaskSpec(
        task_type=TaskType.MEETING_SCHEDULE, task_id="meeting_schedule_001",
        description=(
            "Schedule a 60-minute post-mortem meeting for the payment outage (BUG-101). "
            "Required attendees: Alice Chen, Bob Kumar, Carol Martinez. "
            "Must be within March 31 – April 2, 2026, respect availability, "
            "include a descriptive title, agenda in description, and a video-call link."),
        context={"required_attendees": ["alice.chen@acme.com", "bob.kumar@acme.com",
                                         "carol.martinez@acme.com"],
                 "duration_minutes": 60, "date_range": {"start": "2026-03-31", "end": "2026-04-02"},
                 "organizer": "agent@acme.com"},
        expected_outcomes={
            "required_attendees": ["alice.chen@acme.com", "bob.kumar@acme.com", "carol.martinez@acme.com"],
            "duration_minutes": 60, "title_must_contain": ["post-mortem"],
            "description_must_contain": ["agenda"], "must_have_location": True,
            "valid_date_range_start": "2026-03-31", "valid_date_range_end": "2026-04-02",
            "must_respect_availability": True},
        max_steps=20),
    emails=[
        Email(id="email-002", sender="alice.chen@acme.com", recipients=["team@acme.com"],
              subject="Action Required: Schedule post-mortem for payment outage",
              body="We need a 60-min post-mortem with Bob and Carol in the next 3 business days.",
              timestamp="2026-03-30T16:00:00Z", thread_id="thread-postmortem"),
    ],
    slack_channels=_CHANNELS,
    slack_messages=[
        SlackMessage(id="sl-m1", channel="incidents", sender="alice.chen",
                     text="Please schedule the post-mortem this week. Coordinate availability.",
                     timestamp="2026-03-30T16:05:00Z"),
    ],
    calendar_events=[
        CalendarEvent(id="cal-001", title="Alice - Sprint Planning",
                      start_time="2026-03-31T10:00:00-04:00", end_time="2026-03-31T11:00:00-04:00",
                      attendees=["alice.chen@acme.com"], organizer="alice.chen@acme.com"),
        CalendarEvent(id="cal-002", title="Bob - Code Review",
                      start_time="2026-03-31T09:00:00-05:00", end_time="2026-03-31T10:00:00-05:00",
                      attendees=["bob.kumar@acme.com"], organizer="bob.kumar@acme.com"),
        CalendarEvent(id="cal-003", title="Carol - Product Sync",
                      start_time="2026-04-01T14:00:00-07:00", end_time="2026-04-01T15:00:00-07:00",
                      attendees=["carol.martinez@acme.com"], organizer="carol.martinez@acme.com"),
    ],
    team_members=_TEAM,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 3 — TASK 4: INBOX TRIAGE (Easy, ~10 steps)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Scenario: Monday morning. 8 emails in inbox (4 urgent, 4 non-urgent).
# Agent must classify each email via classify_email, then summarize the
# 2 active threads.  Includes 2 noise emails (newsletter, OOO auto-reply).
# ─────────────────────────────────────────────────────────────────────

_INBOX_TRIAGE_EMAILS = [
    # -- Urgent --
    Email(id="it-e01", sender="pat.riley@globex.com",
          recipients=["support@acme.com"],
          subject="URGENT: Payment gateway returning 502",
          body="Hi,\n\nOur payment integration is returning 502 errors since 6 AM. "
               "Customers cannot complete purchases. This is critical — we need immediate support.\n\n"
               "Pat Riley\nGlobex Corp",
          timestamp="2026-04-07T06:12:00Z", thread_id="thread-payment-502"),
    Email(id="it-e02", sender="david.wright@acme.com",
          recipients=["engineering@acme.com"],
          subject="Re: URGENT: Payment gateway returning 502",
          body="I can confirm — our monitoring shows 502s spiking at 05:58 UTC. "
               "Looks like the load balancer cert expired. Frank, can you check?\n\nDavid",
          timestamp="2026-04-07T06:25:00Z", thread_id="thread-payment-502"),
    Email(id="it-e03", sender="security@acme.com",
          recipients=["alice.chen@acme.com", "agent@acme.com"],
          subject="CRITICAL: Suspicious login attempts detected",
          body="Our SIEM flagged 847 brute-force login attempts against the admin panel "
               "from IP 203.0.113.42 between 02:00-04:00 UTC today. Immediate action required: "
               "block the IP and rotate affected credentials.\n\n— Acme Security Bot",
          timestamp="2026-04-07T04:15:00Z", thread_id="thread-security-alert"),
    Email(id="it-e04", sender="alice.chen@acme.com",
          recipients=["agent@acme.com"],
          subject="Database migration deadline MOVED UP to Wednesday",
          body="Hi,\n\nCritical update: the Postgres 16 migration deadline has been moved from "
               "Friday to Wednesday due to compliance requirements. We need to finalize the "
               "migration runbook and do a dry run by tomorrow EOD.\n\nAlice",
          timestamp="2026-04-07T07:00:00Z"),

    # -- Non-urgent --
    Email(id="it-e05", sender="hr@acme.com",
          recipients=["all@acme.com"],
          subject="Reminder: Q2 Benefits Enrollment Deadline April 15",
          body="Hi everyone,\n\nThis is a friendly reminder that Q2 benefits enrollment "
               "closes on April 15. Please review your selections in the HR portal.\n\n"
               "Best,\nHR Team",
          timestamp="2026-04-07T08:00:00Z"),
    Email(id="it-e06", sender="newsletter@techdigest.io",
          recipients=["agent@acme.com"],
          subject="TechDigest Weekly: Top 10 LLM Frameworks in 2026",
          body="This week's top stories:\n1. New LLM benchmark results\n"
               "2. Rust adoption in ML pipelines\n3. Cloud cost optimization tips\n\n"
               "Unsubscribe: https://techdigest.io/unsub",
          timestamp="2026-04-07T05:30:00Z"),
    Email(id="it-e07", sender="carol.martinez@acme.com",
          recipients=["agent@acme.com"],
          subject="Re: Q3 Roadmap Draft",
          body="Thanks for the feedback on the roadmap. I've incorporated your suggestions "
               "into v2. Could you glance at Section 3 (Platform Scalability) when you have "
               "a chance? No rush — next week is fine.\n\nCarol",
          timestamp="2026-04-06T18:45:00Z", thread_id="thread-roadmap"),
    Email(id="it-e08", sender="bob.kumar@acme.com",
          recipients=["agent@acme.com"],
          subject="OOO Auto-Reply: Bob Kumar",
          body="Hi,\n\nI'm currently out of office until April 8. For urgent backend "
               "issues, please contact Frank Liu (frank.liu@acme.com).\n\nBob",
          timestamp="2026-04-07T06:30:00Z"),
]

_INBOX_TRIAGE_TASK = TaskDefinition(
    spec=TaskSpec(
        task_type=TaskType.INBOX_TRIAGE,
        task_id="inbox_triage_001",
        description=(
            "It's Monday morning and your inbox has 8 new emails. You must:\n\n"
            "1. Read and classify EVERY email as urgent or non-urgent using classify_email.\n"
            "2. Summarize the 2 main threads (thread-payment-502, thread-security-alert) "
            "using summarize_thread.\n\n"
            "Urgent emails are those that:\n"
            "  - Report production outages or security incidents\n"
            "  - Have 'urgent', 'critical', or 'ASAP' in subject/body\n"
            "  - Involve deadline changes requiring immediate action\n\n"
            "Non-urgent emails are newsletters, OOO auto-replies, FYI messages, "
            "and requests with flexible deadlines.\n\n"
            "NOTE: Your inbox contains some noise (newsletters, auto-replies). "
            "Do not skip any email — classify all 8."
        ),
        context={
            "your_email": "agent@acme.com",
            "today": "2026-04-07",
            "email_count": 8,
            "target_threads": ["thread-payment-502", "thread-security-alert"],
        },
        expected_outcomes={
            # Expected classification for each email
            "classifications": {
                "it-e01": "urgent",       # Payment 502
                "it-e02": "urgent",       # Payment 502 follow-up
                "it-e03": "urgent",       # Security alert
                "it-e04": "urgent",       # Deadline moved up
                "it-e05": "non-urgent",   # HR reminder
                "it-e06": "non-urgent",   # Newsletter
                "it-e07": "non-urgent",   # Roadmap feedback (no rush)
                "it-e08": "non-urgent",   # OOO auto-reply
            },
            # Threads that must be summarized
            "threads_summarized": ["thread-payment-502", "thread-security-alert"],
            # Minimum number of classify_email calls
            "min_classifications": 8,
        },
        max_steps=15,
    ),
    emails=_INBOX_TRIAGE_EMAILS,
    slack_channels=_CHANNELS,
    # Noise: unrelated slack chatter
    slack_messages=[
        SlackMessage(id="it-s01", channel="random", sender="eve.johnson",
                     text="Anyone want to do a coffee run? ☕",
                     timestamp="2026-04-07T08:30:00Z"),
        SlackMessage(id="it-s02", channel="general", sender="carol.martinez",
                     text="Happy Monday everyone! Big week ahead.",
                     timestamp="2026-04-07T08:00:00Z"),
        SlackMessage(id="it-s03", channel="incidents", sender="frank.liu",
                     text="Investigating the 502s. Cert expiry confirmed. Working on renewal.",
                     timestamp="2026-04-07T06:40:00Z"),
    ],
    team_members=_TEAM,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 3 — TASK 5: MEETING COORDINATION (Medium, ~15 steps)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Scenario: A cross-functional design review needs scheduling.
# Agent must: read emails & slack for context, check calendar availability
# across 3 timezones, find valid meeting slots, create event with agenda,
# and notify participants.  Includes calendar conflicts and noise messages.
# ─────────────────────────────────────────────────────────────────────

_MEETING_COORD_TASK = TaskDefinition(
    spec=TaskSpec(
        task_type=TaskType.MEETING_COORDINATION,
        task_id="meeting_coord_001",
        description=(
            "Schedule a 90-minute cross-functional Design Review meeting.\n\n"
            "CONTEXT:\n"
            "- The Platform v2 redesign is entering final review phase\n"
            "- Required attendees: Alice Chen (Engineering Manager, ET), "
            "Bob Kumar (Sr. Backend, CT), Carol Martinez (Product Manager, PT)\n"
            "- Must happen within April 8–10, 2026\n"
            "- Must respect each attendee's working hours and existing calendar\n\n"
            "YOU MUST:\n"
            "1. Read the request email and relevant Slack messages for full context\n"
            "2. Review the design doc on Drive for agenda items\n"
            "3. Check calendar availability for all 3 required attendees on each candidate date\n"
            "4. Find a 90-minute slot when all 3 are free during overlapping work hours\n"
            "5. Create the calendar event with:\n"
            "   - Title containing 'design review'\n"
            "   - All 3 required attendees\n"
            "   - Agenda in description (referencing the Drive doc)\n"
            "   - Video call link in location\n"
            "6. Send a Slack message to #engineering announcing the meeting\n\n"
            "CONSTRAINTS:\n"
            "- Overlapping working hours (all 3 timezones): 12:00-16:00 ET = 11:00-15:00 CT = 09:00-13:00 PT\n"
            "- Some calendar slots are blocked (check availability first!)\n"
            "- Noise: there are unrelated Slack messages and emails — focus on the task"
        ),
        context={
            "required_attendees": ["alice.chen@acme.com", "bob.kumar@acme.com",
                                   "carol.martinez@acme.com"],
            "duration_minutes": 90,
            "date_range": {"start": "2026-04-08", "end": "2026-04-10"},
            "organizer": "agent@acme.com",
        },
        expected_outcomes={
            "required_attendees": ["alice.chen@acme.com", "bob.kumar@acme.com",
                                   "carol.martinez@acme.com"],
            "duration_minutes": 90,
            "title_must_contain": ["design review"],
            "description_must_contain": ["agenda", "platform"],
            "must_have_location": True,
            "valid_date_range_start": "2026-04-08",
            "valid_date_range_end": "2026-04-10",
            "must_have_slack_announcement": True,
            "slack_channel": "engineering",
            "slack_must_contain": ["design review"],
        },
        max_steps=20,
    ),
    emails=[
        Email(id="mc-e01", sender="carol.martinez@acme.com",
              recipients=["agent@acme.com", "alice.chen@acme.com"],
              subject="Please schedule: Platform v2 Design Review",
              body="Hi,\n\nWe need to schedule a 90-minute design review for Platform v2. "
                   "Required: Alice, Bob, and myself. Ideally April 8-10. "
                   "Please check calendars and find a slot that works for all of us.\n\n"
                   "The design doc is on Drive — please reference it in the agenda.\n\nCarol",
              timestamp="2026-04-07T15:00:00Z", thread_id="thread-design-review"),
        # Noise email
        Email(id="mc-e02", sender="newsletter@cloudwatch.dev",
              recipients=["agent@acme.com"],
              subject="CloudWatch Weekly: New Observability Features",
              body="This week in CloudWatch...\n\nNew metrics dashboard, improved alerting...",
              timestamp="2026-04-07T06:00:00Z"),
        # Noise email
        Email(id="mc-e03", sender="hr@acme.com",
              recipients=["all@acme.com"],
              subject="Office closure: April 14 (Holiday)",
              body="Please note the office will be closed on April 14 for the holiday.",
              timestamp="2026-04-07T09:00:00Z"),
    ],
    slack_channels=_CHANNELS,
    slack_messages=[
        SlackMessage(id="mc-s01", channel="product", sender="carol.martinez",
                     text="Design review for Platform v2 needs to happen this week. "
                          "Alice and Bob are must-haves. The design doc 'Platform v2 Design Spec' "
                          "has all the details we need to discuss.",
                     timestamp="2026-04-07T15:10:00Z"),
        SlackMessage(id="mc-s02", channel="engineering", sender="alice.chen",
                     text="Agree on the design review. Let's make sure we cover the API "
                          "migration plan and the new auth flow in the agenda.",
                     timestamp="2026-04-07T15:20:00Z"),
        # Noise
        SlackMessage(id="mc-s03", channel="random", sender="frank.liu",
                     text="New coffee machine in the 3rd floor kitchen 🎉",
                     timestamp="2026-04-07T14:00:00Z"),
        SlackMessage(id="mc-s04", channel="general", sender="david.wright",
                     text="Reminder: QA freeze starts April 11.",
                     timestamp="2026-04-07T10:00:00Z"),
        # Noise
        SlackMessage(id="mc-s05", channel="engineering", sender="bob.kumar",
                     text="Pushed a fix for the retry logic in the payment service. PR #4521.",
                     timestamp="2026-04-07T13:00:00Z"),
    ],
    drive_files=[
        DriveFile(id="mc-doc01", name="Platform v2 Design Spec",
                  content=(
                      "# Platform v2 Design Specification\n\n"
                      "## Overview\n"
                      "Complete redesign of the platform backend with new microservices architecture.\n\n"
                      "## Key Discussion Points\n"
                      "1. API Migration Plan (v1 → v2 endpoints)\n"
                      "2. New Authentication Flow (OAuth2 + PKCE)\n"
                      "3. Database Schema Changes (multi-tenancy support)\n"
                      "4. Performance Benchmarks (target: <100ms p99)\n"
                      "5. Rollout Strategy (canary → staged → GA)\n\n"
                      "## Timeline\n"
                      "- Design approval: April 10\n"
                      "- Implementation start: April 14\n"
                      "- Beta release: May 15\n"
                  ),
                  owner="carol.martinez@acme.com",
                  created_at="2026-04-05T10:00:00Z",
                  modified_at="2026-04-07T14:00:00Z",
                  shared_with=["alice.chen@acme.com", "bob.kumar@acme.com"]),
        # Noise doc
        DriveFile(id="mc-doc02", name="Q1 Retrospective Notes",
                  content="Q1 went well. Some action items for Q2...",
                  owner="alice.chen@acme.com",
                  created_at="2026-04-01T10:00:00Z",
                  modified_at="2026-04-01T10:00:00Z"),
    ],
    calendar_events=[
        # Alice: busy April 8 morning, April 9 afternoon
        CalendarEvent(id="mc-cal01", title="Alice - 1:1 with VP",
                      start_time="2026-04-08T13:00:00-04:00",
                      end_time="2026-04-08T14:00:00-04:00",
                      attendees=["alice.chen@acme.com"], organizer="alice.chen@acme.com"),
        CalendarEvent(id="mc-cal02", title="Alice - Team Standup",
                      start_time="2026-04-09T09:30:00-04:00",
                      end_time="2026-04-09T10:00:00-04:00",
                      attendees=["alice.chen@acme.com"], organizer="alice.chen@acme.com"),
        CalendarEvent(id="mc-cal03", title="Alice - Budget Review",
                      start_time="2026-04-09T14:00:00-04:00",
                      end_time="2026-04-09T15:30:00-04:00",
                      attendees=["alice.chen@acme.com"], organizer="alice.chen@acme.com"),
        # Bob: busy April 8 morning CT, April 10 midday CT
        CalendarEvent(id="mc-cal04", title="Bob - Sprint Review",
                      start_time="2026-04-08T09:00:00-05:00",
                      end_time="2026-04-08T10:30:00-05:00",
                      attendees=["bob.kumar@acme.com"], organizer="bob.kumar@acme.com"),
        CalendarEvent(id="mc-cal05", title="Bob - Architecture Sync",
                      start_time="2026-04-10T11:00:00-05:00",
                      end_time="2026-04-10T12:00:00-05:00",
                      attendees=["bob.kumar@acme.com"], organizer="bob.kumar@acme.com"),
        # Carol: busy April 9 morning PT
        CalendarEvent(id="mc-cal06", title="Carol - Stakeholder Demo",
                      start_time="2026-04-09T09:00:00-07:00",
                      end_time="2026-04-09T10:30:00-07:00",
                      attendees=["carol.martinez@acme.com"], organizer="carol.martinez@acme.com"),
        CalendarEvent(id="mc-cal07", title="Carol - Board Prep",
                      start_time="2026-04-10T09:00:00-07:00",
                      end_time="2026-04-10T10:00:00-07:00",
                      attendees=["carol.martinez@acme.com"], organizer="carol.martinez@acme.com"),
    ],
    team_members=_TEAM,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 3 — TASK 6: PROJECT RESCUE (Hard, 15–30 steps)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Scenario: "Project Phoenix" — a critical data platform migration — is
# failing.  The main Jira epic is stalled, Slack is chaotic with
# conflicting status updates, and the VP is asking for a status email.
#
# The agent must:
#   a) Read the epic and all 4 sub-tickets to understand current state
#   b) Parse through noisy Slack (12+ messages, half are noise)
#   c) Read 3 Drive docs (runbook, architecture, risk register)
#   d) Break the epic into proper subtasks (update tickets)
#   e) Assign owners to each subtask
#   f) Send a structured status email to the VP
#   g) Schedule a 30-min sync meeting within the next 2 days
#
# This requires 15–30 steps of multi-tool reasoning.
# ─────────────────────────────────────────────────────────────────────

_PROJECT_RESCUE_JIRA_TICKETS = [
    # Epic (parent)
    JiraTicket(
        id="PHOENIX-100", title="[EPIC] Project Phoenix: Data Platform Migration",
        description=(
            "Migrate legacy data platform to new Lakehouse architecture.\n\n"
            "STATUS: BLOCKED — multiple sub-tasks stalled.\n"
            "DEADLINE: April 15, 2026 (hard deadline from compliance).\n\n"
            "Sub-tasks:\n"
            "- PHOENIX-101: Schema migration\n"
            "- PHOENIX-102: ETL pipeline rewrite\n"
            "- PHOENIX-103: Data validation framework\n"
            "- PHOENIX-104: Rollback procedure\n"
        ),
        reporter="alice.chen@acme.com", created_at="2026-03-15T09:00:00Z",
        status="in_progress", labels=["epic", "migration", "compliance"],
        priority=Priority.CRITICAL,
    ),
    # Sub-task 1: Schema migration — IN PROGRESS, partially done
    JiraTicket(
        id="PHOENIX-101", title="Schema migration: legacy → lakehouse",
        description=(
            "Migrate 47 tables from PostgreSQL to Lakehouse format.\n"
            "Progress: 32/47 tables migrated. Blocked on 'payments_ledger' table "
            "due to schema conflicts (see Drive doc: Migration Runbook v3).\n"
            "Estimated effort remaining: 3 days."
        ),
        reporter="grace.park@acme.com", created_at="2026-03-20T10:00:00Z",
        assigned_to="grace.park@acme.com", status="in_progress",
        labels=["schema", "migration"], component="data-platform",
    ),
    # Sub-task 2: ETL rewrite — BLOCKED, no assignee
    JiraTicket(
        id="PHOENIX-102", title="ETL pipeline rewrite for lakehouse ingestion",
        description=(
            "Rewrite 12 ETL jobs from legacy Spark 2.4 to Spark 3.5 + Delta Lake.\n"
            "Status: 4/12 jobs rewritten. BLOCKED — waiting on schema migration "
            "(PHOENIX-101) to complete for the remaining jobs.\n"
            "NOTE: Original assignee (intern) left the company. Needs reassignment."
        ),
        reporter="alice.chen@acme.com", created_at="2026-03-22T11:00:00Z",
        status="open", labels=["etl", "migration", "blocked"],
    ),
    # Sub-task 3: Data validation — NOT STARTED
    JiraTicket(
        id="PHOENIX-103", title="Data validation framework for migration verification",
        description=(
            "Build automated validation to ensure data integrity post-migration.\n"
            "Requirements:\n"
            "- Row count verification across all 47 tables\n"
            "- Checksum validation for financial data\n"
            "- Referential integrity checks\n"
            "Status: NOT STARTED. Depends on PHOENIX-101 completion."
        ),
        reporter="david.wright@acme.com", created_at="2026-03-25T09:00:00Z",
        status="open", labels=["qa", "validation", "migration"],
    ),
    # Sub-task 4: Rollback — NOT STARTED, critical for compliance
    JiraTicket(
        id="PHOENIX-104", title="Rollback procedure and disaster recovery plan",
        description=(
            "Document and test rollback procedure in case migration fails.\n"
            "COMPLIANCE REQUIREMENT: Must have tested rollback before go-live.\n"
            "Status: NOT STARTED. This is a hard compliance requirement."
        ),
        reporter="alice.chen@acme.com", created_at="2026-03-25T10:00:00Z",
        status="open", labels=["rollback", "compliance", "migration"],
    ),
]

_PROJECT_RESCUE_SLACK = [
    # Relevant signal messages
    SlackMessage(id="pr-s01", channel="engineering", sender="alice.chen",
                 text="Team — Project Phoenix deadline is April 15 and we're behind. "
                      "Need status updates from everyone ASAP.",
                 timestamp="2026-04-07T09:00:00Z"),
    SlackMessage(id="pr-s02", channel="engineering", sender="grace.park",
                 text="Schema migration update: 32 of 47 tables done. The payments_ledger "
                      "table has schema conflicts — I documented the issue in the runbook. "
                      "Need Bob's help with the column type mismatches.",
                 timestamp="2026-04-07T09:15:00Z"),
    SlackMessage(id="pr-s03", channel="engineering", sender="frank.liu",
                 text="DevOps side: the new lakehouse infra is provisioned and tested. "
                      "Ready when you are. Rollback infra is also set up but the procedure "
                      "doc hasn't been written yet.",
                 timestamp="2026-04-07T09:30:00Z"),
    SlackMessage(id="pr-s04", channel="incidents", sender="david.wright",
                 text="Heads up: the ETL pipeline ticket PHOENIX-102 has no assignee since "
                      "the intern left. Someone needs to pick this up ASAP.",
                 timestamp="2026-04-07T09:45:00Z"),
    SlackMessage(id="pr-s05", channel="engineering", sender="bob.kumar",
                 text="I can look at the payments_ledger schema conflicts. Also happy to "
                      "take over the remaining ETL jobs — I'm familiar with Spark 3.5.",
                 timestamp="2026-04-07T10:00:00Z"),
    SlackMessage(id="pr-s06", channel="engineering", sender="alice.chen",
                 text="@bob.kumar great — please take PHOENIX-102. David, can you own "
                      "PHOENIX-103 (validation framework)? And Frank, please write the "
                      "rollback procedure (PHOENIX-104).",
                 timestamp="2026-04-07T10:15:00Z"),

    # Noise messages — agent must filter these out
    SlackMessage(id="pr-s07", channel="random", sender="eve.johnson",
                 text="Just saw the new Star Wars trailer. Thoughts? 🍿",
                 timestamp="2026-04-07T10:20:00Z"),
    SlackMessage(id="pr-s08", channel="general", sender="carol.martinez",
                 text="Reminder: all-hands is Thursday at 2 PM.",
                 timestamp="2026-04-07T11:00:00Z"),
    SlackMessage(id="pr-s09", channel="random", sender="frank.liu",
                 text="My CI pipeline passed on the first try. Is this a dream? 😂",
                 timestamp="2026-04-07T11:30:00Z"),
    SlackMessage(id="pr-s10", channel="engineering", sender="eve.johnson",
                 text="Unrelated: anyone else seeing flaky tests in the frontend CI? "
                      "Might need to update the test runner.",
                 timestamp="2026-04-07T12:00:00Z"),
    SlackMessage(id="pr-s11", channel="general", sender="grace.park",
                 text="Lunch plans? Thinking Thai food today.",
                 timestamp="2026-04-07T12:15:00Z"),

    # More signal
    SlackMessage(id="pr-s12", channel="engineering", sender="alice.chen",
                 text="VP wants a status email on Phoenix by EOD. Can someone compile "
                      "the current state and send it to vp@acme.com?",
                 timestamp="2026-04-07T14:00:00Z"),
]

_PROJECT_RESCUE_DRIVE = [
    DriveFile(
        id="pr-doc01", name="Phoenix Migration Runbook v3",
        content=(
            "# Project Phoenix — Migration Runbook v3\n\n"
            "## Current Status (as of April 7)\n"
            "- Schema migration: 32/47 tables complete\n"
            "- BLOCKER: payments_ledger table — column type mismatch\n"
            "  - Legacy: decimal(10,2) → Lakehouse: requires decimal(18,6)\n"
            "  - Impact: 15 dependent tables waiting on this\n"
            "- ETL rewrite: 4/12 jobs complete (needs new assignee)\n"
            "- Validation: not started\n"
            "- Rollback: infra ready, procedure not documented\n\n"
            "## Dependencies\n"
            "- PHOENIX-102 depends on PHOENIX-101\n"
            "- PHOENIX-103 depends on PHOENIX-101\n"
            "- PHOENIX-104 is independent (can be done in parallel)\n\n"
            "## Risks\n"
            "- Hard deadline: April 15 (compliance)\n"
            "- No rollback procedure = cannot go live\n"
            "- ETL has no owner since intern departure\n"
        ),
        owner="grace.park@acme.com",
        created_at="2026-04-05T10:00:00Z",
        modified_at="2026-04-07T09:00:00Z",
        shared_with=["alice.chen@acme.com", "bob.kumar@acme.com"],
    ),
    DriveFile(
        id="pr-doc02", name="Phoenix Architecture Diagram",
        content=(
            "# Architecture Overview\n\n"
            "Legacy Stack → Migration Layer → Lakehouse\n\n"
            "Components:\n"
            "1. PostgreSQL (source) — 47 tables, ~2TB\n"
            "2. Spark ETL Layer — 12 jobs, batch processing\n"
            "3. Delta Lake (target) — Lakehouse format\n"
            "4. Validation Service — row counts + checksums\n"
            "5. Rollback Switch — infrastructure-level point-in-time recovery\n"
        ),
        owner="frank.liu@acme.com",
        created_at="2026-03-20T10:00:00Z",
        modified_at="2026-04-01T16:00:00Z",
    ),
    DriveFile(
        id="pr-doc03", name="Phoenix Risk Register",
        content=(
            "# Risk Register — Project Phoenix\n\n"
            "| ID | Risk | Severity | Mitigation | Owner |\n"
            "|----|------|----------|------------|-------|\n"
            "| R1 | Schema conflicts block migration | High | Manual type mapping | Grace Park |\n"
            "| R2 | No ETL owner since intern left | Critical | Reassign to Bob Kumar | Alice Chen |\n"
            "| R3 | No rollback procedure | Critical | Write+test before go-live | TBD |\n"
            "| R4 | Compliance deadline April 15 | Critical | Parallel workstreams | Alice Chen |\n"
            "| R5 | Data validation not started | High | Start after schema done | David Wright |\n"
        ),
        owner="alice.chen@acme.com",
        created_at="2026-04-01T10:00:00Z",
        modified_at="2026-04-07T08:00:00Z",
    ),
    # Noise doc
    DriveFile(
        id="pr-doc04", name="Team Offsite Planning 2026",
        content="Ideas for the team offsite:\n1. Escape room\n2. Cooking class\n3. Hiking trip",
        owner="carol.martinez@acme.com",
        created_at="2026-04-03T10:00:00Z",
        modified_at="2026-04-03T10:00:00Z",
    ),
]

_PROJECT_RESCUE_EMAILS = [
    Email(id="pr-e01", sender="alice.chen@acme.com",
          recipients=["agent@acme.com"],
          subject="URGENT: Project Phoenix needs rescue — please help coordinate",
          body=(
              "Hi,\n\nProject Phoenix (data platform migration) is in trouble. "
              "The deadline is April 15 and we're significantly behind.\n\n"
              "I need you to:\n"
              "1. Review all Phoenix tickets (PHOENIX-100 through 104)\n"
              "2. Read the Slack discussions for latest updates\n"
              "3. Check the Drive docs (runbook, architecture, risk register)\n"
              "4. Update the Jira tickets with proper assignments:\n"
              "   - PHOENIX-102 → Bob Kumar (ETL rewrite)\n"
              "   - PHOENIX-103 → David Wright (validation)\n"
              "   - PHOENIX-104 → Frank Liu (rollback)\n"
              "5. Send a status update email to the VP (vp@acme.com) summarizing:\n"
              "   - Current state (what's done, what's blocked)\n"
              "   - Updated assignments\n"
              "   - Mitigation plan for the April 15 deadline\n"
              "6. Schedule a 30-minute Phoenix sync meeting for tomorrow or the day after "
              "(April 8-9) with Alice, Bob, Grace, David, and Frank\n\n"
              "Thanks,\nAlice"
          ),
          timestamp="2026-04-07T14:30:00Z", thread_id="thread-phoenix-rescue"),
    # Noise email
    Email(id="pr-e02", sender="facilities@acme.com",
          recipients=["all@acme.com"],
          subject="Elevator maintenance: April 10",
          body="Elevator B will be out of service on April 10 for scheduled maintenance.",
          timestamp="2026-04-07T08:00:00Z"),
    # Noise email
    Email(id="pr-e03", sender="learning@acme.com",
          recipients=["all@acme.com"],
          subject="New training available: Advanced Kubernetes",
          body="Sign up for our new K8s training course at learning.acme.com",
          timestamp="2026-04-07T07:00:00Z"),
]

_PROJECT_RESCUE_TASK = TaskDefinition(
    spec=TaskSpec(
        task_type=TaskType.PROJECT_RESCUE,
        task_id="project_rescue_001",
        description=(
            "Project Phoenix — a critical data platform migration — is failing and needs rescue.\n\n"
            "SITUATION:\n"
            "- Hard compliance deadline: April 15, 2026\n"
            "- Epic PHOENIX-100 has 4 sub-tasks, most are stalled or unassigned\n"
            "- Slack is full of conflicting updates and noise\n"
            "- The VP needs a status email by EOD\n\n"
            "YOU MUST (all steps required for full score):\n\n"
            "1. GATHER INFORMATION:\n"
            "   - Read all 5 Jira tickets (PHOENIX-100 through 104)\n"
            "   - Read relevant Slack channels for status updates\n"
            "   - Read Drive docs: Migration Runbook, Architecture Diagram, Risk Register\n\n"
            "2. UPDATE JIRA TICKETS (assign proper owners):\n"
            "   - PHOENIX-102 (ETL rewrite) → assigned_to: bob.kumar@acme.com, severity: major, priority: critical\n"
            "   - PHOENIX-103 (validation) → assigned_to: david.wright@acme.com, severity: major, priority: high\n"
            "   - PHOENIX-104 (rollback) → assigned_to: frank.liu@acme.com, severity: blocker, priority: critical\n\n"
            "3. SEND STATUS EMAIL to vp@acme.com:\n"
            "   - Subject must contain 'Phoenix' and 'status'\n"
            "   - Body must cover: current progress, blockers, assignments, April 15 deadline, mitigation plan\n"
            "   - CC alice.chen@acme.com\n\n"
            "4. SCHEDULE MEETING:\n"
            "   - 30-minute Phoenix sync within April 8-9, 2026\n"
            "   - Required attendees: alice.chen, bob.kumar, grace.park, david.wright, frank.liu\n"
            "   - Title must contain 'Phoenix'\n"
            "   - Include agenda in description\n"
            "   - Include video call link in location\n\n"
            "IMPORTANT: Filter out noise — there are irrelevant Slack messages, emails, and docs."
        ),
        context={
            "today": "2026-04-07",
            "deadline": "2026-04-15",
            "vp_email": "vp@acme.com",
            "organizer": "agent@acme.com",
        },
        expected_outcomes={
            # Jira updates (3 tickets need assignment)
            "jira_updates": {
                "PHOENIX-102": {
                    "assigned_to": "bob.kumar@acme.com",
                    "severity": "major",
                    "priority": "critical",
                },
                "PHOENIX-103": {
                    "assigned_to": "david.wright@acme.com",
                    "severity": "major",
                    "priority": "high",
                },
                "PHOENIX-104": {
                    "assigned_to": "frank.liu@acme.com",
                    "severity": "blocker",
                    "priority": "critical",
                },
            },
            # Status email
            "email_to": ["vp@acme.com"],
            "email_cc": ["alice.chen@acme.com"],
            "email_subject_must_contain": ["phoenix", "status"],
            "email_body_must_contain": [
                "april 15", "migration", "blocked", "rollback",
            ],
            "email_body_forbidden": ["TODO", "PLACEHOLDER", "[INSERT"],
            "email_min_length": 200,
            # Meeting
            "meeting_attendees": [
                "alice.chen@acme.com", "bob.kumar@acme.com",
                "grace.park@acme.com", "david.wright@acme.com",
                "frank.liu@acme.com",
            ],
            "meeting_duration_minutes": 30,
            "meeting_title_must_contain": ["phoenix"],
            "meeting_description_must_contain": ["agenda"],
            "meeting_must_have_location": True,
            "meeting_date_range_start": "2026-04-08",
            "meeting_date_range_end": "2026-04-09",
        },
        max_steps=30,
    ),
    emails=_PROJECT_RESCUE_EMAILS,
    slack_channels=_CHANNELS,
    slack_messages=_PROJECT_RESCUE_SLACK,
    drive_files=_PROJECT_RESCUE_DRIVE,
    jira_tickets=_PROJECT_RESCUE_JIRA_TICKETS,
    calendar_events=[
        # Alice: busy April 8 morning
        CalendarEvent(id="pr-cal01", title="Alice - Exec Standup",
                      start_time="2026-04-08T09:00:00-04:00",
                      end_time="2026-04-08T09:30:00-04:00",
                      attendees=["alice.chen@acme.com"], organizer="alice.chen@acme.com"),
        # Bob: busy April 8 late afternoon CT
        CalendarEvent(id="pr-cal02", title="Bob - Deploy Window",
                      start_time="2026-04-08T15:00:00-05:00",
                      end_time="2026-04-08T16:00:00-05:00",
                      attendees=["bob.kumar@acme.com"], organizer="bob.kumar@acme.com"),
        # Grace: busy April 9 morning CT
        CalendarEvent(id="pr-cal03", title="Grace - Sprint Planning",
                      start_time="2026-04-09T09:00:00-05:00",
                      end_time="2026-04-09T10:00:00-05:00",
                      attendees=["grace.park@acme.com"], organizer="grace.park@acme.com"),
        # David: mostly free
        CalendarEvent(id="pr-cal04", title="David - QA Standup",
                      start_time="2026-04-08T09:30:00-04:00",
                      end_time="2026-04-08T10:00:00-04:00",
                      attendees=["david.wright@acme.com"], organizer="david.wright@acme.com"),
        # Frank: busy April 9 afternoon
        CalendarEvent(id="pr-cal05", title="Frank - Infra Review",
                      start_time="2026-04-09T14:00:00-04:00",
                      end_time="2026-04-09T15:00:00-04:00",
                      attendees=["frank.liu@acme.com"], organizer="frank.liu@acme.com"),
    ],
    team_members=_TEAM,
)


# ── Public registry ──────────────────────────────────────────────────
TASK_REGISTRY: Dict[str, TaskDefinition] = {
    # Phase 1 (backward compat)
    "email_draft_001": _EMAIL_TASK,
    "bug_triage_001": _BUG_TASK,
    "meeting_schedule_001": _MEETING_TASK,
    # Phase 3 (difficulty-tiered)
    "inbox_triage_001": _INBOX_TRIAGE_TASK,
    "meeting_coord_001": _MEETING_COORD_TASK,
    "project_rescue_001": _PROJECT_RESCUE_TASK,
}
