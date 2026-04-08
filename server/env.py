# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
WorkSim Voyager Environment — core implementation (Phase 1–5).

Accepts WorkSimAction {tool, command, input} and returns
{observation, reward, done, info} via deterministic, in-memory simulation.

Phase 5 — Reward Function:
  - Action-category shaping bonuses (classification, scheduling, breakdown, email)
  - Graduated penalty schedule (wrong tool, repeated useless, destructive)
  - Per-step reward cap to prevent reward hacking
  - Duplicate-action detection (same tool+command+input → useless)
  - Destructive-action detection (empty overwrites, mass edits)
"""
from __future__ import annotations
import hashlib
import json
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
from server.graders.grader_registry import grade_task, grade_task_detailed
from server.models import WorkSimAction, WorkSimObservation, WorkspaceState, TaskSpec
from server.tasks.task_registry import TASK_REGISTRY
from server.tools.workspace_tools import (
    route_action, VALID_TOOLS, ACTION_ROUTER, VALID_COMMANDS,
)

# ═══════════════════════════════════════════════════════════════════════
#  REWARD CONSTANTS (Phase 5)
# ═══════════════════════════════════════════════════════════════════════

# ── Penalty schedule ──────────────────────────────────────────────────
WRONG_TOOL_PENALTY       = -0.10   # Unknown tool or command
REPEATED_USELESS_PENALTY = -0.10   # Exact same action repeated with no effect
DESTRUCTIVE_PENALTY      = -0.20   # Overwriting with empty content, mass delete
VALIDATION_ERROR_PENALTY = -0.05   # Schema validation failure (missing fields, wrong type)
EXECUTION_ERROR_PENALTY  = -0.03   # Handler returned error (not-found, bad value)

# ── Action-category shaping bonuses ──────────────────────────────────
# These reward the agent for taking the right KIND of action, on top of
# grader score improvements. Each bonus is awarded AT MOST ONCE per
# unique (tool, command, key_input) combination to prevent hacking.
CLASSIFICATION_BONUS = 0.20   # classify_email, summarize_thread
SCHEDULING_BONUS     = 0.30   # schedule_meeting, create_event, check_availability
TASK_BREAKDOWN_BONUS  = 0.30   # update_ticket, assign_task, create_ticket
EMAIL_DRAFTING_BONUS  = 0.20   # send_email, reply, compose_draft, send_reply

# ── Per-step reward cap ──────────────────────────────────────────────
MAX_STEP_REWARD = 0.35   # Hard cap: no single step can award more than this
MIN_STEP_REWARD = -0.20  # Floor: worst possible penalty per step

MAX_STEPS_DEFAULT = 25

# ── Action classification ────────────────────────────────────────────
_CLASSIFICATION_ACTIONS = {
    ("mail", "classify_email"), ("mail", "summarize_thread"),
}
_SCHEDULING_ACTIONS = {
    ("calendar", "schedule_meeting"), ("calendar", "create_event"),
    ("calendar", "check_availability"),
}
_TASK_BREAKDOWN_ACTIONS = {
    ("jira", "update_ticket"), ("jira", "assign_task"),
    ("jira", "create_ticket"), ("jira", "add_comment"),
}
_EMAIL_DRAFTING_ACTIONS = {
    ("mail", "send_email"), ("mail", "reply"), ("mail", "send_reply"),
    ("mail", "compose_draft"),
}
# Actions considered "read-only" — no bonus, but no destructive penalty either
_READ_ACTIONS = {
    ("mail", "list_inbox"), ("mail", "read_email"),
    ("slack", "list_channels"), ("slack", "read_channel"), ("slack", "list_dms"),
    ("drive", "list_files"), ("drive", "read_file"), ("drive", "search_files"),
    ("calendar", "list_events"), ("calendar", "get_team_roster"),
    ("jira", "list_tickets"), ("jira", "get_ticket"), ("jira", "read_ticket"),
}
# Actions that could be destructive if misused
_POTENTIALLY_DESTRUCTIVE = {
    ("drive", "edit_file"),  # Overwriting file with empty content
}


def _action_fingerprint(tool: str, command: str, action_input: Dict[str, Any]) -> str:
    """Deterministic hash of (tool, command, input) for duplicate detection."""
    canonical = json.dumps({"t": tool, "c": command, "i": action_input},
                           sort_keys=True, default=str)
    return hashlib.md5(canonical.encode()).hexdigest()[:16]


class WorkSimVoyagerEnvironment:
    """In-memory workplace simulation. No external APIs."""

    def __init__(self) -> None:
        self._ws = WorkspaceState()
        self._task_spec: Optional[TaskSpec] = None
        self._episode_id: str = str(uuid4())
        self._step_count: int = 0
        self._done: bool = False
        self._cumulative_reward: float = 0.0
        self._prev_grader_score: float = 0.0   # Track previous score for delta
        self._action_log: List[Dict[str, Any]] = []
        self._error_history: List[str] = []     # Error signatures for escalation
        self._grader_breakdown: Dict[str, Any] = {}
        # Phase 5: anti-hacking state
        self._action_fingerprints: List[str] = []       # All action fingerprints in order
        self._rewarded_actions: Set[str] = set()         # Fingerprints already given bonus
        self._reward_trace: List[Dict[str, Any]] = []    # Full reward decomposition per step

    # ── helpers ────────────────────────────────────────────────────────
    @property
    def workspace(self) -> WorkspaceState:
        return self._ws

    def _snapshot_observation(self) -> WorkSimObservation:
        ws = self._ws
        return WorkSimObservation(
            emails=[e.model_dump() for e in ws.emails + ws.drafts + ws.sent_emails],
            slack_messages=[m.model_dump() for m in ws.slack_messages],
            calendar=[e.model_dump() for e in ws.calendar_events + ws.scheduled_meetings],
            drive_files=[f.model_dump() for f in ws.drive_files + ws.created_files],
            jira_tickets=[t.model_dump() for t in ws.jira_tickets],
            step_count=self._step_count,
        )

    def _max_steps(self) -> int:
        return self._task_spec.max_steps if self._task_spec else MAX_STEPS_DEFAULT

    # ── Phase 5: Penalty computation ──────────────────────────────────
    def _compute_penalty(self, result: Dict[str, Any], tool: str, command: str,
                         action_input: Dict[str, Any], fingerprint: str) -> float:
        """
        Compute stepped penalty based on error type:
          -0.10  wrong tool / command
          -0.10  repeated useless action (exact duplicate with no state change)
          -0.20  destructive action (empty overwrite)
          -0.05  validation error
          -0.03  execution error (first occurrence)
        """
        penalty = 0.0

        # ── 1. Destructive action detection ──────────────────────────
        tc = (tool, command)
        if tc in _POTENTIALLY_DESTRUCTIVE:
            # Overwriting a file with empty content = destructive
            content = action_input.get("content", "")
            if isinstance(content, str) and len(content.strip()) == 0:
                return DESTRUCTIVE_PENALTY  # Immediately return worst penalty

        # ── 2. No error? Check for duplicates only ───────────────────
        if "error" not in result:
            # Check if this exact action was already performed
            if fingerprint in self._action_fingerprints[:-1]:
                # Exact duplicate — only penalize if it didn't improve the score
                # (we check this later in the reward function, but flag it now)
                return REPEATED_USELESS_PENALTY
            return 0.0

        # ── 3. Error-based penalties ─────────────────────────────────
        error_sig = f"{tool}/{command}/{result.get('error', '')[:50]}"

        # Wrong tool or unknown command → −0.10
        if result.get("validation_error"):
            err_text = result.get("error", "").lower()
            if "unknown tool" in err_text or "unknown command" in err_text:
                self._error_history.append(error_sig)
                return WRONG_TOOL_PENALTY

        # Repeated errors → escalated to −0.10 (useless repetition)
        if error_sig in self._error_history:
            self._error_history.append(error_sig)
            return REPEATED_USELESS_PENALTY

        self._error_history.append(error_sig)

        # Validation error (missing fields, wrong types) → −0.05
        if result.get("validation_error"):
            return VALIDATION_ERROR_PENALTY

        # Execution error (not found, invalid value) → −0.03
        return EXECUTION_ERROR_PENALTY

    # ── Phase 5: Action-category bonus ────────────────────────────────
    def _compute_action_bonus(self, tool: str, command: str,
                              fingerprint: str, has_error: bool,
                              grader_delta: float) -> float:
        """
        Award action-category shaping bonus on top of grader delta.

        Rules:
          +0.20  correct classification (classify_email, summarize_thread)
          +0.30  scheduling success (schedule_meeting, create_event)
          +0.30  task breakdown (update_ticket, assign_task)
          +0.20  email drafting (send_email, reply, compose_draft)

        Anti-hacking:
          - Only awarded if action succeeded (no error)
          - Only awarded if grader delta > 0 (action actually helped)
          - Each unique (tool, command, input) gets bonus AT MOST ONCE
          - Read-only actions never get a bonus
        """
        if has_error:
            return 0.0
        if grader_delta <= 0:
            return 0.0
        if fingerprint in self._rewarded_actions:
            return 0.0  # Already got bonus for this exact action

        tc = (tool, command)
        bonus = 0.0

        if tc in _CLASSIFICATION_ACTIONS:
            bonus = CLASSIFICATION_BONUS
        elif tc in _SCHEDULING_ACTIONS:
            bonus = SCHEDULING_BONUS
        elif tc in _TASK_BREAKDOWN_ACTIONS:
            bonus = TASK_BREAKDOWN_BONUS
        elif tc in _EMAIL_DRAFTING_ACTIONS:
            bonus = EMAIL_DRAFTING_BONUS

        if bonus > 0:
            # Scale bonus by grader improvement (smooth, not binary)
            # If grader delta is small, bonus is proportionally small
            scaled_bonus = bonus * min(1.0, grader_delta / 0.10)
            self._rewarded_actions.add(fingerprint)
            return round(scaled_bonus, 6)

        return 0.0

    # ── reset() ───────────────────────────────────────────────────────
    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None,
              task_id: Optional[str] = None, **kw: Any) -> Dict[str, Any]:
        if task_id and task_id in TASK_REGISTRY:
            td = TASK_REGISTRY[task_id]
        else:
            td = next(iter(TASK_REGISTRY.values()))
        self._task_spec = td.spec
        self._ws = WorkspaceState(
            emails=list(td.emails),
            slack_channels=list(getattr(td, "slack_channels", [])),
            slack_messages=list(getattr(td, "slack_messages", [])),
            drive_files=list(getattr(td, "drive_files", [])),
            jira_tickets=list(getattr(td, "jira_tickets", [])),
            calendar_events=list(td.calendar_events),
            team_members=list(td.team_members),
        )
        self._episode_id = episode_id or str(uuid4())
        self._step_count = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._prev_grader_score = 0.0
        self._action_log = []
        self._error_history = []
        self._grader_breakdown = {}
        self._action_fingerprints = []
        self._rewarded_actions = set()
        self._reward_trace = []
        obs = self._snapshot_observation()
        return {
            "observation": obs.model_dump(),
            "reward": 0.0, "done": False,
            "info": {
                "status": "ready",
                "task_id": self._task_spec.task_id,
                "task_type": self._task_spec.task_type.value,
                "task_description": self._task_spec.description,
                "max_steps": self._max_steps(),
                "available_tools": sorted(VALID_TOOLS),
                "available_commands": {t: sorted(c for (tt, c) in ACTION_ROUTER if tt == t)
                                       for t in sorted(VALID_TOOLS)},
                "grader_breakdown": {},
                "reward_breakdown": {},
            },
        }

    # ── step(action) ──────────────────────────────────────────────────
    def step(self, action: Any, **kw: Any) -> Dict[str, Any]:
        # Already done?
        if self._done:
            obs = self._snapshot_observation()
            return {"observation": obs.model_dump(),
                    "reward": 0.0, "done": True,
                    "info": {"error": "Episode done. Call reset().",
                             "cumulative_reward": round(self._cumulative_reward, 4),
                             "step": self._step_count,
                             "max_steps": self._max_steps(),
                             "grader_breakdown": self._grader_breakdown,
                             "reward_breakdown": {}}}

        self._step_count += 1

        # Parse action (handle dict or WorkSimAction)
        if isinstance(action, dict):
            tool = str(action.get("tool", "")).strip()
            command = str(action.get("command", "")).strip()
            action_input = dict(action.get("input", {}))
        elif isinstance(action, WorkSimAction):
            tool, command, action_input = action.tool, action.command, dict(action.input)
        else:
            tool = command = ""
            action_input = {}

        # Compute action fingerprint for duplicate detection
        fingerprint = _action_fingerprint(tool, command, action_input)
        self._action_fingerprints.append(fingerprint)

        # Route action through validation layer
        if not tool or not command:
            result = {
                "error": "Action must specify 'tool' and 'command'.",
                "validation_error": True,
                "hint": f"Available tools: {sorted(VALID_TOOLS)}",
            }
        else:
            result = route_action(self._ws, tool, command, action_input)

        has_error = "error" in result

        # ── Compute grader score delta ────────────────────────────────
        if self._task_spec:
            current_score, breakdown = grade_task_detailed(self._ws, self._task_spec)
            self._grader_breakdown = breakdown
        else:
            current_score = 0.0
            breakdown = {}
            self._grader_breakdown = {}

        grader_delta = max(0.0, current_score - self._prev_grader_score)

        # ── Compute penalty ───────────────────────────────────────────
        penalty = self._compute_penalty(result, tool, command, action_input, fingerprint)

        # ── Compute action-category bonus ────────────────────────────
        action_bonus = self._compute_action_bonus(
            tool, command, fingerprint, has_error, grader_delta)

        # ── Assemble step reward ─────────────────────────────────────
        # Components: grader_delta + action_bonus + penalty
        raw_reward = grader_delta + action_bonus + penalty

        # Apply per-step cap (anti-hacking)
        capped_reward = max(MIN_STEP_REWARD, min(MAX_STEP_REWARD, raw_reward))
        step_reward = round(capped_reward, 6)

        # Update cumulative (use grader score, not reward sum, for accurate tracking)
        self._prev_grader_score = current_score
        self._cumulative_reward = current_score

        # ── Build reward breakdown for introspection ─────────────────
        reward_breakdown = {
            "grader_delta": round(grader_delta, 6),
            "action_bonus": round(action_bonus, 6),
            "penalty": round(penalty, 6),
            "raw_reward": round(raw_reward, 6),
            "capped_reward": step_reward,
            "grader_score": round(current_score, 4),
            "action_category": (
                "classification" if (tool, command) in _CLASSIFICATION_ACTIONS else
                "scheduling" if (tool, command) in _SCHEDULING_ACTIONS else
                "task_breakdown" if (tool, command) in _TASK_BREAKDOWN_ACTIONS else
                "email_drafting" if (tool, command) in _EMAIL_DRAFTING_ACTIONS else
                "read" if (tool, command) in _READ_ACTIONS else
                "other"
            ),
            "is_duplicate": fingerprint in self._action_fingerprints[:-1],
            "was_capped": raw_reward != capped_reward,
        }
        self._reward_trace.append(reward_breakdown)

        # ── Log action ───────────────────────────────────────────────
        self._action_log.append({
            "step": self._step_count,
            "tool": tool,
            "command": command,
            "result_ok": not has_error,
            "error": result.get("error") if has_error else None,
            "reward": step_reward,
        })

        # ── Termination ──────────────────────────────────────────────
        if self._step_count >= self._max_steps() or current_score >= 0.99:
            self._done = True

        obs = self._snapshot_observation()
        return {
            "observation": obs.model_dump(),
            "reward": step_reward,
            "done": self._done,
            "info": {
                "action_result": result,
                "cumulative_reward": round(self._cumulative_reward, 4),
                "step": self._step_count,
                "max_steps": self._max_steps(),
                "grader_breakdown": breakdown,
                "reward_breakdown": reward_breakdown,
            },
        }

    # ── state() ───────────────────────────────────────────────────────
    def state(self) -> Dict[str, Any]:
        return {
            "episode_id": self._episode_id,
            "step_count": self._step_count,
            "done": self._done,
            "cumulative_reward": round(self._cumulative_reward, 4),
            "task_id": self._task_spec.task_id if self._task_spec else None,
            "error_count": len(self._error_history),
            "action_log": self._action_log,
            "grader_breakdown": self._grader_breakdown,
            "reward_trace": self._reward_trace,
        }
