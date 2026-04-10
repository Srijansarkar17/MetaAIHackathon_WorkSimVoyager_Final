"""
Inference Script — WorkSim Voyager
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    LOCAL_IMAGE_NAME The name of the local image to use for the environment if you are using from_docker_image()
                     method

- Defaults are set only for API_BASE_URL and MODEL_NAME
    (and should reflect your active inference setup):
    API_BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
    MODEL_NAME = os.getenv("MODEL_NAME", "<your-active-model>")

- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables

STDOUT FORMAT
- The script must emit exactly three line types to stdout, in this order:

    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

  Rules:
    - One [START] line at episode begin.
    - One [STEP] line per step, immediately after env.step() returns.
    - One [END] line after env.close(), always emitted (even on exception).
    - reward and rewards are formatted to 2 decimal places.
    - done and success are lowercase booleans: true or false.
    - error is the raw last_action_error string, or null if none.
    - All fields on a single line with no newlines within a line.
    - Each tasks should return score in [0, 1]

  Example:
    [START] task=click-test env=miniwob model=Qwen3-VL-30B
    [STEP] step=1 action=click('123') reward=0.00 done=false error=null
    [STEP] step=2 action=fill('456','text') reward=0.00 done=false error=null
    [STEP] step=3 action=click('789') reward=1.00 done=true error=null
    [END] success=true steps=3 score=1.00 rewards=0.00,0.00,1.00
"""

import asyncio
import json
import os
import textwrap
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

# ═══════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

IMAGE_NAME = os.getenv("IMAGE_NAME")  # If you are using docker image
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

# HF Space URL — the environment is already deployed here
HF_SPACE_URL = os.getenv(
    "ENV_BASE_URL",
    "https://srijan1617-metaai-worksimvoyager.hf.space",
)

# The 3 required tasks (difficulty-tiered)
TASK_IDS: List[str] = [
    "inbox_triage_001",     # Easy
    "meeting_coord_001",    # Medium
    "project_rescue_001",   # Hard
]

BENCHMARK = "worksim_voyager"

# Hard limits
MAX_STEPS_PER_TASK: int = 40          # Never exceed 40 steps per task
TOTAL_TIMEOUT_SECONDS: int = 1200     # 20 minutes hard cap
PER_TASK_TIMEOUT_SECONDS: int = 360   # 6 minutes per task
MAX_RETRIES: int = 2                  # Retry failed API calls

SUCCESS_SCORE_THRESHOLD = 0.1         # normalized score in [0, 1]

# ═══════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = textwrap.dedent("""
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
    - Use proper email formatting with meaningful subject and body
""").strip()

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
#  STDOUT LOGGING (hackathon-compliant format)
# ═══════════════════════════════════════════════════════════════════════

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ═══════════════════════════════════════════════════════════════════════
#  HELPER: Parse function name → (tool, command)
# ═══════════════════════════════════════════════════════════════════════

def _parse_function_name(name: str) -> tuple:
    """Split 'mail_send_email' → ('mail', 'send_email')."""
    parts = name.split("_", 1)
    return (parts[0], parts[1]) if len(parts) > 1 else (parts[0], "")


# ═══════════════════════════════════════════════════════════════════════
#  ENVIRONMENT CLIENT — HTTP-based, no Docker dependency
# ═══════════════════════════════════════════════════════════════════════

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EnvHTTPClient:
    """
    Lightweight HTTP client for the WorkSim Voyager environment.
    Talks directly to the server's /reset, /step, /state endpoints.
    No Docker dependency — works with any reachable server.
    """

    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/json"

    def health_check(self) -> bool:
        """Check if the server is reachable."""
        try:
            r = self._session.get(
                f"{self.base_url}/health", timeout=10, verify=False,
            )
            return r.status_code == 200
        except Exception:
            return False

    def reset(self, task_id: str) -> Dict[str, Any]:
        """POST /reset with task_id."""
        try:
            r = self._session.post(
                f"{self.base_url}/reset",
                json={"task_id": task_id},
                timeout=self.timeout,
                verify=False,
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            print(f"[DEBUG] reset() failed: {exc}", flush=True)
            return {"observation": {}, "reward": 0, "done": False, "info": {}}

    def step(self, tool: str, command: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /step with action={tool, command, input}."""
        try:
            r = self._session.post(
                f"{self.base_url}/step",
                json={"action": {"tool": tool, "command": command, "input": input_data}},
                timeout=self.timeout,
                verify=False,
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            print(f"[DEBUG] step() failed: {exc}", flush=True)
            return {"observation": {}, "reward": 0, "done": False,
                    "info": {"action_result": {"error": str(exc)}}}

    def state(self) -> Dict[str, Any]:
        """GET /state."""
        try:
            r = self._session.get(
                f"{self.base_url}/state", timeout=self.timeout, verify=False,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return {"cumulative_reward": 0, "step_count": 0}

    def close(self):
        """Close the HTTP session."""
        try:
            self._session.close()
        except Exception:
            pass


async def create_env():
    """
    Create environment connection with fallback strategy:
      1. Try OpenEnv SDK from_docker_image (if Docker is available)
      2. Fall back to direct HTTP connection to HF Space
    """
    # ── Strategy 1: OpenEnv SDK with Docker (preferred) ───────────────
    if IMAGE_NAME:
        try:
            from client import WorkSimVoyagerEnv
            env = await WorkSimVoyagerEnv.from_docker_image(IMAGE_NAME)
            print("[DEBUG] Connected via from_docker_image()", flush=True)
            return ("sdk", env)
        except Exception as exc:
            print(f"[DEBUG] from_docker_image() failed: {exc}", flush=True)
            print("[DEBUG] Falling back to HTTP client...", flush=True)

    # ── Strategy 2: Direct HTTP to HF Space ───────────────────────────
    env = EnvHTTPClient(base_url=HF_SPACE_URL)

    # Wait for the Space to be ready (may take time to wake up)
    for attempt in range(30):
        if env.health_check():
            print(f"[DEBUG] Connected via HTTP to {HF_SPACE_URL}", flush=True)
            return ("http", env)
        print(f"[DEBUG] Waiting for env server (attempt {attempt + 1}/30)...", flush=True)
        await asyncio.sleep(2)

    # Even if health check fails, return the client — step/reset will handle errors
    print(f"[DEBUG] Health check timed out, proceeding anyway...", flush=True)
    return ("http", env)


# ═══════════════════════════════════════════════════════════════════════
#  AGENT LOOP FOR A SINGLE TASK
# ═══════════════════════════════════════════════════════════════════════

async def run_task(
    oai_client: OpenAI,
    env_type: str,
    env: Any,
    task_id: str,
    model: str,
    task_timeout: float,
) -> Dict[str, Any]:
    """
    Run the agent loop for a single task.
    Supports both SDK (env_type="sdk") and HTTP (env_type="http") clients.
    """
    task_start = time.monotonic()

    rewards: List[float] = []
    steps_taken = 0
    score = 0
    success = False
    done = False

    log_start(task=task_id, env=BENCHMARK, model=model)

    try:
        # ── Reset environment for this task ───────────────────────────
        try:
            if env_type == "sdk":
                from client import WorkSimAction
                reset_result = await env.reset(task_id=task_id)
                obs = reset_result.observation
                info = getattr(obs, "info", None) or {}
            else:
                reset_data = env.reset(task_id=task_id)
                info = reset_data.get("info", {})
        except Exception as exc:
            print(f"[DEBUG] Failed to reset environment: {exc}", flush=True)
            log_end(success=False, steps=0, score=0, rewards=[])
            return {
                "task_id": task_id, "score": 0, "steps": 0,
                "rewards": [], "success": False, "done": False,
            }

        description = info.get("task_description", f"Complete task: {task_id}")
        max_steps_env = info.get("max_steps", MAX_STEPS_PER_TASK)
        max_steps = min(MAX_STEPS_PER_TASK, max_steps_env)

        # ── Build initial messages for LLM ────────────────────────────
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Complete this task:\n\n{description}"},
        ]

        error_count: int = 0

        # ── Agent loop ────────────────────────────────────────────────
        for turn in range(max_steps):
            elapsed = time.monotonic() - task_start
            if elapsed > task_timeout:
                break

            if done:
                break

            # ── Call LLM ──────────────────────────────────────────────
            try:
                response = oai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOL_DEFS,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=2048,
                )
            except Exception as exc:
                print(f"[DEBUG] LLM API error on turn {turn + 1}: {exc}", flush=True)
                error_count += 1
                if error_count <= MAX_RETRIES:
                    time.sleep(2)
                    continue
                else:
                    break

            choice = response.choices[0]
            message = choice.message

            # Append assistant message to history
            messages.append(message.model_dump(exclude_none=True))

            # ── Process tool calls ────────────────────────────────────
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool, command = _parse_function_name(tc.function.name)

                    try:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except (json.JSONDecodeError, TypeError):
                        args = {}

                    steps_taken += 1

                    action_str = f"{tool}_{command}({json.dumps(args, default=str)[:80]})"

                    # ── Execute step ──────────────────────────────────
                    try:
                        if env_type == "sdk":
                            from client import WorkSimAction
                            step_result = await env.step(
                                WorkSimAction(tool=tool, command=command, input=args)
                            )
                            step_reward = step_result.reward or 0
                            done = step_result.done
                            action_result = getattr(step_result.observation, "action_result", None) or {}
                        else:
                            step_data = env.step(tool=tool, command=command, input_data=args)
                            step_reward = step_data.get("reward", 0)
                            done = step_data.get("done", False)
                            action_result = step_data.get("info", {}).get("action_result", {})

                        error_msg = None
                        if isinstance(action_result, dict) and "error" in action_result:
                            error_msg = str(action_result["error"])

                        rewards.append(step_reward)

                        log_step(
                            step=steps_taken,
                            action=action_str,
                            reward=step_reward,
                            done=done,
                            error=error_msg,
                        )

                        result_str = json.dumps(action_result, default=str)
                        if len(result_str) > 4000:
                            result_str = result_str[:4000] + "...(truncated)"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result_str,
                        })

                    except Exception as exc:
                        error_msg = str(exc)
                        rewards.append(0)

                        log_step(
                            step=steps_taken,
                            action=action_str,
                            reward=0,
                            done=False,
                            error=error_msg,
                        )

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"error": error_msg}),
                        })

                    if done:
                        break

            elif choice.finish_reason == "stop":
                break

        # ── Compute final score ───────────────────────────────────────
        try:
            if env_type == "sdk":
                final_state = await env.state()
                score = getattr(final_state, "cumulative_reward", 0)
            else:
                state_data = env.state()
                score = state_data.get("cumulative_reward", 0)
        except Exception:
            score = sum(rewards)

        score = min(max(score, 0), 1)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_id} exception: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task_id": task_id,
        "score": round(score, 4),
        "steps": steps_taken,
        "rewards": rewards,
        "success": success,
        "done": done,
    }


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main() -> None:
    """Run inference on all 3 tasks sequentially."""
    global_start = time.monotonic()

    # ── Initialize OpenAI client ──────────────────────────────────────
    oai_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # ── Initialize environment (Docker → HTTP fallback) ───────────────
    env_type, env = await create_env()

    try:
        # ── Run all 3 tasks sequentially ──────────────────────────────
        for i, task_id in enumerate(TASK_IDS):
            global_elapsed = time.monotonic() - global_start
            remaining = TOTAL_TIMEOUT_SECONDS - global_elapsed
            if remaining < 30:
                log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
                log_end(success=False, steps=0, score=0, rewards=[])
                continue

            task_timeout = min(PER_TASK_TIMEOUT_SECONDS, remaining - 10)

            try:
                await run_task(
                    oai_client=oai_client,
                    env_type=env_type,
                    env=env,
                    task_id=task_id,
                    model=MODEL_NAME,
                    task_timeout=task_timeout,
                )
            except Exception as exc:
                print(f"[DEBUG] FATAL ERROR on task {task_id}: {exc}", flush=True)
                log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
                log_end(success=False, steps=0, score=0, rewards=[])

    finally:
        try:
            if env_type == "sdk":
                await env.close()
            else:
                env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
