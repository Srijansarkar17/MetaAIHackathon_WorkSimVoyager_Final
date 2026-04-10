# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
WorkSim Voyager Client — OpenEnv-compliant client for the WorkSim environment.

Provides WorkSimVoyagerEnv (EnvClient subclass) that can connect to:
  - A Docker image:   WorkSimVoyagerEnv.from_docker_image("image-name")
  - A running server: WorkSimVoyagerEnv(base_url="http://localhost:7860")
  - A HF Space:       WorkSimVoyagerEnv.from_env("org/space")

Example:
    >>> from client import WorkSimVoyagerEnv, WorkSimAction
    >>> env = await WorkSimVoyagerEnv.from_docker_image("worksim-voyager:latest")
    >>> result = await env.reset(task_id="inbox_triage_001")
    >>> result = await env.step(WorkSimAction(tool="mail", command="list_inbox", input={}))
    >>> await env.close()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult


# ── Action / Observation / State models ──────────────────────────────

@dataclass
class WorkSimAction:
    """Action for the WorkSim Voyager environment."""
    tool: str
    command: str
    input: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkSimObservation:
    """Observation returned from the WorkSim environment."""
    emails: List[Dict[str, Any]] = field(default_factory=list)
    slack_messages: List[Dict[str, Any]] = field(default_factory=list)
    calendar: List[Dict[str, Any]] = field(default_factory=list)
    drive_files: List[Dict[str, Any]] = field(default_factory=list)
    jira_tickets: List[Dict[str, Any]] = field(default_factory=list)
    step_count: int = 0
    # Extra fields from the server response
    action_result: Optional[Dict[str, Any]] = None
    cumulative_reward: float = 0.0
    grader_breakdown: Optional[Dict[str, Any]] = None
    reward_breakdown: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None


@dataclass
class WorkSimState:
    """State of the WorkSim environment."""
    episode_id: Optional[str] = None
    step_count: int = 0
    done: bool = False
    cumulative_reward: float = 0.0
    task_id: Optional[str] = None
    error_count: int = 0
    action_log: List[Dict[str, Any]] = field(default_factory=list)


# ── Client ───────────────────────────────────────────────────────────

class WorkSimVoyagerEnv(EnvClient[WorkSimAction, WorkSimObservation, WorkSimState]):
    """
    Client for the WorkSim Voyager Environment.

    Bridges the OpenEnv SDK with the WorkSim server's action protocol.
    Actions are sent as {tool, command, input} dicts over WebSocket.

    Example with Docker:
        >>> env = await WorkSimVoyagerEnv.from_docker_image("worksim-voyager:latest")
        >>> try:
        ...     result = await env.reset(task_id="inbox_triage_001")
        ...     result = await env.step(WorkSimAction(
        ...         tool="mail", command="list_inbox", input={}
        ...     ))
        ...     print(result.reward, result.done)
        ... finally:
        ...     await env.close()
    """

    def _step_payload(self, action: WorkSimAction) -> Dict[str, Any]:
        """Convert WorkSimAction to the JSON payload the server expects."""
        return {
            "tool": action.tool,
            "command": action.command,
            "input": action.input,
        }

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[WorkSimObservation]:
        """Convert a JSON response from the server to StepResult."""
        obs_data = payload.get("observation", {})
        info = payload.get("info", {})

        observation = WorkSimObservation(
            emails=obs_data.get("emails", []),
            slack_messages=obs_data.get("slack_messages", []),
            calendar=obs_data.get("calendar", []),
            drive_files=obs_data.get("drive_files", []),
            jira_tickets=obs_data.get("jira_tickets", []),
            step_count=obs_data.get("step_count", 0),
            action_result=info.get("action_result"),
            cumulative_reward=info.get("cumulative_reward", 0.0),
            grader_breakdown=info.get("grader_breakdown"),
            reward_breakdown=info.get("reward_breakdown"),
            info=info,
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> WorkSimState:
        """Convert a JSON response from the state endpoint to WorkSimState."""
        return WorkSimState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            done=payload.get("done", False),
            cumulative_reward=payload.get("cumulative_reward", 0.0),
            task_id=payload.get("task_id"),
            error_count=payload.get("error_count", 0),
            action_log=payload.get("action_log", []),
        )
