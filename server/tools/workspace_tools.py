# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
Action-routed workspace tools for the five simulated services:
  mail · slack · drive · calendar · jira

Phase 2: Full tool simulation layer with:
  - 24+ commands across 5 tools
  - Input validation layer (type & required-field checks)
  - Incorrect-usage penalties via ActionValidationError
  - Edge-case handling (missing data, scheduling conflicts, invalid IDs)
  - Higher-level semantic commands (classify_email, summarize_thread, etc.)

Every handler receives the current WorkspaceState (mutated in-place)
and an arbitrary kwargs dict.  Returns a result dict.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4
from server.models import (
    BugSeverity, CalendarEvent, DriveFile, Email, JiraTicket,
    Priority, SlackMessage, TicketStatus, WorkspaceState,
)

_TS = lambda: datetime.utcnow().isoformat() + "Z"
_ID = lambda pfx: f"{pfx}-{uuid4().hex[:8]}"

# ═══════════════════════════════════════════════════════════════════════
#  ACTION VALIDATION LAYER
# ═══════════════════════════════════════════════════════════════════════

class ActionValidationError(Exception):
    """Raised when action input fails validation. Carries structured info."""
    def __init__(self, message: str, field: str = "", expected: str = ""):
        self.message = message
        self.field = field
        self.expected = expected
        super().__init__(message)


# Per-command schema:  {(tool, command): {field: {"type": ..., "required": bool}}}
_INPUT_SCHEMAS: Dict[Tuple[str, str], Dict[str, Dict[str, Any]]] = {
    # ── MAIL ──────────────────────────────────────────────────────────
    ("mail", "list_inbox"): {},
    ("mail", "read_email"): {
        "email_id": {"type": "string", "required": True},
    },
    ("mail", "compose_draft"): {
        "to":        {"type": "list", "required": True},
        "subject":   {"type": "string", "required": True},
        "body":      {"type": "string", "required": True},
        "cc":        {"type": "list", "required": False},
        "thread_id": {"type": "string", "required": False},
    },
    ("mail", "send_email"): {
        "to":        {"type": "list", "required": False},   # optional if draft_id
        "subject":   {"type": "string", "required": False},
        "body":      {"type": "string", "required": False},
        "cc":        {"type": "list", "required": False},
        "draft_id":  {"type": "string", "required": False},
        "thread_id": {"type": "string", "required": False},
    },
    ("mail", "reply"): {
        "email_id": {"type": "string", "required": True},
        "body":     {"type": "string", "required": True},
        "cc":       {"type": "list", "required": False},
    },
    ("mail", "classify_email"): {
        "email_id": {"type": "string", "required": True},
    },
    ("mail", "summarize_thread"): {
        "thread_id": {"type": "string", "required": True},
    },
    ("mail", "send_reply"): {
        "email_id": {"type": "string", "required": True},
        "body":     {"type": "string", "required": True},
        "cc":       {"type": "list", "required": False},
    },
    # ── SLACK ─────────────────────────────────────────────────────────
    ("slack", "list_channels"): {},
    ("slack", "read_channel"): {
        "channel": {"type": "string", "required": True},
    },
    ("slack", "send_message"): {
        "channel":   {"type": "string", "required": True},
        "text":      {"type": "string", "required": True},
        "thread_ts": {"type": "string", "required": False},
    },
    ("slack", "list_dms"): {},
    ("slack", "send_dm"): {
        "user": {"type": "string", "required": True},
        "text": {"type": "string", "required": True},
    },
    # ── DRIVE ─────────────────────────────────────────────────────────
    ("drive", "list_files"): {},
    ("drive", "read_file"): {
        "file_id": {"type": "string", "required": True},
    },
    ("drive", "create_file"): {
        "name":        {"type": "string", "required": True},
        "content":     {"type": "string", "required": False},
        "shared_with": {"type": "list", "required": False},
    },
    ("drive", "edit_file"): {
        "file_id": {"type": "string", "required": True},
        "content":  {"type": "string", "required": True},
    },
    ("drive", "search_files"): {
        "query": {"type": "string", "required": True},
    },
    # ── CALENDAR ──────────────────────────────────────────────────────
    ("calendar", "list_events"): {},
    ("calendar", "check_availability"): {
        "attendee_emails": {"type": "list", "required": True},
        "date":            {"type": "string", "required": True},
    },
    ("calendar", "schedule_meeting"): {
        "title":       {"type": "string", "required": True},
        "start_time":  {"type": "string", "required": True},
        "end_time":    {"type": "string", "required": True},
        "attendees":   {"type": "list", "required": True},
        "description": {"type": "string", "required": False},
        "location":    {"type": "string", "required": False},
    },
    ("calendar", "create_event"): {
        "title":       {"type": "string", "required": True},
        "start_time":  {"type": "string", "required": True},
        "end_time":    {"type": "string", "required": True},
        "attendees":   {"type": "list", "required": False},
        "description": {"type": "string", "required": False},
        "location":    {"type": "string", "required": False},
    },
    ("calendar", "get_team_roster"): {},
    # ── JIRA ──────────────────────────────────────────────────────────
    ("jira", "list_tickets"): {},
    ("jira", "get_ticket"): {
        "ticket_id": {"type": "string", "required": True},
    },
    ("jira", "read_ticket"): {
        "ticket_id": {"type": "string", "required": True},
    },
    ("jira", "update_ticket"): {
        "ticket_id":   {"type": "string", "required": True},
        "severity":    {"type": "string", "required": False},
        "priority":    {"type": "string", "required": False},
        "assigned_to": {"type": "string", "required": False},
        "component":   {"type": "string", "required": False},
        "labels":      {"type": "list", "required": False},
        "status":      {"type": "string", "required": False},
    },
    ("jira", "create_ticket"): {
        "title":       {"type": "string", "required": True},
        "description": {"type": "string", "required": True},
        "severity":    {"type": "string", "required": False},
        "priority":    {"type": "string", "required": False},
        "assigned_to": {"type": "string", "required": False},
        "component":   {"type": "string", "required": False},
        "labels":      {"type": "list", "required": False},
    },
    ("jira", "add_comment"): {
        "ticket_id": {"type": "string", "required": True},
        "text":      {"type": "string", "required": True},
    },
    ("jira", "assign_task"): {
        "ticket_id":   {"type": "string", "required": True},
        "assigned_to": {"type": "string", "required": True},
    },
}


def validate_action_input(tool: str, command: str,
                          action_input: Dict[str, Any]) -> Dict[str, Any]:
    """Validate action input against the schema. Returns sanitised input or raises."""
    schema = _INPUT_SCHEMAS.get((tool, command))
    if schema is None:
        # Unknown command — caller will catch via ACTION_ROUTER lookup
        return action_input

    clean: Dict[str, Any] = {}
    for field, spec in schema.items():
        val = action_input.get(field)
        is_required = spec["required"]
        expected_type = spec["type"]

        # Missing required
        if val is None and is_required:
            raise ActionValidationError(
                f"Missing required field '{field}' for {tool}/{command}",
                field=field,
                expected=expected_type,
            )

        if val is None:
            continue

        # Type coercion / validation
        if expected_type == "string":
            if not isinstance(val, str):
                try:
                    val = str(val)
                except Exception:
                    raise ActionValidationError(
                        f"Field '{field}' must be a string, got {type(val).__name__}",
                        field=field, expected="string")
            if is_required and not val.strip():
                raise ActionValidationError(
                    f"Field '{field}' cannot be empty for {tool}/{command}",
                    field=field, expected="non-empty string")
        elif expected_type == "list":
            if isinstance(val, str):
                val = [val]  # auto-wrap single string into list
            if not isinstance(val, list):
                raise ActionValidationError(
                    f"Field '{field}' must be a list, got {type(val).__name__}",
                    field=field, expected="list")

        clean[field] = val

    # Pass through any extra kwargs that aren't in the schema (forward-compat)
    for k, v in action_input.items():
        if k not in clean:
            clean[k] = v

    return clean


# ═══════════════════════════════════════════════════════════════════════
#  MAIL — 8 commands
# ═══════════════════════════════════════════════════════════════════════
def mail_list_inbox(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """List all emails in inbox (excludes drafts and sent)."""
    return {"emails": [e.model_dump() for e in ws.emails]}


def mail_read_email(ws: WorkspaceState, *, email_id: str = "", **_: Any) -> Dict[str, Any]:
    """Read a specific email by ID. Searches inbox, drafts, and sent."""
    for pool in (ws.emails, ws.drafts, ws.sent_emails):
        for e in pool:
            if e.id == email_id:
                return e.model_dump()
    return {"error": f"Email '{email_id}' not found",
            "hint": "Use mail/list_inbox to see available email IDs."}


def mail_compose_draft(ws: WorkspaceState, *, to: List[str] = None,
                       subject: str = "", body: str = "",
                       cc: List[str] = None, thread_id: str = None, **_: Any) -> Dict[str, Any]:
    """Compose an email draft. Does not send."""
    draft = Email(id=_ID("draft"), sender="agent@acme.com", recipients=to or [],
                  cc=cc or [], subject=subject, body=body, timestamp=_TS(),
                  thread_id=thread_id, is_draft=True)
    ws.drafts.append(draft)
    return {"status": "drafted", "draft": draft.model_dump()}


def mail_send_email(ws: WorkspaceState, *, draft_id: str = "",
                    to: List[str] = None, subject: str = "", body: str = "",
                    cc: List[str] = None, thread_id: str = None, **_: Any) -> Dict[str, Any]:
    """Send an email. Either send a draft (via draft_id) or compose+send inline."""
    # Send existing draft
    if draft_id:
        for i, d in enumerate(ws.drafts):
            if d.id == draft_id:
                sent = d.model_copy(update={"is_draft": False, "timestamp": _TS()})
                ws.sent_emails.append(sent)
                ws.drafts.pop(i)
                return {"status": "sent", "email": sent.model_dump()}
        return {"error": f"Draft '{draft_id}' not found",
                "hint": "Use mail/compose_draft first, or pass 'to','subject','body' to send directly."}

    # Inline compose + send
    if not to and not subject and not body:
        return {"error": "Must provide either 'draft_id' or at least 'to' and 'body' to send an email.",
                "hint": "Example: {to: ['user@example.com'], subject: 'Hi', body: 'Hello'}"}

    email = Email(id=_ID("sent"), sender="agent@acme.com", recipients=to or [],
                  cc=cc or [], subject=subject, body=body, timestamp=_TS(),
                  thread_id=thread_id, is_draft=False)
    ws.sent_emails.append(email)
    return {"status": "sent", "email": email.model_dump()}


def mail_reply(ws: WorkspaceState, *, email_id: str = "", body: str = "",
               cc: List[str] = None, **_: Any) -> Dict[str, Any]:
    """Reply to an existing email. Auto-sets recipients, subject, thread_id."""
    orig = next((e for e in ws.emails if e.id == email_id), None)
    if not orig:
        return {"error": f"Email '{email_id}' not found in inbox",
                "hint": "Use mail/list_inbox to find valid email IDs."}
    reply = Email(id=_ID("sent"), sender="agent@acme.com",
                  recipients=[orig.sender], cc=cc if cc is not None else list(orig.cc),
                  subject=f"Re: {orig.subject}", body=body, timestamp=_TS(),
                  thread_id=orig.thread_id or orig.id, is_draft=False)
    ws.sent_emails.append(reply)
    return {"status": "sent", "email": reply.model_dump()}


def mail_classify_email(ws: WorkspaceState, *, email_id: str = "", **_: Any) -> Dict[str, Any]:
    """
    Classify an email deterministically based on content heuristics.
    Returns: category (urgent, bug_report, meeting_request, client_escalation, info, general),
             priority (critical, high, medium, low), and suggested_action.

    Also stores the classification on ws.email_classifications for grader tracking.
    """
    email = None
    for pool in (ws.emails, ws.drafts, ws.sent_emails):
        for e in pool:
            if e.id == email_id:
                email = e
                break
        if email:
            break
    if not email:
        return {"error": f"Email '{email_id}' not found",
                "hint": "Use mail/list_inbox to find valid email IDs."}

    text = (email.subject + " " + email.body).lower()

    # Deterministic classification rules (ordered by specificity)
    # 1. OOO auto-reply — always non-urgent, check before "urgent" keywords
    if "out of office" in text or "ooo" in text.split() or "auto-reply" in text:
        category, priority = "info", "low"
        suggested_action = "archive"
    # 2. Newsletter / FYI / HR reminders — check BEFORE urgent keywords
    #    (prevents "Benefits Enrollment Deadline" from triggering urgent)
    elif any(w in text for w in ["newsletter", "unsubscribe",
                                  "weekly", "digest",
                                  "enrollment", "benefits",
                                  "friendly reminder"]):
        category, priority = "info", "low"
        suggested_action = "archive"
    # 3. Urgent / critical / emergency
    elif any(w in text for w in ["urgent", "asap", "critical", "emergency",
                                  "crash", "suspicious", "brute-force",
                                  "immediate action", "502", "outage"]):
        category, priority = "urgent", "critical"
        suggested_action = "respond_immediately"
    # 4. Deadline MOVED UP (requires "moved up" or "moved forward" — not just "deadline")
    elif any(w in text for w in ["moved up", "moved forward", "accelerat"]):
        category, priority = "urgent", "critical"
        suggested_action = "respond_immediately"
    # 5. Bug / error reports
    elif any(w in text for w in ["bug", "error", "broken", "failed",
                                  "exception", "500"]):
        category, priority = "bug_report", "high"
        suggested_action = "create_jira_ticket"
    # 6. Client escalation
    elif any(w in text for w in ["escalat", "client", "customer", "complaint"]):
        category, priority = "client_escalation", "high"
        suggested_action = "escalate_to_manager"
    # 7. Meeting / schedule
    elif any(w in text for w in ["schedule", "meeting", "calendar", "invite"]):
        category, priority = "meeting_request", "medium"
        suggested_action = "check_calendar"
    # 8. FYI / info / reminders
    elif any(w in text for w in ["fyi", "info", "update", "reminder"]):
        category, priority = "info", "low"
        suggested_action = "archive"
    # 8. "No rush" / low-priority review requests
    elif any(w in text for w in ["no rush", "when you have a chance",
                                  "no hurry", "low priority"]):
        category, priority = "general", "low"
        suggested_action = "review"
    else:
        category, priority = "general", "medium"
        suggested_action = "review"

    result = {
        "email_id": email_id,
        "category": category,
        "priority": priority,
        "suggested_action": suggested_action,
        "subject": email.subject,
        "sender": email.sender,
    }

    # Track classification on workspace state (for inbox_triage grader)
    if not hasattr(ws, "email_classifications") or not isinstance(getattr(ws, "email_classifications", None), dict):
        ws.email_classifications = {}  # type: ignore[attr-defined]
    ws.email_classifications[email_id] = result  # type: ignore[attr-defined]

    return result


def mail_summarize_thread(ws: WorkspaceState, *, thread_id: str = "", **_: Any) -> Dict[str, Any]:
    """
    Summarize an email thread. Gathers all emails with matching thread_id,
    returns participant list, message count, timeline, and key topics.

    Also stores the summary on ws.thread_summaries for grader tracking.
    """
    thread_emails = []
    for pool in (ws.emails, ws.drafts, ws.sent_emails):
        for e in pool:
            if e.thread_id == thread_id or e.id == thread_id:
                thread_emails.append(e)

    if not thread_emails:
        return {"error": f"No emails found for thread '{thread_id}'",
                "hint": "Use mail/list_inbox and check thread_id fields."}

    # Sort by timestamp
    thread_emails.sort(key=lambda e: e.timestamp)

    participants = list({e.sender for e in thread_emails}
                        | {r for e in thread_emails for r in e.recipients})
    subjects = list({e.subject for e in thread_emails})

    # Extract key terms from bodies (deterministic: top words by frequency)
    all_text = " ".join(e.body for e in thread_emails).lower()
    stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "to",
            "of", "and", "or", "in", "on", "at", "for", "with", "from", "by",
            "this", "that", "it", "we", "our", "has", "have", "had", "not",
            "but", "if", "so", "as", "do", "can", "will"}
    words = [w.strip(".,!?:;\"'()-") for w in all_text.split()
             if len(w.strip(".,!?:;\"'()-")) > 2]
    freq: Dict[str, int] = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1
    key_topics = sorted(freq, key=freq.get, reverse=True)[:8]

    result = {
        "thread_id": thread_id,
        "message_count": len(thread_emails),
        "participants": sorted(participants),
        "subjects": subjects,
        "first_message": thread_emails[0].timestamp,
        "last_message": thread_emails[-1].timestamp,
        "key_topics": key_topics,
        "messages": [
            {"id": e.id, "sender": e.sender, "timestamp": e.timestamp,
             "subject": e.subject, "body_preview": e.body[:200]}
            for e in thread_emails
        ],
    }

    # Track thread summary on workspace state (for inbox_triage grader)
    if not hasattr(ws, "thread_summaries") or not isinstance(getattr(ws, "thread_summaries", None), dict):
        ws.thread_summaries = {}  # type: ignore[attr-defined]
    ws.thread_summaries[thread_id] = result  # type: ignore[attr-defined]

    return result


def mail_send_reply(ws: WorkspaceState, *, email_id: str = "", body: str = "",
                    cc: List[str] = None, **_: Any) -> Dict[str, Any]:
    """Alias for mail_reply (Phase 2 semantic name). Reply to email with body."""
    return mail_reply(ws, email_id=email_id, body=body, cc=cc)


# ═══════════════════════════════════════════════════════════════════════
#  SLACK — 5 commands
# ═══════════════════════════════════════════════════════════════════════
def slack_list_channels(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """List all Slack channels with metadata."""
    return {"channels": [c.model_dump() for c in ws.slack_channels]}


def slack_read_channel(ws: WorkspaceState, *, channel: str = "", **_: Any) -> Dict[str, Any]:
    """Read messages from a channel. Returns error if channel doesn't exist."""
    # Validate channel exists
    channel_names = {c.name for c in ws.slack_channels}
    if channel_names and channel not in channel_names:
        return {"error": f"Channel '{channel}' not found",
                "hint": f"Available channels: {sorted(channel_names)}",
                "available_channels": sorted(channel_names)}

    msgs = [m.model_dump() for m in ws.slack_messages if m.channel == channel]
    return {"channel": channel, "messages": msgs, "message_count": len(msgs)}


def slack_send_message(ws: WorkspaceState, *, channel: str = "", text: str = "",
                       thread_ts: str = None, **_: Any) -> Dict[str, Any]:
    """Send a message to a Slack channel."""
    # Validate channel exists (if channels are seeded)
    if ws.slack_channels:
        channel_names = {c.name for c in ws.slack_channels}
        if channel not in channel_names:
            return {"error": f"Channel '{channel}' not found. Cannot send message.",
                    "hint": f"Available channels: {sorted(channel_names)}"}

    msg = SlackMessage(id=_ID("slack"), channel=channel, sender="agent",
                       text=text, timestamp=_TS(), thread_ts=thread_ts)
    ws.slack_messages.append(msg)
    ws.sent_slack.append(msg)
    return {"status": "sent", "message": msg.model_dump()}


def slack_list_dms(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """List direct messages (channels starting with 'dm-')."""
    dms = [m.model_dump() for m in ws.slack_messages if m.channel.startswith("dm-")]
    return {"direct_messages": dms, "count": len(dms)}


def slack_send_dm(ws: WorkspaceState, *, user: str = "", text: str = "", **_: Any) -> Dict[str, Any]:
    """Send a direct message to a user."""
    # Validate user exists in team
    if ws.team_members:
        team_emails = {m.email.lower() for m in ws.team_members}
        team_names = {m.name.lower() for m in ws.team_members}
        if user.lower() not in team_emails and user.lower() not in team_names:
            return {"error": f"User '{user}' not found in team",
                    "hint": f"Known team members: {[m.name for m in ws.team_members]}"}

    ch = f"dm-{user}"
    msg = SlackMessage(id=_ID("slack"), channel=ch, sender="agent",
                       text=text, timestamp=_TS())
    ws.slack_messages.append(msg)
    ws.sent_slack.append(msg)
    return {"status": "sent", "message": msg.model_dump()}


# ═══════════════════════════════════════════════════════════════════════
#  DRIVE — 5 commands
# ═══════════════════════════════════════════════════════════════════════
def drive_list_files(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """List all files (seed + created)."""
    all_f = ws.drive_files + ws.created_files
    return {"files": [f.model_dump() for f in all_f], "count": len(all_f)}


def drive_read_file(ws: WorkspaceState, *, file_id: str = "", **_: Any) -> Dict[str, Any]:
    """Read a specific file by ID."""
    for f in ws.drive_files + ws.created_files:
        if f.id == file_id:
            return f.model_dump()
    # Helpfully list available file IDs
    all_ids = [f.id for f in ws.drive_files + ws.created_files]
    return {"error": f"File '{file_id}' not found",
            "hint": f"Available file IDs: {all_ids}" if all_ids else "No files exist yet."}


def drive_create_file(ws: WorkspaceState, *, name: str = "", content: str = "",
                      shared_with: List[str] = None, **_: Any) -> Dict[str, Any]:
    """Create a new file. Prevents duplicate filenames."""
    # Check for duplicate name
    existing_names = {f.name.lower() for f in ws.drive_files + ws.created_files}
    if name.lower() in existing_names:
        return {"error": f"File named '{name}' already exists",
                "hint": "Use drive/edit_file to modify existing files, or choose a different name."}

    f = DriveFile(id=_ID("file"), name=name, content=content, owner="agent@acme.com",
                  created_at=_TS(), modified_at=_TS(), shared_with=shared_with or [])
    ws.created_files.append(f)
    return {"status": "created", "file": f.model_dump()}


def drive_edit_file(ws: WorkspaceState, *, file_id: str = "", content: str = "", **_: Any) -> Dict[str, Any]:
    """Edit an existing file's content."""
    for f in ws.drive_files + ws.created_files:
        if f.id == file_id:
            f.content = content
            f.modified_at = _TS()
            return {"status": "updated", "file": f.model_dump()}
    return {"error": f"File '{file_id}' not found",
            "hint": "Use drive/list_files to see available file IDs."}


def drive_search_files(ws: WorkspaceState, *, query: str = "", **_: Any) -> Dict[str, Any]:
    """Search files by name or content. Case-insensitive substring match."""
    q = query.lower()
    if not q:
        return {"error": "Search query cannot be empty",
                "hint": "Provide a search term in the 'query' field."}
    hits = [f.model_dump() for f in ws.drive_files + ws.created_files
            if q in f.name.lower() or q in f.content.lower()]
    return {"results": hits, "query": query, "result_count": len(hits)}


# ═══════════════════════════════════════════════════════════════════════
#  CALENDAR — 5 commands
# ═══════════════════════════════════════════════════════════════════════
def calendar_list_events(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """List all calendar events (seed + scheduled)."""
    evts = ws.calendar_events + ws.scheduled_meetings
    return {"events": [e.model_dump() for e in evts], "count": len(evts)}


def calendar_check_availability(ws: WorkspaceState, *, attendee_emails: List[str] = None,
                                date: str = "", **_: Any) -> Dict[str, Any]:
    """Check availability for one or more attendees on a given date."""
    result: Dict[str, Any] = {}
    for email in (attendee_emails or []):
        member = next((m for m in ws.team_members if m.email.lower() == email.lower()), None)
        if not member:
            result[email] = {"error": f"Team member '{email}' not found",
                             "available": False}
            continue
        evts = [{"title": e.title, "start": e.start_time, "end": e.end_time}
                for e in ws.calendar_events + ws.scheduled_meetings
                if date in e.start_time and email.lower() in [a.lower() for a in e.attendees]]
        result[email] = {
            "name": member.name,
            "timezone": member.timezone,
            "working_hours": member.available_hours,
            "events_on_date": evts,
            "busy_slots": len(evts),
            "available": True,
        }
    if not result:
        return {"error": "No attendee emails provided",
                "hint": "Pass attendee_emails as a list of email addresses."}
    return result


def calendar_schedule_meeting(ws: WorkspaceState, *, title: str = "",
                              start_time: str = "", end_time: str = "",
                              attendees: List[str] = None, description: str = None,
                              location: str = None, **_: Any) -> Dict[str, Any]:
    """Schedule a meeting. Detects double-booking conflicts."""
    att = attendees or []

    # Validate time format
    try:
        st = datetime.fromisoformat(start_time)
        et = datetime.fromisoformat(end_time)
    except (ValueError, TypeError):
        return {"error": "Invalid time format. Use ISO 8601 (e.g., '2026-04-01T14:00:00-04:00').",
                "hint": "start_time and end_time must be valid ISO datetime strings."}

    if et <= st:
        return {"error": "end_time must be after start_time",
                "start_time": start_time, "end_time": end_time}

    # Detect scheduling conflicts
    conflicts = []
    for existing in ws.calendar_events + ws.scheduled_meetings:
        try:
            ex_st = datetime.fromisoformat(existing.start_time)
            ex_et = datetime.fromisoformat(existing.end_time)
        except (ValueError, TypeError):
            continue
        # Check overlap: new event overlaps existing
        if st < ex_et and et > ex_st:
            # Check if any attendee is double-booked
            overlap_attendees = set(a.lower() for a in att) & set(a.lower() for a in existing.attendees)
            if overlap_attendees:
                conflicts.append({
                    "conflicting_event": existing.title,
                    "event_id": existing.id,
                    "time": f"{existing.start_time} - {existing.end_time}",
                    "conflicting_attendees": sorted(overlap_attendees),
                })

    evt = CalendarEvent(id=_ID("cal"), title=title, start_time=start_time,
                        end_time=end_time, attendees=att,
                        description=description, location=location, organizer="agent@acme.com")
    ws.scheduled_meetings.append(evt)

    result: Dict[str, Any] = {"status": "scheduled", "event": evt.model_dump()}
    if conflicts:
        result["warnings"] = conflicts
        result["warning_message"] = f"Scheduling conflict detected with {len(conflicts)} event(s)."
    return result


def calendar_create_event(ws: WorkspaceState, *, title: str = "",
                          start_time: str = "", end_time: str = "",
                          attendees: List[str] = None, description: str = None,
                          location: str = None, **_: Any) -> Dict[str, Any]:
    """Alias for schedule_meeting (Phase 2 semantic name)."""
    return calendar_schedule_meeting(ws, title=title, start_time=start_time,
                                     end_time=end_time, attendees=attendees,
                                     description=description, location=location)


def calendar_get_team_roster(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """Get the full team roster with roles, timezones, and availability."""
    return {"team": [m.model_dump() for m in ws.team_members], "count": len(ws.team_members)}


# ═══════════════════════════════════════════════════════════════════════
#  JIRA — 7 commands
# ═══════════════════════════════════════════════════════════════════════
def jira_list_tickets(ws: WorkspaceState, **_: Any) -> Dict[str, Any]:
    """List all Jira tickets."""
    return {"tickets": [t.model_dump() for t in ws.jira_tickets], "count": len(ws.jira_tickets)}


def jira_get_ticket(ws: WorkspaceState, *, ticket_id: str = "", **_: Any) -> Dict[str, Any]:
    """Get full details for a specific ticket."""
    for t in ws.jira_tickets:
        if t.id == ticket_id:
            return t.model_dump()
    all_ids = [t.id for t in ws.jira_tickets]
    return {"error": f"Ticket '{ticket_id}' not found",
            "hint": f"Available ticket IDs: {all_ids}" if all_ids else "No tickets exist."}


def jira_read_ticket(ws: WorkspaceState, *, ticket_id: str = "", **_: Any) -> Dict[str, Any]:
    """Alias for get_ticket (Phase 2 semantic name)."""
    return jira_get_ticket(ws, ticket_id=ticket_id)


def jira_update_ticket(ws: WorkspaceState, *, ticket_id: str = "",
                       severity: str = None, priority: str = None,
                       assigned_to: str = None, component: str = None,
                       labels: List[str] = None, status: str = None, **_: Any) -> Dict[str, Any]:
    """Update ticket fields. Validates severity, priority, and status values."""
    for t in ws.jira_tickets:
        if t.id == ticket_id:
            # Validate severity
            if severity is not None:
                try:
                    t.severity = BugSeverity(severity)
                except ValueError:
                    valid = [s.value for s in BugSeverity]
                    return {"error": f"Invalid severity '{severity}'",
                            "valid_values": valid,
                            "hint": f"Severity must be one of: {valid}"}
            # Validate priority
            if priority is not None:
                try:
                    t.priority = Priority(priority)
                except ValueError:
                    valid = [p.value for p in Priority]
                    return {"error": f"Invalid priority '{priority}'",
                            "valid_values": valid,
                            "hint": f"Priority must be one of: {valid}"}
            # Validate status
            if status is not None:
                valid_statuses = {s.value for s in TicketStatus}
                if status not in valid_statuses:
                    return {"error": f"Invalid status '{status}'",
                            "valid_values": sorted(valid_statuses),
                            "hint": f"Status must be one of: {sorted(valid_statuses)}"}
                t.status = status

            if assigned_to is not None:
                t.assigned_to = assigned_to
            if component is not None:
                t.component = component
            if labels is not None:
                t.labels = labels

            ws.triage_actions.append({
                "bug_id": ticket_id,
                "severity": severity,
                "priority": priority,
                "assigned_to": assigned_to,
                "component": component,
                "labels": labels or [],
                "status": status,
                "timestamp": _TS(),
            })
            return {"status": "updated", "ticket": t.model_dump()}

    all_ids = [t.id for t in ws.jira_tickets]
    return {"error": f"Ticket '{ticket_id}' not found",
            "hint": f"Available ticket IDs: {all_ids}" if all_ids else "No tickets exist."}


def jira_create_ticket(ws: WorkspaceState, *, title: str = "", description: str = "",
                       severity: str = None, priority: str = None,
                       assigned_to: str = None, component: str = None,
                       labels: List[str] = None, **_: Any) -> Dict[str, Any]:
    """Create a new Jira ticket."""
    t = JiraTicket(id=_ID("TICKET"), title=title, description=description,
                   reporter="agent@acme.com", assigned_to=assigned_to, component=component,
                   labels=labels or [], created_at=_TS())
    if severity:
        try:
            t.severity = BugSeverity(severity)
        except ValueError:
            return {"error": f"Invalid severity '{severity}'",
                    "valid_values": [s.value for s in BugSeverity]}
    if priority:
        try:
            t.priority = Priority(priority)
        except ValueError:
            return {"error": f"Invalid priority '{priority}'",
                    "valid_values": [p.value for p in Priority]}
    ws.jira_tickets.append(t)
    return {"status": "created", "ticket": t.model_dump()}


def jira_add_comment(ws: WorkspaceState, *, ticket_id: str = "", text: str = "", **_: Any) -> Dict[str, Any]:
    """Add a comment to an existing ticket."""
    for t in ws.jira_tickets:
        if t.id == ticket_id:
            comment = {"id": _ID("cmt"), "author": "agent@acme.com",
                       "text": text, "timestamp": _TS()}
            t.comments.append(comment)
            ws.jira_comments.append({**comment, "ticket_id": ticket_id})
            return {"status": "comment_added", "comment": comment}
    return {"error": f"Ticket '{ticket_id}' not found",
            "hint": "Use jira/list_tickets to see available ticket IDs."}


def jira_assign_task(ws: WorkspaceState, *, ticket_id: str = "",
                     assigned_to: str = "", **_: Any) -> Dict[str, Any]:
    """Assign a ticket to a specific team member. Validates the team member exists."""
    for t in ws.jira_tickets:
        if t.id == ticket_id:
            # Validate assignee exists in team (if team is seeded)
            if ws.team_members:
                team_emails = {m.email.lower() for m in ws.team_members}
                if assigned_to.lower() not in team_emails:
                    return {"error": f"Assignee '{assigned_to}' is not a team member",
                            "valid_assignees": sorted(team_emails),
                            "hint": "Use calendar/get_team_roster to see team members."}
            t.assigned_to = assigned_to
            t.status = "in_progress"
            ws.triage_actions.append({
                "bug_id": ticket_id, "assigned_to": assigned_to,
                "action": "assign_task", "timestamp": _TS(),
            })
            return {"status": "assigned", "ticket": t.model_dump()}

    return {"error": f"Ticket '{ticket_id}' not found",
            "hint": "Use jira/list_tickets to see available ticket IDs."}


# ═══════════════════════════════════════════════════════════════════════
#  ACTION ROUTER
# ═══════════════════════════════════════════════════════════════════════
ACTION_ROUTER: Dict[Tuple[str, str], Callable[..., Dict[str, Any]]] = {
    # Mail (8 commands)
    ("mail", "list_inbox"):         mail_list_inbox,
    ("mail", "read_email"):         mail_read_email,
    ("mail", "compose_draft"):      mail_compose_draft,
    ("mail", "send_email"):         mail_send_email,
    ("mail", "reply"):              mail_reply,
    ("mail", "classify_email"):     mail_classify_email,
    ("mail", "summarize_thread"):   mail_summarize_thread,
    ("mail", "send_reply"):         mail_send_reply,
    # Slack (5 commands)
    ("slack", "list_channels"):     slack_list_channels,
    ("slack", "read_channel"):      slack_read_channel,
    ("slack", "send_message"):      slack_send_message,
    ("slack", "list_dms"):          slack_list_dms,
    ("slack", "send_dm"):           slack_send_dm,
    # Drive (5 commands)
    ("drive", "list_files"):        drive_list_files,
    ("drive", "read_file"):         drive_read_file,
    ("drive", "create_file"):       drive_create_file,
    ("drive", "edit_file"):         drive_edit_file,
    ("drive", "search_files"):      drive_search_files,
    # Calendar (5 commands)
    ("calendar", "list_events"):         calendar_list_events,
    ("calendar", "check_availability"):  calendar_check_availability,
    ("calendar", "schedule_meeting"):    calendar_schedule_meeting,
    ("calendar", "create_event"):        calendar_create_event,
    ("calendar", "get_team_roster"):     calendar_get_team_roster,
    # Jira (7 commands)
    ("jira", "list_tickets"):       jira_list_tickets,
    ("jira", "get_ticket"):         jira_get_ticket,
    ("jira", "read_ticket"):        jira_read_ticket,
    ("jira", "update_ticket"):      jira_update_ticket,
    ("jira", "create_ticket"):      jira_create_ticket,
    ("jira", "add_comment"):        jira_add_comment,
    ("jira", "assign_task"):        jira_assign_task,
}

VALID_TOOLS = {"mail", "slack", "drive", "calendar", "jira"}

# Precompute valid commands per tool for error messages
VALID_COMMANDS: Dict[str, List[str]] = {}
for (t, c) in ACTION_ROUTER:
    VALID_COMMANDS.setdefault(t, []).append(c)
for t in VALID_COMMANDS:
    VALID_COMMANDS[t].sort()


def route_action(ws: WorkspaceState, tool: str, command: str,
                 action_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch (tool, command) → handler with full validation.

    Returns a result dict.  On validation failure, returns an error dict
    with "validation_error" key set to True (so the env can apply penalty).
    """
    # 1. Validate tool name
    if tool not in VALID_TOOLS:
        return {"error": f"Unknown tool: '{tool}'",
                "valid_tools": sorted(VALID_TOOLS),
                "hint": f"Use one of: {', '.join(sorted(VALID_TOOLS))}",
                "validation_error": True}

    # 2. Validate command name
    handler = ACTION_ROUTER.get((tool, command))
    if handler is None:
        cmds = VALID_COMMANDS.get(tool, [])
        return {"error": f"Unknown command '{command}' for tool '{tool}'",
                "valid_commands": cmds,
                "hint": f"Valid commands for '{tool}': {', '.join(cmds)}",
                "validation_error": True}

    # 3. Validate input schema
    try:
        validated_input = validate_action_input(tool, command, action_input)
    except ActionValidationError as exc:
        return {"error": exc.message,
                "field": exc.field,
                "expected": exc.expected,
                "validation_error": True}

    # 4. Execute handler
    try:
        return handler(ws, **validated_input)
    except TypeError as exc:
        # Catch unexpected keyword arguments
        return {"error": f"Invalid arguments for {tool}/{command}: {exc}",
                "validation_error": True}
    except Exception as exc:
        return {"error": f"Action execution failed: {exc}"}
