#!/usr/bin/env python3
# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
inference.py — OpenEnv-compliant inference script for WorkSim Voyager.

Uses the OpenAI client to run an LLM agent through all 3 difficulty-tiered
tasks sequentially:
  1. inbox_triage_001   (Easy,   ~10 steps)
  2. meeting_coord_001  (Medium, ~15 steps)
  3. project_rescue_001 (Hard,   15–30 steps)

Environment variables (required):
  API_BASE_URL  — OpenAI-compatible API base URL (e.g. https://api-inference.huggingface.co/v1)
  MODEL_NAME    — Model identifier (e.g. meta-llama/Llama-3.3-70B-Instruct)
  HF_TOKEN      — HuggingFace token used as the API key

Constraints:
  - Max 40 steps per task
  - Total runtime < 20 minutes
  - Works on 2 vCPU, 8 GB RAM
  - Deterministic output (no randomness)
  - No crashes (all exceptions handled gracefully)
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

import requests
from openai import OpenAI

# ═══════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

# Required environment variables
API_BASE_URL: str = os.environ.get("API_BASE_URL", "")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "")
HF_TOKEN: str = os.environ.get("HF_TOKEN", "")

# Environment server (local or HF Space)
ENV_BASE_URL: str = os.environ.get("ENV_BASE_URL", "https://huggingface.co/spaces/srijan1617/MetaAI_WorkSimVoyager")

# Hard limits
MAX_STEPS_PER_TASK: int = 40          # Never exceed 40 steps per task
TOTAL_TIMEOUT_SECONDS: int = 1200     # 20 minutes hard cap
PER_TASK_TIMEOUT_SECONDS: int = 360   # 6 minutes per task
MAX_RETRIES: int = 2                  # Retry failed API calls

# The 3 required tasks (difficulty-tiered)
TASK_IDS: List[str] = [
    "inbox_triage_001",     # Easy
    "meeting_coord_001",    # Medium
    "project_rescue_001",   # Hard
]

# ═══════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are a workplace assistant inside the WorkSim Voyager environment.
You have 5 tools: mail, slack, drive, calendar, jira — each with multiple commands.
Complete the assigned task as accurately as possible. Partial credit is awarded.

STRATEGY:
1. Always read context before acting (list emails, read Slack, list files, etc.)
2. Use the EXACT tool function names (e.g. mail_list_inbox, slack_read_channel)
3. Provide ALL required parameters for each function call
4. Invalid or repeated actions incur penalties — avoid them
5. Each correct action earns incremental reward — maximize coverage
6. Work systematically: gather info → plan → execute → verify

IMPORTANT:
- You get partial credit for each correct sub-step
- Classify ALL emails when asked (don't skip any)
- Always check calendar availability BEFORE scheduling
- Include all required attendees in meetings
- Use proper email formatting with meaningful subject and body"""

# ═══════════════════════════════════════════════════════════════════════
#  OPENAI TOOL DEFINITIONS (30 commands across 5 tools)
# ═══════════════════════════════════════════════════════════════════════

TOOL_DEFS: List[Dict[str, Any]] = [
    # ── MAIL (8 commands) ──────────────────────────────────────────
    {"type": "function", "function": {"name": "mail_list_inbox",
        "description": "List all emails in the inbox",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "mail_read_email",
        "description": "Read a specific email by ID",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string", "description": "ID of the email to read"}},
            "required": ["email_id"]}}},
    {"type": "function", "function": {"name": "mail_compose_draft",
        "description": "Compose an email draft without sending",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "array", "items": {"type": "string"}, "description": "Recipient email addresses"},
            "subject": {"type": "string", "description": "Email subject"},
            "body": {"type": "string", "description": "Email body"},
            "cc": {"type": "array", "items": {"type": "string"}, "description": "CC recipients"},
            "thread_id": {"type": "string", "description": "Thread ID to reply in"}},
            "required": ["to", "subject", "body"]}}},
    {"type": "function", "function": {"name": "mail_send_email",
        "description": "Send an email (compose+send). Can also send a draft by passing draft_id.",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "array", "items": {"type": "string"}},
            "subject": {"type": "string"},
            "body": {"type": "string"},
            "cc": {"type": "array", "items": {"type": "string"}},
            "draft_id": {"type": "string", "description": "Send an existing draft by ID"},
            "thread_id": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "mail_reply",
        "description": "Reply to an existing email. Auto-sets recipients and subject.",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string", "description": "ID of the email to reply to"},
            "body": {"type": "string", "description": "Reply body text"},
            "cc": {"type": "array", "items": {"type": "string"}}},
            "required": ["email_id", "body"]}}},
    {"type": "function", "function": {"name": "mail_classify_email",
        "description": "Classify an email into category (urgent, bug_report, meeting_request, client_escalation, info, general) with priority and suggested action.",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string", "description": "ID of the email to classify"}},
            "required": ["email_id"]}}},
    {"type": "function", "function": {"name": "mail_summarize_thread",
        "description": "Summarize an email thread: participants, message count, timeline, key topics.",
        "parameters": {"type": "object", "properties": {
            "thread_id": {"type": "string", "description": "Thread ID to summarize"}},
            "required": ["thread_id"]}}},
    {"type": "function", "function": {"name": "mail_send_reply",
        "description": "Send a reply to an email (alias for mail_reply).",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string"},
            "body": {"type": "string"},
            "cc": {"type": "array", "items": {"type": "string"}}},
            "required": ["email_id", "body"]}}},

    # ── SLACK (5 commands) ─────────────────────────────────────────
    {"type": "function", "function": {"name": "slack_list_channels",
        "description": "List all Slack channels",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "slack_read_channel",
        "description": "Read messages from a Slack channel",
        "parameters": {"type": "object", "properties": {
            "channel": {"type": "string", "description": "Channel name"}},
            "required": ["channel"]}}},
    {"type": "function", "function": {"name": "slack_send_message",
        "description": "Send a message to a Slack channel",
        "parameters": {"type": "object", "properties": {
            "channel": {"type": "string", "description": "Channel name"},
            "text": {"type": "string", "description": "Message text"},
            "thread_ts": {"type": "string", "description": "Thread timestamp for replies"}},
            "required": ["channel", "text"]}}},
    {"type": "function", "function": {"name": "slack_list_dms",
        "description": "List direct messages",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "slack_send_dm",
        "description": "Send a direct message to a user",
        "parameters": {"type": "object", "properties": {
            "user": {"type": "string", "description": "User name or email"},
            "text": {"type": "string", "description": "Message text"}},
            "required": ["user", "text"]}}},

    # ── DRIVE (5 commands) ─────────────────────────────────────────
    {"type": "function", "function": {"name": "drive_list_files",
        "description": "List all files in Drive",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "drive_read_file",
        "description": "Read a file by ID",
        "parameters": {"type": "object", "properties": {
            "file_id": {"type": "string"}},
            "required": ["file_id"]}}},
    {"type": "function", "function": {"name": "drive_create_file",
        "description": "Create a new file in Drive",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "File name"},
            "content": {"type": "string", "description": "File content"},
            "shared_with": {"type": "array", "items": {"type": "string"}}},
            "required": ["name"]}}},
    {"type": "function", "function": {"name": "drive_edit_file",
        "description": "Edit an existing file's content",
        "parameters": {"type": "object", "properties": {
            "file_id": {"type": "string"},
            "content": {"type": "string"}},
            "required": ["file_id", "content"]}}},
    {"type": "function", "function": {"name": "drive_search_files",
        "description": "Search files by name or content",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}},
            "required": ["query"]}}},

    # ── CALENDAR (5 commands) ──────────────────────────────────────
    {"type": "function", "function": {"name": "calendar_list_events",
        "description": "List all calendar events",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "calendar_check_availability",
        "description": "Check attendee availability for a specific date",
        "parameters": {"type": "object", "properties": {
            "attendee_emails": {"type": "array", "items": {"type": "string"},
                               "description": "Email addresses to check"},
            "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}},
            "required": ["attendee_emails", "date"]}}},
    {"type": "function", "function": {"name": "calendar_schedule_meeting",
        "description": "Schedule a meeting. Detects conflicts automatically.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "start_time": {"type": "string", "description": "ISO 8601 datetime"},
            "end_time": {"type": "string", "description": "ISO 8601 datetime"},
            "attendees": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string"},
            "location": {"type": "string"}},
            "required": ["title", "start_time", "end_time", "attendees"]}}},
    {"type": "function", "function": {"name": "calendar_create_event",
        "description": "Create a calendar event (alias for schedule_meeting).",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "start_time": {"type": "string"},
            "end_time": {"type": "string"},
            "attendees": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string"},
            "location": {"type": "string"}},
            "required": ["title", "start_time", "end_time"]}}},
    {"type": "function", "function": {"name": "calendar_get_team_roster",
        "description": "Get team roster with roles, timezones, and working hours",
        "parameters": {"type": "object", "properties": {}}}},

    # ── JIRA (7 commands) ──────────────────────────────────────────
    {"type": "function", "function": {"name": "jira_list_tickets",
        "description": "List all Jira tickets",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "jira_get_ticket",
        "description": "Get full details for a specific ticket",
        "parameters": {"type": "object", "properties": {
            "ticket_id": {"type": "string"}},
            "required": ["ticket_id"]}}},
    {"type": "function", "function": {"name": "jira_read_ticket",
        "description": "Read a ticket (alias for get_ticket)",
        "parameters": {"type": "object", "properties": {
            "ticket_id": {"type": "string"}},
            "required": ["ticket_id"]}}},
    {"type": "function", "function": {"name": "jira_update_ticket",
        "description": "Update a Jira ticket fields (severity, priority, assignee, component, labels, status)",
        "parameters": {"type": "object", "properties": {
            "ticket_id": {"type": "string"},
            "severity": {"type": "string", "enum": ["blocker", "major", "minor", "trivial"]},
            "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
            "assigned_to": {"type": "string"},
            "component": {"type": "string"},
            "labels": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string", "enum": ["open", "in_progress", "triaged", "resolved", "closed"]}},
            "required": ["ticket_id"]}}},
    {"type": "function", "function": {"name": "jira_create_ticket",
        "description": "Create a new Jira ticket",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "severity": {"type": "string", "enum": ["blocker", "major", "minor", "trivial"]},
            "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
            "assigned_to": {"type": "string"},
            "component": {"type": "string"},
            "labels": {"type": "array", "items": {"type": "string"}}},
            "required": ["title", "description"]}}},
    {"type": "function", "function": {"name": "jira_add_comment",
        "description": "Add a comment to a ticket",
        "parameters": {"type": "object", "properties": {
            "ticket_id": {"type": "string"},
            "text": {"type": "string"}},
            "required": ["ticket_id", "text"]}}},
    {"type": "function", "function": {"name": "jira_assign_task",
        "description": "Assign a ticket to a team member. Validates team membership.",
        "parameters": {"type": "object", "properties": {
            "ticket_id": {"type": "string", "description": "Ticket ID to assign"},
            "assigned_to": {"type": "string", "description": "Email of the assignee"}},
            "required": ["ticket_id", "assigned_to"]}}},
]


# ═══════════════════════════════════════════════════════════════════════
#  ENVIRONMENT HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════════

class EnvClient:
    """Lightweight HTTP client to interact with the WorkSim Voyager server."""

    def __init__(self, base_url: str) -> None:
        self._session = requests.Session()
        self._base = base_url.rstrip("/")

    def health(self) -> Dict[str, Any]:
        """Check if the environment server is healthy."""
        resp = self._session.get(f"{self._base}/health", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def reset(self, task_id: str) -> Dict[str, Any]:
        """Reset the environment for a specific task."""
        resp = self._session.post(
            f"{self._base}/reset",
            json={"task_id": task_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def step(self, tool: str, command: str, action_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action step."""
        resp = self._session.post(
            f"{self._base}/step",
            json={"action": {"tool": tool, "command": command, "input": action_input}},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def state(self) -> Dict[str, Any]:
        """Get the current episode state."""
        resp = self._session.get(f"{self._base}/state", timeout=10)
        resp.raise_for_status()
        return resp.json()


# ═══════════════════════════════════════════════════════════════════════
#  AGENT LOOP
# ═══════════════════════════════════════════════════════════════════════

def _parse_function_name(name: str) -> tuple:
    """Split 'mail_send_email' → ('mail', 'send_email')."""
    parts = name.split("_", 1)
    return (parts[0], parts[1]) if len(parts) > 1 else (parts[0], "")


def run_task(
    client: OpenAI,
    env: EnvClient,
    task_id: str,
    model: str,
    task_timeout: float,
) -> Dict[str, Any]:
    """
    Run the agent loop for a single task.

    Returns a result dict with:
      - task_id, score, steps, errors, done, elapsed_seconds
    """
    task_start = time.monotonic()
    print(f"\n{'━' * 70}")
    print(f"  TASK: {task_id}")
    print(f"{'━' * 70}")

    # ── Reset environment ─────────────────────────────────────────────
    try:
        reset_result = env.reset(task_id)
    except Exception as exc:
        print(f"  ✗ Failed to reset environment: {exc}")
        return {
            "task_id": task_id, "score": 0.0, "steps": 0,
            "errors": 1, "done": False, "elapsed_seconds": 0.0,
        }

    info = reset_result.get("info", {})
    description = info.get("task_description", "No description available.")
    max_steps_env = info.get("max_steps", MAX_STEPS_PER_TASK)
    max_steps = min(MAX_STEPS_PER_TASK, max_steps_env)

    print(f"  Description: {description[:150]}...")
    print(f"  Max steps: {max_steps}")
    print(f"  Available tools: {info.get('available_tools', [])}")
    print()

    # ── Build initial messages ────────────────────────────────────────
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Complete this task:\n\n{description}"},
    ]

    total_reward: float = 0.0
    step_count: int = 0
    error_count: int = 0
    done: bool = False
    final_score: float = 0.0

    # ── Agent loop ────────────────────────────────────────────────────
    for turn in range(max_steps):
        # Check timeout
        elapsed = time.monotonic() - task_start
        if elapsed > task_timeout:
            print(f"  ⏱ Task timeout after {elapsed:.1f}s")
            break

        if done:
            break

        # ── Call LLM ──────────────────────────────────────────────────
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_DEFS,
                tool_choice="auto",
                temperature=0.0,   # Deterministic
                max_tokens=2048,
            )
        except Exception as exc:
            print(f"  ✗ LLM API error on turn {turn + 1}: {exc}")
            error_count += 1
            # Retry logic: add an error message and continue
            if error_count <= MAX_RETRIES:
                time.sleep(2)
                continue
            else:
                print(f"  ✗ Max retries exceeded. Stopping task.")
                break

        choice = response.choices[0]
        message = choice.message

        # Append assistant message to history
        messages.append(message.model_dump(exclude_none=True))

        # ── Process tool calls ────────────────────────────────────────
        if message.tool_calls:
            for tc in message.tool_calls:
                tool, command = _parse_function_name(tc.function.name)

                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except (json.JSONDecodeError, TypeError):
                    args = {}

                step_count += 1
                print(f"  [{step_count:2d}] {tool}.{command}({json.dumps(args, default=str)[:100]})")

                # ── Execute step ──────────────────────────────────────
                try:
                    step_result = env.step(tool, command, args)
                except Exception as exc:
                    print(f"       ✗ Step execution error: {exc}")
                    error_count += 1
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": str(exc)}),
                    })
                    continue

                step_reward = step_result.get("reward", 0) or 0
                total_reward += step_reward
                done = step_result.get("done", False)

                # Extract action result for LLM context
                action_result = step_result.get("info", {}).get("action_result", {})
                cumulative = step_result.get("info", {}).get("cumulative_reward", 0)
                grader_score = step_result.get("info", {}).get("reward_breakdown", {}).get("grader_score", 0)

                # Feed result back to LLM
                result_str = json.dumps(action_result, default=str)
                # Truncate to avoid context overflow on low-memory systems
                if len(result_str) > 4000:
                    result_str = result_str[:4000] + "...(truncated)"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

                # Print status
                has_error = "error" in action_result
                status = "✗" if has_error else "✓"
                print(f"       {status} reward={step_reward:+.4f}  "
                      f"cum={cumulative:.4f}  grader={grader_score:.4f}  "
                      f"done={done}")
                if has_error:
                    error_count += 1
                    err_msg = action_result.get("error", "")[:80]
                    print(f"       ERROR: {err_msg}")

                if done:
                    break

        elif choice.finish_reason == "stop":
            # LLM decided it's done (no more tool calls)
            print(f"  ── LLM finished (no more tool calls) at step {step_count}")
            break

    # ── Get final state ───────────────────────────────────────────────
    try:
        final_state = env.state()
        final_score = final_state.get("cumulative_reward", 0.0)
        step_count = final_state.get("step_count", step_count)
        error_count_env = final_state.get("error_count", 0)
    except Exception:
        final_score = total_reward

    elapsed = time.monotonic() - task_start

    print(f"\n  {'─' * 50}")
    print(f"  Result: score={final_score:.4f}  steps={step_count}  "
          f"errors={error_count}  time={elapsed:.1f}s")
    print(f"  {'─' * 50}")

    return {
        "task_id": task_id,
        "score": round(final_score, 4),
        "steps": step_count,
        "errors": error_count,
        "done": done,
        "elapsed_seconds": round(elapsed, 1),
    }


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def validate_env_vars() -> bool:
    """Validate that all required environment variables are set."""
    missing = []
    if not API_BASE_URL:
        missing.append("API_BASE_URL")
    if not MODEL_NAME:
        missing.append("MODEL_NAME")
    if not HF_TOKEN:
        missing.append("HF_TOKEN")

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print()
        print("Required environment variables:")
        print("  API_BASE_URL  — OpenAI-compatible API base URL")
        print("  MODEL_NAME    — Model identifier")
        print("  HF_TOKEN      — HuggingFace token (used as API key)")
        print()
        print("Example:")
        print("  export API_BASE_URL=https://api-inference.huggingface.co/v1")
        print("  export MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct")
        print("  export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx")
        return False
    return True


def main() -> None:
    """Run inference on all 3 tasks and print results."""
    global_start = time.monotonic()

    print("=" * 70)
    print("  WorkSim Voyager — Inference Script")
    print("=" * 70)
    print()

    # ── Validate environment variables ────────────────────────────────
    if not validate_env_vars():
        sys.exit(1)

    print(f"  API Base URL: {API_BASE_URL}")
    print(f"  Model:        {MODEL_NAME}")
    print(f"  HF Token:     {'*' * 8}...{HF_TOKEN[-4:] if len(HF_TOKEN) > 4 else '****'}")
    print(f"  Env Server:   {ENV_BASE_URL}")
    print(f"  Tasks:        {TASK_IDS}")
    print(f"  Max steps:    {MAX_STEPS_PER_TASK} per task")
    print(f"  Timeout:      {TOTAL_TIMEOUT_SECONDS}s total, {PER_TASK_TIMEOUT_SECONDS}s per task")
    print()

    # ── Initialize clients ────────────────────────────────────────────
    oai_client = OpenAI(
        api_key=HF_TOKEN,
        base_url=API_BASE_URL,
    )
    env_client = EnvClient(ENV_BASE_URL)

    # ── Health check ──────────────────────────────────────────────────
    try:
        health = env_client.health()
        print(f"  Environment health: {health.get('status', 'unknown')}")
    except Exception as exc:
        print(f"  WARNING: Environment health check failed: {exc}")
        print(f"  Continuing anyway — server may still respond to requests.")
    print()

    # ── Run all 3 tasks sequentially ──────────────────────────────────
    results: List[Dict[str, Any]] = []

    for i, task_id in enumerate(TASK_IDS, 1):
        # Check global timeout
        global_elapsed = time.monotonic() - global_start
        remaining = TOTAL_TIMEOUT_SECONDS - global_elapsed
        if remaining < 30:
            print(f"\n⏱ Global timeout approaching ({global_elapsed:.0f}s elapsed). Skipping remaining tasks.")
            # Record zero scores for skipped tasks
            results.append({
                "task_id": task_id, "score": 0.0, "steps": 0,
                "errors": 0, "done": False, "elapsed_seconds": 0.0,
            })
            continue

        task_timeout = min(PER_TASK_TIMEOUT_SECONDS, remaining - 10)

        try:
            result = run_task(
                client=oai_client,
                env=env_client,
                task_id=task_id,
                model=MODEL_NAME,
                task_timeout=task_timeout,
            )
        except Exception as exc:
            print(f"\n  ✗ FATAL ERROR on task {task_id}: {exc}")
            traceback.print_exc()
            result = {
                "task_id": task_id, "score": 0.0, "steps": 0,
                "errors": 1, "done": False, "elapsed_seconds": 0.0,
            }

        results.append(result)

    # ── Print summary ─────────────────────────────────────────────────
    total_elapsed = time.monotonic() - global_start

    print()
    print("=" * 70)
    print("  INFERENCE RESULTS SUMMARY")
    print("=" * 70)
    print()
    print(f"  {'Task ID':<25} {'Score':>8} {'Steps':>7} {'Errors':>8} {'Time (s)':>10} {'Done':>6}")
    print(f"  {'─' * 25} {'─' * 8} {'─' * 7} {'─' * 8} {'─' * 10} {'─' * 6}")

    total_score: float = 0.0
    for r in results:
        total_score += r["score"]
        done_str = "✓" if r["done"] else "✗"
        print(f"  {r['task_id']:<25} {r['score']:>8.4f} {r['steps']:>7d} "
              f"{r['errors']:>8d} {r['elapsed_seconds']:>10.1f} {done_str:>6}")

    avg_score = total_score / len(results) if results else 0.0

    print(f"  {'─' * 25} {'─' * 8} {'─' * 7} {'─' * 8} {'─' * 10} {'─' * 6}")
    print(f"  {'AVERAGE':<25} {avg_score:>8.4f}")
    print(f"  {'TOTAL':<25} {total_score:>8.4f}")
    print()
    print(f"  Total runtime: {total_elapsed:.1f}s ({total_elapsed / 60:.1f} minutes)")
    print(f"  Tasks completed: {sum(1 for r in results if r['done'])}/{len(results)}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL ERROR: {exc}")
        traceback.print_exc()
        sys.exit(1)
