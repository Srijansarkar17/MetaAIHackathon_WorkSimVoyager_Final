# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""Pydantic models for WorkSim Voyager — full workplace simulation."""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

# ── Enums ─────────────────────────────────────────────────────────────
class TaskType(str, Enum):
    EMAIL_DRAFT = "email_draft"
    BUG_TRIAGE = "bug_triage"
    MEETING_SCHEDULE = "meeting_schedule"
    # Phase 3 — new difficulty-tiered tasks
    INBOX_TRIAGE = "inbox_triage"
    MEETING_COORDINATION = "meeting_coordination"
    PROJECT_RESCUE = "project_rescue"

class Priority(str, Enum):
    CRITICAL = "critical"; HIGH = "high"; MEDIUM = "medium"; LOW = "low"

class BugSeverity(str, Enum):
    BLOCKER = "blocker"; MAJOR = "major"; MINOR = "minor"; TRIVIAL = "trivial"

class TicketStatus(str, Enum):
    OPEN = "open"; IN_PROGRESS = "in_progress"; TRIAGED = "triaged"
    RESOLVED = "resolved"; CLOSED = "closed"

# ── Workspace Entities ────────────────────────────────────────────────
class Email(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str; sender: str; recipients: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list); subject: str; body: str
    timestamp: str; thread_id: Optional[str] = None; is_draft: bool = False

class SlackMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str; channel: str; sender: str; text: str; timestamp: str
    thread_ts: Optional[str] = None

class SlackChannel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str; name: str; topic: str = ""; members: List[str] = Field(default_factory=list)

class DriveFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str; name: str; content: str = ""; owner: str; mime_type: str = "text/plain"
    created_at: str; modified_at: str; shared_with: List[str] = Field(default_factory=list)

class JiraTicket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str; title: str; description: str; reporter: str
    assigned_to: Optional[str] = None; severity: Optional[BugSeverity] = None
    priority: Optional[Priority] = None; labels: List[str] = Field(default_factory=list)
    status: str = "open"; created_at: str; component: Optional[str] = None
    steps_to_reproduce: Optional[str] = None; expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    comments: List[Dict[str, Any]] = Field(default_factory=list)

class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str; title: str; start_time: str; end_time: str
    attendees: List[str] = Field(default_factory=list)
    location: Optional[str] = None; description: Optional[str] = None
    organizer: str; is_recurring: bool = False

class TeamMember(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str; name: str; role: str; department: str
    timezone: str = "America/New_York"
    available_hours: str = "09:00-17:00"

# ── WorkSim Action / Observation (Phase-1 spec) ──────────────────────
class WorkSimAction(BaseModel):
    """Agent action: pick a tool, a command, and supply input."""
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(description="Tool name: mail | slack | drive | calendar | jira")
    command: str = Field(description="Command within the tool")
    input: Dict[str, Any] = Field(default_factory=dict, description="Command arguments")

class WorkSimObservation(BaseModel):
    """Rich observation returned after every step."""
    model_config = ConfigDict(extra="allow")
    emails: List[Dict[str, Any]] = Field(default_factory=list)
    slack_messages: List[Dict[str, Any]] = Field(default_factory=list)
    calendar: List[Dict[str, Any]] = Field(default_factory=list)
    drive_files: List[Dict[str, Any]] = Field(default_factory=list)
    jira_tickets: List[Dict[str, Any]] = Field(default_factory=list)
    step_count: int = 0

class WorkSimReward(BaseModel):
    value: float = 0.0

# ── Workspace State (internal simulation) ─────────────────────────────
class WorkspaceState(BaseModel):
    model_config = ConfigDict(extra="allow")
    emails: List[Email] = Field(default_factory=list)
    slack_channels: List[SlackChannel] = Field(default_factory=list)
    slack_messages: List[SlackMessage] = Field(default_factory=list)
    drive_files: List[DriveFile] = Field(default_factory=list)
    jira_tickets: List[JiraTicket] = Field(default_factory=list)
    calendar_events: List[CalendarEvent] = Field(default_factory=list)
    team_members: List[TeamMember] = Field(default_factory=list)
    # Agent-generated artefacts
    drafts: List[Email] = Field(default_factory=list)
    sent_emails: List[Email] = Field(default_factory=list)
    sent_slack: List[SlackMessage] = Field(default_factory=list)
    created_files: List[DriveFile] = Field(default_factory=list)
    triage_actions: List[Dict[str, Any]] = Field(default_factory=list)
    scheduled_meetings: List[CalendarEvent] = Field(default_factory=list)
    jira_comments: List[Dict[str, Any]] = Field(default_factory=list)

# ── Task Specification ────────────────────────────────────────────────
class TaskSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    task_type: TaskType; task_id: str; description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict)
    max_steps: int = Field(default=20, ge=1)
