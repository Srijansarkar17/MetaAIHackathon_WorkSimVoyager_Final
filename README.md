---
title: WorkSimVoyager
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---


# WorkSim Voyager 🚀

**A production-grade OpenEnv workplace-simulation environment for agentic reinforcement learning.**

WorkSim Voyager drops an AI agent into a realistic corporate workspace and challenges it to complete multi-step professional tasks using 5 simulated tools — **mail, slack, drive, calendar, jira**. Every task is scored by deterministic graders returning continuous rewards in **[0.0, 1.0]** with rich reward shaping.

Deployed Link : https://huggingface.co/spaces/srijan1617/MetaAI_WorkSimVoyager

---

## 1. Project Overview

| Feature | Details |
|---|---|
| **Framework** | [OpenEnv](https://github.com/meta-pytorch/OpenEnv) (`openenv-core >= 0.2.3`) |
| **API** | `step()` / `reset()` / `state()` — Gymnasium-style |
| **Tasks** | 6 deterministic tasks (3 original + 3 difficulty-tiered) |
| **Tools** | 5 tools, 30 commands (mail, slack, drive, calendar, jira) |
| **Reward** | Continuous 0.0–1.0 per-step shaping (not sparse) |
| **Simulation** | Fully in-memory, no external APIs |
| **Max steps** | 15–30 per episode |

---

## 2. Task Design

### Task Difficulty Tiers

| # | Task ID | Difficulty | Steps | Tools Used | Description |
|---|---|---|---|---|---|
| 1 | `inbox_triage_001` | 🟢 Easy | ~10 | mail | Classify 8 emails + summarize 2 threads |
| 2 | `meeting_coord_001` | 🟡 Medium | ~15 | mail, slack, drive, calendar | Cross-tool meeting scheduling with agenda |
| 3 | `project_rescue_001` | 🔴 Hard | 15–30 | mail, slack, drive, calendar, jira | Rescue a failing project across all 5 tools |

### Phase 1 Tasks (backward compatible)

| # | Task ID | Type | Description |
|---|---|---|---|
| 4 | `email_draft_001` | Email Draft | Reply to client with root-cause analysis + remediation timeline |
| 5 | `bug_triage_001` | Bug Triage | Triage 3 Jira tickets: severity, priority, assignee, component, labels |
| 6 | `meeting_schedule_001` | Meeting Schedule | Schedule 60-min post-mortem across 3 time zones |

---

### 2.1 Task 1: Inbox Triage (Easy) 🟢

**Scenario**: Monday morning. 8 new emails in inbox — 4 urgent, 4 non-urgent. Includes realistic noise: newsletters, OOO auto-replies.

**Agent must**:
1. Read and **classify all 8 emails** as urgent/non-urgent via `mail/classify_email`
2. **Summarize 2 threads** (`thread-payment-502`, `thread-security-alert`) via `mail/summarize_thread`

**Seed data**:
- 8 emails (payment 502, security alert, deadline change, HR reminder, newsletter, OOO reply, roadmap feedback)
- 3 Slack noise messages (coffee run, Happy Monday, incident follow-up)

**Classification rules** (deterministic):
- **Urgent**: production outages, security incidents, deadline changes, critical/emergency keywords
- **Non-urgent**: newsletters, OOO auto-replies, FYI, "no rush" requests, HR enrollment reminders

**Grader** (3 sub-criteria):
| Criterion | Weight | Detail |
|---|---|---|
| Classification accuracy | 0.60 | 0.075 per correct email (8 emails) |
| Thread summarization | 0.25 | 0.125 per thread summarized (2 threads) |
| Coverage bonus | 0.15 | Fraction of emails classified out of 8 |

---

### 2.2 Task 2: Meeting Coordination (Medium) 🟡

**Scenario**: Schedule a 90-minute cross-functional Design Review for Platform v2.

**Agent must**:
1. Read the request email and Slack messages for context
2. Review the design doc on Drive for agenda items
3. Check calendar availability for 3 attendees across 3 time zones (ET, CT, PT)
4. Find a valid 90-minute slot within April 8-10
5. Create calendar event with title, attendees, agenda, video link
6. Send Slack announcement to #engineering

**Seed data**:
- 3 emails (1 request + 2 noise: newsletter, office closure)
- 5 Slack messages (2 signal + 3 noise: coffee machine, QA freeze, PR fix)
- 2 Drive files (1 design spec + 1 noise: Q1 retro)
- 7 calendar events (blocking various slots for each attendee)

**Constraints**:
- Overlapping working hours: 12:00-16:00 ET = 11:00-15:00 CT = 09:00-13:00 PT
- Multiple blocked calendar slots (agent must check availability)
- Must filter noise emails, Slack messages, and Drive docs

**Grader** (7 sub-criteria):
| Criterion | Weight |
|---|---|
| Required attendees (3) | 0.25 |
| Duration (90 min ± 5) | 0.15 |
| Title (contains "design review") | 0.12 |
| Description/agenda (contains "platform" + "agenda") | 0.12 |
| Location/video link | 0.12 |
| Date range (April 8-10) | 0.12 |
| Slack announcement in #engineering | 0.12 |

---

### 2.3 Task 3: Project Rescue (Hard) 🔴

**Scenario**: "Project Phoenix" — a critical data platform migration — is failing. The deadline is April 15 (hard compliance). The epic has 4 sub-tasks stuck, Slack is chaotic, and the VP needs a status email.

**Agent must** (multi-step reasoning, 15-30 steps):
1. **Gather information** (read 5 Jira tickets, Slack channels, 3 Drive docs — while filtering noise)
2. **Update Jira tickets** (assign owners + severity + priority for 3 sub-tasks)
3. **Send status email** to VP (progress, blockers, assignments, mitigation plan)
4. **Schedule sync meeting** (30 min within April 8-9, 5 attendees)

**Seed data**:
- 3 emails (1 rescue request + 2 noise: elevator maintenance, K8s training)
- 12 Slack messages (6 signal + 6 noise: Star Wars, lunch, all-hands, CI jokes, flaky tests)
- 4 Drive files (runbook, architecture, risk register + 1 noise: offsite planning)
- 5 Jira tickets (1 epic + 4 sub-tasks with dependencies)
- 5 calendar events (various blocks for 5 attendees)

**Expected Jira updates**:
| Ticket | Assignee | Severity | Priority |
|---|---|---|---|
| PHOENIX-102 (ETL rewrite) | bob.kumar@acme.com | major | critical |
| PHOENIX-103 (validation) | david.wright@acme.com | major | high |
| PHOENIX-104 (rollback) | frank.liu@acme.com | blocker | critical |

**Status email requirements**:
- To: vp@acme.com, CC: alice.chen@acme.com
- Subject contains "phoenix" and "status"
- Body covers: migration, blocked, April 15, rollback (min 200 chars)

**Meeting requirements**:
- 30 min, within April 8-9
- Attendees: Alice, Bob, Grace, David, Frank
- Title contains "phoenix", description contains "agenda"
- Video call link in location

**Grader** (4 components, 15+ sub-criteria):
| Component | Weight | Sub-criteria |
|---|---|---|
| Jira updates | 0.30 | 3 tickets × (assignee 0.40, severity 0.30, priority 0.30) |
| Status email | 0.35 | recipient, CC, subject, body keywords, no forbidden text, length, coherence |
| Meeting | 0.20 | attendees, duration, title, description, location, date range |
| Info gathering | 0.15 | ticket coverage, output completeness |

---

## 3. Architecture Overview

```
worksim_voyager/
├── server/
│   ├── env.py                  # WorkSimVoyagerEnvironment (action router + penalties)
│   ├── app.py                  # FastAPI HTTP + WebSocket server
│   ├── models.py               # Pydantic models (Action, Observation, entities)
│   ├── tools/
│   │   └── workspace_tools.py  # 30 commands across 5 tools + validation layer
│   ├── tasks/
│   │   └── task_registry.py    # 6 tasks with seed data across all tools
│   └── graders/
│       └── grader_registry.py  # 6 deterministic graders (0.0–1.0)
├── inference.py                # OpenAI-client agent loop (30 tool defs)
├── openenv.yaml / Dockerfile / pyproject.toml / requirements.txt
└── README.md
```

---

## 4. Tool Simulation

All tools operate on in-memory `WorkspaceState` — no external APIs. Every command mutates state deterministically and returns structured results. Invalid actions are caught by the **action validation layer** and incur graduated penalties.

### 4.1 Mail (8 commands)

| Command | Description | Edge Cases |
|---|---|---|
| `list_inbox` | List all emails in inbox | Empty inbox → empty list |
| `read_email` | Read specific email by ID | Invalid ID → error + hint with available IDs |
| `compose_draft` | Create a draft email | Validates required fields (to, subject, body) |
| `send_email` | Send email or existing draft | Missing draft_id or to/body → structured error |
| `reply` | Reply to inbox email | Original email not found → error + hint |
| `classify_email` | Deterministic classification: category, priority, suggested_action. Tracks calls for grading. | Email not found → error |
| `summarize_thread` | Thread summary: participants, count, timeline, key topics. Tracks calls for grading. | No matching thread → error |
| `send_reply` | Alias for `reply` (semantic name) | Same as `reply` |

### 4.2 Slack (5 commands)

| Command | Description | Edge Cases |
|---|---|---|
| `list_channels` | List all Slack channels | Empty channels → empty list |
| `read_channel` | Read messages from a channel | Channel not found → error + available channels |
| `send_message` | Send a message to a channel | Unknown channel → error; validates channel exists |
| `list_dms` | List direct messages | No DMs → empty list |
| `send_dm` | Send DM to a user | User not in team → error + known team members |

### 4.3 Drive (5 commands)

| Command | Description | Edge Cases |
|---|---|---|
| `list_files` | List all files (seed + created) | Empty drive → empty list with count |
| `read_file` | Read a specific file by ID | File not found → error + available file IDs |
| `create_file` | Create a new file | Duplicate filename → error + hint to use edit |
| `edit_file` | Edit file content | File not found → error |
| `search_files` | Search by name/content | Empty query → error; no results → empty list |

### 4.4 Calendar (5 commands)

| Command | Description | Edge Cases |
|---|---|---|
| `list_events` | List all events (seed + scheduled) | Empty calendar → empty list |
| `check_availability` | Check attendee availability on date | Unknown member → `available: false`; no emails → error |
| `schedule_meeting` | Schedule with conflict detection | Invalid ISO time → error; end ≤ start → error; double-booking → warning |
| `create_event` | Alias for `schedule_meeting` | Same as `schedule_meeting` |
| `get_team_roster` | Team roster with timezones | Empty team → empty list |

### 4.5 Jira (7 commands)

| Command | Description | Edge Cases |
|---|---|---|
| `list_tickets` | List all tickets | Empty board → empty list |
| `get_ticket` | Full ticket details | Invalid ID → error + available IDs |
| `read_ticket` | Alias for `get_ticket` | Same as `get_ticket` |
| `update_ticket` | Update fields (severity, priority, assignee, component, labels, status) | Invalid enum value → error + valid values list |
| `create_ticket` | Create a new ticket | Invalid severity/priority → error + valid values |
| `add_comment` | Add comment to ticket | Ticket not found → error |
| `assign_task` | Assign ticket to team member | Assignee not in team → error + valid assignees |

### 4.6 Action Validation Layer

Every action passes through a 4-stage validation pipeline before execution:

1. **Tool validation** — Is the tool name valid? (`mail`, `slack`, `drive`, `calendar`, `jira`)
2. **Command validation** — Is the command valid for this tool?
3. **Input schema validation** — Are required fields present? Correct types? Non-empty?
4. **Execution** — Handler runs on `WorkspaceState`; catches unexpected errors

### 4.7 Penalty Schedule (Phase 5)

| Error Type | Penalty | Description |
|---|---|---|
| Wrong tool/command | −0.10 | Unknown tool or command |
| Repeated useless action | −0.10 | Exact duplicate action with no state change |
| Destructive action | −0.20 | Overwriting file with empty content |
| Schema validation failure | −0.05 | Missing required field or wrong type |
| Execution error (first) | −0.03 | Handler-level error (not-found, invalid value) |
| Repeated error | −0.10 | Same error signature repeated → escalated penalty |

---

## 5. Grading System

All graders are **deterministic** (no randomness), return a **float in [0.0, 1.0]**, and reflect real agent performance. Grader outputs vary with each action — they never return the same value for different workspace states.

### 5.1 Reward Shaping

Rewards are **not sparse**. Step rewards are **incremental**:

```
reward_t = max(0, score_t − score_{t−1}) + penalty
```

Each grader decomposes scoring into weighted sub-criteria. The full component breakdown is available in `info["grader_breakdown"]` after every `step()` and in `state()`.

### 5.2 Easy: Inbox Triage

**Formula**: `accuracy = correct_classifications / total`

| Component | Weight | Detail |
|---|---|---|
| Classification accuracy | 0.60 | `correct / 8` — each classify_email call is checked |
| Thread summarization | 0.25 | `threads_summarized / 2` |
| Coverage bonus | 0.15 | Fraction of emails classified out of 8 |

**Breakdown keys**: `classification_accuracy`, `correct_count`, `classified_count`, `per_email`, `thread_summarization`, `threads_summarized`, `coverage`

### 5.3 Medium: Meeting Coordination

| Component | Weight | Sub-criteria |
|---|---|---|
| **Slot validity** | **0.30** | date_in_range (0.40), duration_correct (0.40), no_conflicts (0.20) |
| **Event creation** | **0.30** | attendees (0.50), title (0.25), location (0.25) |
| **Agenda completeness** | **0.40** | description_keywords (0.70), slack_announcement (0.30) |

**Breakdown keys**: `slot_validity.{score,date_in_range,duration_correct,no_conflicts}`, `event_creation.{score,attendees,title,location}`, `agenda_completeness.{score,description_keywords,slack_announcement}`

### 5.4 Hard: Project Rescue

| Component | Weight | Sub-criteria |
|---|---|---|
| **Task breakdown** | **0.30** | tickets_read (0.35), tickets_updated (0.35), outputs_produced (0.30) |
| **Correct assignments** | **0.20** | per-ticket: assignee (0.40), severity (0.30), priority (0.30) |
| **Email quality** | **0.30** | recipient (0.12), CC (0.08), subject (0.10), body keywords (0.30), no_forbidden (0.10), length (0.10), coherence (0.20) |
| **Meeting scheduling** | **0.20** | attendees (0.30), duration (0.15), title (0.20), description (0.15), location (0.10), date_range (0.10) |

**Breakdown keys**: `task_breakdown.{score,tickets_read,tickets_updated,outputs_produced}`, `correct_assignments.{score,per_ticket}`, `email_quality.{score,recipient,cc,...}`, `meeting_scheduling.{score,attendees,...}`

### 5.5 Grader Output in info Dict

Every `step()` response includes the full grader breakdown:

```python
result = env.step(action)
breakdown = result["info"]["grader_breakdown"]

# Easy task example:
# breakdown = {
#   "classification_accuracy": 0.625,
#   "correct_count": 5,
#   "classified_count": 5,
#   "total_emails": 8,
#   "per_email": {"it-e01": {"classified": True, "correct": True, ...}, ...},
#   "thread_summarization": 0.5,
#   "coverage": 0.625
# }

# Hard task example:
# breakdown = {
#   "task_breakdown": {"score": 0.66, "tickets_updated": 3, ...},
#   "correct_assignments": {"score": 1.0, "per_ticket": {...}},
#   "email_quality": {"score": 0.92, "body_keywords": 1.0, ...},
#   "meeting_scheduling": {"score": 0.85, "attendees": 1.0, ...}
# }
```

`state()` also includes `grader_breakdown` for final episode reporting.

### 5.6 Guarantees

- **Deterministic**: Same actions → same score. No randomness.
- **Range**: Always `[0.0, 1.0]`
- **Initial**: All tasks score `0.0` on fresh workspace (no free credit)
- **Monotonic progress**: Agent score only increases with correct actions
- **Varying output**: Graders produce different values at each step — never static
- **No penalty leakage**: Penalties are additive to reward, never affect grader score

---

## 6. Reward Design (Phase 5)

The reward function provides **per-step, continuous feedback** — not binary. Every `step()` decomposes reward into three additive components:

```
step_reward = clamp(grader_delta + action_bonus + penalty, −0.20, +0.35)
```

### 6.1 Action-Category Bonuses

Bonuses reward the agent for taking the **right kind** of action. Each bonus is scaled by grader improvement and deduplicated by action fingerprint (anti-hacking).

| Action Category | Bonus | Applies to |
|---|---|---|
| Correct classification | **+0.20** | `classify_email`, `summarize_thread` |
| Scheduling success | **+0.30** | `schedule_meeting`, `create_event`, `check_availability` |
| Task breakdown | **+0.30** | `update_ticket`, `assign_task`, `create_ticket`, `add_comment` |
| Email drafting | **+0.20** | `send_email`, `reply`, `compose_draft`, `send_reply` |
| Read-only actions | 0.00 | `list_inbox`, `read_email`, `read_channel`, etc. |

**Scaling**: `bonus × min(1.0, grader_delta / 0.10)` — small improvements get proportionally smaller bonuses.

### 6.2 Penalty Schedule

| Error Type | Penalty | Trigger |
|---|---|---|
| Wrong tool/command | **−0.10** | Unknown tool or command |
| Repeated useless action | **−0.10** | Exact same (tool, command, input) repeated |
| Destructive action | **−0.20** | Overwriting file with empty content |
| Validation error | −0.05 | Missing required field, wrong type |
| Execution error | −0.03 | Handler error (not-found, invalid value) |

### 6.3 Anti-Hacking Measures

| Measure | How It Works |
|---|---|
| **Action fingerprinting** | MD5 hash of (tool, command, input) detects duplicates |
| **One-time bonus** | Each unique action fingerprint gets bonus AT MOST ONCE |
| **Grader-gated bonus** | Bonus only awarded if `grader_delta > 0` (action must help) |
| **Per-step cap** | `[−0.20, +0.35]` — no single step can award excessive reward |
| **Duplicate penalty** | Repeating exact same action → −0.10 instead of bonus |

### 6.4 Reward Breakdown in info Dict

Every `step()` response includes `info["reward_breakdown"]`:

```python
result = env.step(action)
rb = result["info"]["reward_breakdown"]
# {
#   "grader_delta": 0.0938,      # Score improvement from this action
#   "action_bonus": 0.1876,      # Category bonus (scaled)
#   "penalty": 0.0,              # Penalty applied
#   "raw_reward": 0.2814,        # Before cap
#   "capped_reward": 0.2814,     # After cap (same here, not capped)
#   "grader_score": 0.0938,      # Current total grader score
#   "action_category": "classification",
#   "is_duplicate": false,
#   "was_capped": false
# }
```

`state()` includes `reward_trace` — the full reward breakdown for every step in the episode.

---

## 7. Baseline Results

### Inference Configuration

| Setting | Value |
|---|---|
| **Script** | `inference.py` |
| **LLM Client** | OpenAI Python SDK (compatible with HF Inference API) |
| **Env Vars** | `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` |
| **Tasks** | 3 (inbox_triage_001, meeting_coord_001, project_rescue_001) |
| **Max Steps** | 40 per task |
| **Temperature** | 0.0 (deterministic) |
| **Timeout** | 6 min/task, 20 min total |
| **Resource Target** | 2 vCPU, 8 GB RAM |

### Running Inference

```bash
# Set required environment variables
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct"
export HF_TOKEN="hf_your_token_here"

# Optional: override the environment server URL
export ENV_BASE_URL="https://aditya9981-meta-hackthon-worksim-voyager.hf.space"

# Run inference
python inference.py
```

### Expected Output

The inference script prints per-task scores and a summary table:

```
  Task ID                     Score   Steps   Errors   Time (s)   Done
  ───────────────────────── ──────── ─────── ──────── ────────── ──────
  inbox_triage_001            0.XXXX      NN       NN       NN.N      ✓
  meeting_coord_001           0.XXXX      NN       NN       NN.N      ✓
  project_rescue_001          0.XXXX      NN       NN       NN.N      ✓
  ───────────────────────── ──────── ─────── ──────── ────────── ──────
  AVERAGE                     0.XXXX
  TOTAL                       X.XXXX
```

### Score Interpretation

| Range | Meaning |
|---|---|
| 0.00–0.20 | Agent barely started — likely not reading context |
| 0.20–0.50 | Partial completion — some correct actions but missing key steps |
| 0.50–0.75 | Good performance — most sub-criteria met |
| 0.75–0.90 | Strong performance — nearly all actions correct |
| 0.90–1.00 | Near-perfect — all grader criteria satisfied |



## 8. Deployment Instructions

### 8.1 Local Development

```bash
cd worksim_voyager
pip install -e ".[inference,dev]"

# Start server (choose one)
python -m server
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/health
# → {"status": "healthy"}

curl -X POST http://localhost:8000/reset \
  -H 'Content-Type: application/json' \
  -d '{"task_id": "inbox_triage_001"}'
# → {observation, reward: 0.0, done: false, info: {...}}
```

### 8.2 Docker Build & Run

```bash
# Build the image (multi-stage, ~850MB final)
docker build -t worksim-voyager:latest .

# Run the container
docker run -p 8000:8000 worksim-voyager:latest

# Verify
curl http://localhost:8000/health
curl -X POST http://localhost:8000/reset \
  -H 'Content-Type: application/json' \
  -d '{"task_id": "inbox_triage_001"}'
```

**Image details:**

| Property | Value |
|---|---|
| Base | `python:3.11-slim` (multi-stage) |
| Size | ~850 MB |
| User | Non-root (`appuser`, UID 1000) |
| Port | 8000 |
| Workers | 1 (optimized for 2 vCPU) |
| Health check | `GET /health` every 30s |

### 8.3 HuggingFace Spaces Deployment

#### Option A: Using `openenv push` (recommended)

```bash
# Install OpenEnv CLI
pip install openenv-core

# Login to HuggingFace
huggingface-cli login

# Push to HF Spaces (from the worksim_voyager directory)
openenv push

# Or specify a custom repo
openenv push --repo-id your-username/worksim-voyager --private
```

The `openenv push` command reads `openenv.yaml`, validates the environment, builds the Docker image, and uploads it to HuggingFace Spaces.

#### Option B: Manual HF Spaces setup

1. Create a new Space on [huggingface.co/new-space](https://huggingface.co/new-space)
   - Select **Docker** as the SDK
   - Choose **Blank** template

2. Clone and push your code:

```bash
git clone https://huggingface.co/spaces/your-username/worksim-voyager
cp -r worksim_voyager/* worksim-voyager/
cd worksim-voyager
git add .
git commit -m "Deploy WorkSim Voyager"
git push
```

3. The Space will auto-build from the Dockerfile and start serving on port 8000.

### 8.4 Run Inference Against Deployed Space

```bash
# Set environment variables
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct"
export HF_TOKEN="hf_your_token_here"

# Point to your deployed Space
export ENV_BASE_URL="https://your-username-worksim-voyager.hf.space"

# Run inference
python inference.py
```

### 8.5 OpenEnv Configuration

The `openenv.yaml` defines the environment contract:

```yaml
spec_version: 1
name: worksim_voyager
type: space
runtime: fastapi
app: server.app:app
port: 7860
```

| Field | Description |
|---|---|
| `spec_version` | OpenEnv spec version (1) |
| `name` | Environment identifier |
| `type` | Deployment type (`space` = HF Spaces) |
| `runtime` | Server framework (`fastapi`) |
| `app` | ASGI app path for uvicorn |
| `port` | Exposed HTTP port |

---

## 9. Environment API (HTTP Endpoints)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check → `{"status": "healthy"}` |
| POST | `/reset` | Reset env → `{observation, reward, done, info}` |
| POST | `/step` | Execute action → `{observation, reward, done, info}` |
| GET | `/state` | Episode metadata → `{episode_id, step_count, done, ...}` |
| GET | `/schema` | Action/Observation JSON schemas |
| WS | `/ws` | WebSocket interface (per-session env) |

---



### Reproduction

```bash
# Run the full validation suite locally
python validate_all.py

# Expected output:
#   PASSED: 123
#   FAILED: 0
#   🎉 ALL CHECKS PASSED! Environment is ready for submission.
```

---

## License

apache-2.0
