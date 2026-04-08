# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
Deterministic graders — continuous 0.0–1.0 with meaningful reward shaping.

Phase 4: graders return BOTH a scalar score AND a component breakdown dict,
enabling full introspection of partial credit via the info dict.

Weight specifications:
  Easy  (inbox_triage):        accuracy = correct / total
  Medium (meeting_coord):      slot_validity 0.30, event_creation 0.30, agenda 0.40
  Hard  (project_rescue):      task_breakdown 0.30, assignments 0.20, email 0.30, meeting 0.20

Phase 1 graders preserved for backward compatibility.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple
from server.models import TaskSpec, TaskType, WorkspaceState


# ═══════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def _ci(haystack: str, needle: str) -> bool:
    """Case-insensitive substring check."""
    return needle.lower() in haystack.lower()


def _overlap(actual: List[str], expected: List[str]) -> float:
    """Fraction of expected items found (case-insensitive) in actual."""
    if not expected:
        return 1.0
    lo = {a.lower() for a in actual}
    return sum(1 for e in expected if e.lower() in lo) / len(expected)


def _kw_score(text: str, keywords: List[str]) -> float:
    """Fraction of keywords found (case-insensitive) in text."""
    if not keywords:
        return 1.0
    return sum(_ci(text, k) for k in keywords) / len(keywords)


# ═══════════════════════════════════════════════════════════════════════
#  Phase 1 — Email Draft grader (7 sub-criteria)
# ═══════════════════════════════════════════════════════════════════════

def _grade_email_draft(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    exp = spec.expected_outcomes
    emails = ws.sent_emails or ws.drafts
    breakdown: Dict[str, Any] = {
        "recipients": 0.0, "cc": 0.0, "subject_keywords": 0.0,
        "body_keywords": 0.0, "no_forbidden": 0.0, "body_length": 0.0,
        "coherence": 0.0,
    }
    if not emails:
        return 0.0, breakdown
    em = emails[-1]

    # 1. Recipients (0.15)
    breakdown["recipients"] = round(_overlap(em.recipients, exp.get("to", [])), 4)

    # 2. CC (0.10)
    breakdown["cc"] = round(_overlap(em.cc, exp.get("cc", [])), 4)

    # 3. Subject keywords (0.10)
    kw = exp.get("subject_must_contain", [])
    breakdown["subject_keywords"] = round(_kw_score(em.subject, kw), 4)

    # 4. Body keywords (0.25)
    bk = exp.get("body_must_contain", [])
    breakdown["body_keywords"] = round(_kw_score(em.body, bk), 4)

    # 5. No forbidden text (0.10)
    fb = exp.get("body_forbidden", [])
    breakdown["no_forbidden"] = round(
        max(0, 1 - sum(_ci(em.body, f) for f in fb) / max(len(fb), 1)) if fb else 1.0, 4)

    # 6. Body length (0.15)
    mn, mx = exp.get("min_body_length", 0), exp.get("max_body_length", 10000)
    bl = len(em.body)
    if mn <= bl <= mx:
        breakdown["body_length"] = 1.0
    elif bl < mn:
        breakdown["body_length"] = round(bl / mn if mn else 0, 4)
    else:
        breakdown["body_length"] = round(max(0, 1 - (bl - mx) / mx), 4)

    # 7. Coherence (0.15)
    co = 0.0
    sents = [x.strip() for x in em.body.replace("\n", " ").split(".") if x.strip()]
    if len(sents) >= 3:
        co += 0.5
    if any(_ci(em.body[:60], g) for g in ["hi ", "hello", "dear"]):
        co += 0.25
    if any(_ci(em.body[-120:], g) for g in ["thanks", "regards", "best", "sincerely"]):
        co += 0.25
    breakdown["coherence"] = round(co, 4)

    s = (0.15 * breakdown["recipients"] + 0.10 * breakdown["cc"] +
         0.10 * breakdown["subject_keywords"] + 0.25 * breakdown["body_keywords"] +
         0.10 * breakdown["no_forbidden"] + 0.15 * breakdown["body_length"] +
         0.15 * breakdown["coherence"])

    score = round(min(1.0, max(0.0, s)), 4)
    return score, breakdown


# ═══════════════════════════════════════════════════════════════════════
#  Phase 1 — Bug / Jira Triage grader (5 sub-criteria per ticket)
# ═══════════════════════════════════════════════════════════════════════

def _grade_bug_triage(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    exp = spec.expected_outcomes
    breakdown: Dict[str, Any] = {"ticket_scores": {}, "average": 0.0}
    if not exp:
        return 0.0, breakdown
    triaged = {t.id: t for t in ws.jira_tickets if t.severity is not None}
    ta_map: Dict[str, Dict] = {}
    for a in ws.triage_actions:
        bid = a.get("bug_id")
        if bid:
            ta_map[bid] = a
    ids = list(exp.keys())
    if not ids:
        return 1.0, breakdown
    scores = []
    for bid in ids:
        e = exp[bid]
        bs = 0.0
        t = triaged.get(bid)
        ta = ta_map.get(bid, {})
        td: Dict[str, Any] = {"severity": 0.0, "priority": 0.0, "assignee": 0.0,
                               "component": 0.0, "labels": 0.0}
        if t is None and not ta:
            breakdown["ticket_scores"][bid] = td
            scores.append(0.0)
            continue
        sev = (t.severity.value if t and t.severity else ta.get("severity", ""))
        if sev == e.get("severity"):
            td["severity"] = 1.0
            bs += 0.25
        pri = (t.priority.value if t and t.priority else ta.get("priority", ""))
        if pri == e.get("priority"):
            td["priority"] = 1.0
            bs += 0.25
        asgn = (t.assigned_to if t else ta.get("assigned_to", "")) or ""
        if asgn.lower() == (e.get("assigned_to", "")).lower():
            td["assignee"] = 1.0
            bs += 0.25
        comp = (t.component if t else ta.get("component", "")) or ""
        if comp.lower() == (e.get("component", "")).lower():
            td["component"] = 1.0
            bs += 0.15
        labs = (t.labels if t else ta.get("labels", []))
        lab_s = _overlap(labs, e.get("labels", []))
        td["labels"] = round(lab_s, 4)
        bs += 0.10 * lab_s
        breakdown["ticket_scores"][bid] = td
        scores.append(bs)
    avg = sum(scores) / len(scores)
    breakdown["average"] = round(avg, 4)
    return round(avg, 4), breakdown


# ═══════════════════════════════════════════════════════════════════════
#  Phase 1 — Meeting Schedule grader (6 sub-criteria)
# ═══════════════════════════════════════════════════════════════════════

def _grade_meeting_schedule(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    exp = spec.expected_outcomes
    breakdown: Dict[str, Any] = {
        "attendees": 0.0, "duration": 0.0, "title": 0.0,
        "description": 0.0, "location": 0.0, "date_range": 0.0,
    }
    mtgs = ws.scheduled_meetings
    if not mtgs:
        return 0.0, breakdown
    m = mtgs[-1]

    breakdown["attendees"] = round(_overlap(m.attendees, exp.get("required_attendees", [])), 4)

    try:
        from datetime import datetime
        st = datetime.fromisoformat(m.start_time)
        et = datetime.fromisoformat(m.end_time)
        dur = (et - st).total_seconds() / 60
        ed = exp.get("duration_minutes", 60)
        if abs(dur - ed) <= 5:
            breakdown["duration"] = 1.0
        elif abs(dur - ed) <= 15:
            breakdown["duration"] = 0.5
    except Exception:
        pass

    tk = exp.get("title_must_contain", [])
    breakdown["title"] = round(_kw_score(m.title, tk), 4)

    dk = exp.get("description_must_contain", [])
    if dk and m.description:
        breakdown["description"] = round(_kw_score(m.description, dk), 4)
    elif not dk:
        breakdown["description"] = 1.0

    if exp.get("must_have_location") and m.location:
        breakdown["location"] = 1.0

    try:
        from datetime import date, datetime as dt
        sd = dt.fromisoformat(m.start_time).date()
        rs = date.fromisoformat(exp.get("valid_date_range_start", "2000-01-01"))
        re_ = date.fromisoformat(exp.get("valid_date_range_end", "2099-12-31"))
        if rs <= sd <= re_:
            breakdown["date_range"] = 1.0
    except Exception:
        pass

    s = (0.25 * breakdown["attendees"] + 0.15 * breakdown["duration"] +
         0.15 * breakdown["title"] + 0.15 * breakdown["description"] +
         0.15 * breakdown["location"] + 0.15 * breakdown["date_range"])

    score = round(min(1.0, max(0.0, s)), 4)
    return score, breakdown


# ═══════════════════════════════════════════════════════════════════════
#  Phase 3/4 — INBOX TRIAGE grader (Easy)
# ═══════════════════════════════════════════════════════════════════════
#
#  accuracy = correct_classifications / total
#
#  The score IS the classification accuracy — clean, deterministic,
#  varies with each classify_email call.  Thread summarization and
#  coverage are bonus multipliers on top of accuracy.
# ─────────────────────────────────────────────────────────────────────

_URGENT_CATEGORIES = {"urgent", "critical", "bug_report", "client_escalation"}


def _grade_inbox_triage(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    exp = spec.expected_outcomes
    expected_cls = exp.get("classifications", {})
    expected_threads = set(exp.get("threads_summarized", []))
    min_cls = exp.get("min_classifications", 8)
    total_emails = len(expected_cls)

    breakdown: Dict[str, Any] = {
        "classification_accuracy": 0.0,
        "correct_count": 0,
        "classified_count": 0,
        "total_emails": total_emails,
        "per_email": {},
        "thread_summarization": 0.0,
        "threads_summarized": [],
        "coverage": 0.0,
    }

    # ── 1. Classification accuracy ───────────────────────────────────
    # Core formula: accuracy = correct_classifications / total
    classified_emails = getattr(ws, "email_classifications", {})
    correct = 0
    if isinstance(classified_emails, dict):
        breakdown["classified_count"] = len(classified_emails)
        for eid, expected_urgency in expected_cls.items():
            per: Dict[str, Any] = {"classified": False, "correct": False,
                                    "expected": expected_urgency}
            if eid in classified_emails:
                per["classified"] = True
                agent_category = classified_emails[eid].get("category", "")
                per["agent_category"] = agent_category
                if expected_urgency == "urgent" and agent_category in _URGENT_CATEGORIES:
                    correct += 1
                    per["correct"] = True
                elif expected_urgency == "non-urgent" and agent_category not in _URGENT_CATEGORIES:
                    correct += 1
                    per["correct"] = True
            breakdown["per_email"][eid] = per

    breakdown["correct_count"] = correct
    accuracy = correct / total_emails if total_emails > 0 else 0.0
    breakdown["classification_accuracy"] = round(accuracy, 4)

    # ── 2. Thread summarization ──────────────────────────────────────
    summarized_threads = getattr(ws, "thread_summaries", {})
    threads_found: List[str] = []
    if isinstance(summarized_threads, dict):
        threads_found = [t for t in expected_threads if t in summarized_threads]
    elif isinstance(summarized_threads, set):
        threads_found = [t for t in expected_threads if t in summarized_threads]
    thread_score = len(threads_found) / len(expected_threads) if expected_threads else 1.0
    breakdown["thread_summarization"] = round(thread_score, 4)
    breakdown["threads_summarized"] = threads_found

    # ── 3. Coverage ──────────────────────────────────────────────────
    classified_count = len(classified_emails) if isinstance(classified_emails, dict) else 0
    coverage = min(1.0, classified_count / min_cls) if min_cls > 0 else 1.0
    breakdown["coverage"] = round(coverage, 4)

    # ── Combined score ───────────────────────────────────────────────
    # Primary: accuracy (0.60), thread summary (0.25), coverage (0.15)
    s = 0.60 * accuracy + 0.25 * thread_score + 0.15 * coverage

    score = round(min(1.0, max(0.0, s)), 4)
    return score, breakdown


# ═══════════════════════════════════════════════════════════════════════
#  Phase 3/4 — MEETING COORDINATION grader (Medium)
# ═══════════════════════════════════════════════════════════════════════
#
#  Phase 4 weights:
#    slot_validity   → 0.30  (date range, no conflicts, correct duration)
#    event_creation  → 0.30  (attendees, title, location)
#    agenda          → 0.40  (description keywords, contextual references, slack)
# ─────────────────────────────────────────────────────────────────────

def _grade_meeting_coordination(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    exp = spec.expected_outcomes
    mtgs = ws.scheduled_meetings

    breakdown: Dict[str, Any] = {
        "slot_validity": {
            "score": 0.0,
            "date_in_range": 0.0,
            "duration_correct": 0.0,
            "no_conflicts": 0.0,
        },
        "event_creation": {
            "score": 0.0,
            "attendees": 0.0,
            "title": 0.0,
            "location": 0.0,
        },
        "agenda_completeness": {
            "score": 0.0,
            "description_keywords": 0.0,
            "slack_announcement": 0.0,
        },
    }

    slot_score = 0.0
    event_score = 0.0
    agenda_score = 0.0

    if mtgs:
        m = mtgs[-1]

        # ── Slot Validity (0.30) ─────────────────────────────────────
        # Date range check (0.40 of slot)
        try:
            from datetime import date, datetime
            sd = datetime.fromisoformat(m.start_time).date()
            rs = date.fromisoformat(exp.get("valid_date_range_start", "2000-01-01"))
            re_ = date.fromisoformat(exp.get("valid_date_range_end", "2099-12-31"))
            if rs <= sd <= re_:
                breakdown["slot_validity"]["date_in_range"] = 1.0
        except Exception:
            pass

        # Duration check (0.40 of slot)
        try:
            from datetime import datetime as dt2
            st_dt = dt2.fromisoformat(m.start_time)
            et_dt = dt2.fromisoformat(m.end_time)
            dur = (et_dt - st_dt).total_seconds() / 60
            target = exp.get("duration_minutes", 90)
            if abs(dur - target) <= 5:
                breakdown["slot_validity"]["duration_correct"] = 1.0
            elif abs(dur - target) <= 15:
                breakdown["slot_validity"]["duration_correct"] = 0.5
            elif abs(dur - target) <= 30:
                breakdown["slot_validity"]["duration_correct"] = 0.25
        except Exception:
            pass

        # No-conflict heuristic: meeting exists = 1.0 (conflict detection already
        # in scheduler, agent would have seen warnings)
        breakdown["slot_validity"]["no_conflicts"] = 1.0

        slot_score = (0.40 * breakdown["slot_validity"]["date_in_range"] +
                      0.40 * breakdown["slot_validity"]["duration_correct"] +
                      0.20 * breakdown["slot_validity"]["no_conflicts"])
        breakdown["slot_validity"]["score"] = round(slot_score, 4)

        # ── Event Creation (0.30) ────────────────────────────────────
        # Attendees (0.50 of event)
        att_score = _overlap(m.attendees, exp.get("required_attendees", []))
        breakdown["event_creation"]["attendees"] = round(att_score, 4)

        # Title (0.25 of event)
        tk = exp.get("title_must_contain", [])
        title_score = _kw_score(m.title, tk)
        breakdown["event_creation"]["title"] = round(title_score, 4)

        # Location (0.25 of event)
        loc_score = 1.0 if (exp.get("must_have_location") and m.location) else 0.0
        breakdown["event_creation"]["location"] = loc_score

        event_score = (0.50 * att_score + 0.25 * title_score + 0.25 * loc_score)
        breakdown["event_creation"]["score"] = round(event_score, 4)

        # ── Agenda Completeness (0.40) ───────────────────────────────
        # Description keywords (0.70 of agenda)
        dk = exp.get("description_must_contain", [])
        if dk and m.description:
            desc_score = _kw_score(m.description, dk)
        elif not dk:
            desc_score = 1.0
        else:
            desc_score = 0.0
        breakdown["agenda_completeness"]["description_keywords"] = round(desc_score, 4)

        # Slack announcement (0.30 of agenda)
        slack_score = 0.0
        target_channel = exp.get("slack_channel", "engineering")
        slack_kw = exp.get("slack_must_contain", [])
        for msg in ws.sent_slack:
            if msg.channel == target_channel:
                if not slack_kw or _kw_score(msg.text, slack_kw) > 0.5:
                    slack_score = 1.0
                    break
        breakdown["agenda_completeness"]["slack_announcement"] = slack_score

        agenda_score = 0.70 * desc_score + 0.30 * slack_score
        breakdown["agenda_completeness"]["score"] = round(agenda_score, 4)

    # ── Combined: slot 0.30 + event 0.30 + agenda 0.40 ──────────────
    s = 0.30 * slot_score + 0.30 * event_score + 0.40 * agenda_score

    score = round(min(1.0, max(0.0, s)), 4)
    return score, breakdown


# ═══════════════════════════════════════════════════════════════════════
#  Phase 3/4 — PROJECT RESCUE grader (Hard)
# ═══════════════════════════════════════════════════════════════════════
#
#  Phase 4 weights:
#    task_breakdown       → 0.30  (reading tickets/docs, updating tickets)
#    correct_assignments  → 0.20  (assignee, severity, priority for 3 tickets)
#    email_quality        → 0.30  (VP status email: to, cc, subject, body, structure)
#    meeting_scheduling   → 0.20  (attendees, duration, title, agenda, location, dates)
# ─────────────────────────────────────────────────────────────────────

def _grade_project_rescue(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    exp = spec.expected_outcomes

    breakdown: Dict[str, Any] = {
        "task_breakdown": {
            "score": 0.0,
            "tickets_read": 0,
            "tickets_updated": 0,
            "docs_context": 0.0,
            "outputs_produced": 0,
        },
        "correct_assignments": {
            "score": 0.0,
            "per_ticket": {},
        },
        "email_quality": {
            "score": 0.0,
            "recipient": 0.0,
            "cc": 0.0,
            "subject_keywords": 0.0,
            "body_keywords": 0.0,
            "no_forbidden": 0.0,
            "min_length": 0.0,
            "coherence": 0.0,
        },
        "meeting_scheduling": {
            "score": 0.0,
            "attendees": 0.0,
            "duration": 0.0,
            "title": 0.0,
            "description": 0.0,
            "location": 0.0,
            "date_range": 0.0,
        },
    }

    # ── 1. TASK BREAKDOWN (0.30) ─────────────────────────────────────
    # Measures: did agent gather info + break the problem into actionable pieces?
    tb_score = 0.0

    # 1a. Tickets interacted with (0.35 of task_breakdown)
    tickets_interacted = set()
    for a in ws.triage_actions:
        if a.get("bug_id"):
            tickets_interacted.add(a["bug_id"])
    for c in ws.jira_comments:
        if c.get("ticket_id"):
            tickets_interacted.add(c["ticket_id"])
    phoenix_tickets = {"PHOENIX-100", "PHOENIX-101", "PHOENIX-102", "PHOENIX-103", "PHOENIX-104"}
    ticket_coverage = len(tickets_interacted & phoenix_tickets) / len(phoenix_tickets)
    breakdown["task_breakdown"]["tickets_read"] = len(tickets_interacted & phoenix_tickets)
    tb_score += 0.35 * ticket_coverage

    # 1b. Tickets actually updated (0.35 of task_breakdown)
    jira_exp = exp.get("jira_updates", {})
    tickets_updated = 0
    ticket_map = {t.id: t for t in ws.jira_tickets}
    for tid in jira_exp:
        t = ticket_map.get(tid)
        if t and (t.assigned_to or t.severity):
            tickets_updated += 1
    update_coverage = tickets_updated / len(jira_exp) if jira_exp else 0.0
    breakdown["task_breakdown"]["tickets_updated"] = tickets_updated
    tb_score += 0.35 * update_coverage

    # 1c. Outputs produced (0.30 of task_breakdown)
    outputs = 0
    if ws.sent_emails:
        outputs += 1
    if ws.scheduled_meetings:
        outputs += 1
    if tickets_updated > 0:
        outputs += 1
    breakdown["task_breakdown"]["outputs_produced"] = outputs
    tb_score += 0.30 * min(1.0, outputs / 3)

    breakdown["task_breakdown"]["score"] = round(tb_score, 4)

    # ── 2. CORRECT ASSIGNMENTS (0.20) ────────────────────────────────
    # Strict field matching for each ticket
    assign_score = 0.0
    if jira_exp:
        ticket_scores = []
        for tid, expected in jira_exp.items():
            t = ticket_map.get(tid)
            ta_entry = {}
            for a in ws.triage_actions:
                if a.get("bug_id") == tid:
                    ta_entry = a
            ts: Dict[str, Any] = {"assignee": 0.0, "severity": 0.0, "priority": 0.0}
            if t is None and not ta_entry:
                breakdown["correct_assignments"]["per_ticket"][tid] = ts
                ticket_scores.append(0.0)
                continue

            # Assignee (0.40 of ticket)
            actual_assignee = (t.assigned_to if t else ta_entry.get("assigned_to", "")) or ""
            if actual_assignee.lower() == expected.get("assigned_to", "").lower():
                ts["assignee"] = 1.0

            # Severity (0.30 of ticket)
            actual_sev = (t.severity.value if t and t.severity else ta_entry.get("severity", ""))
            if actual_sev == expected.get("severity"):
                ts["severity"] = 1.0

            # Priority (0.30 of ticket)
            actual_pri = (t.priority.value if t and t.priority else ta_entry.get("priority", ""))
            if actual_pri == expected.get("priority"):
                ts["priority"] = 1.0

            breakdown["correct_assignments"]["per_ticket"][tid] = ts
            ticket_scores.append(0.40 * ts["assignee"] + 0.30 * ts["severity"] + 0.30 * ts["priority"])

        assign_score = sum(ticket_scores) / len(ticket_scores) if ticket_scores else 0.0

    breakdown["correct_assignments"]["score"] = round(assign_score, 4)

    # ── 3. EMAIL QUALITY (0.30) ──────────────────────────────────────
    email_score = 0.0
    status_emails = [e for e in ws.sent_emails
                     if any(r.lower() == "vp@acme.com" for r in e.recipients)]
    if status_emails:
        em = status_emails[-1]

        # 3a. Correct recipient (0.12)
        r_score = 1.0 if _overlap(em.recipients, exp.get("email_to", [])) >= 1.0 else 0.0
        breakdown["email_quality"]["recipient"] = r_score

        # 3b. CC (0.08)
        cc_score = 1.0 if _overlap(em.cc, exp.get("email_cc", [])) >= 1.0 else 0.0
        breakdown["email_quality"]["cc"] = cc_score

        # 3c. Subject keywords (0.10)
        subj_kw = exp.get("email_subject_must_contain", [])
        subj_score = _kw_score(em.subject, subj_kw)
        breakdown["email_quality"]["subject_keywords"] = round(subj_score, 4)

        # 3d. Body keywords (0.30)
        body_kw = exp.get("email_body_must_contain", [])
        body_score = _kw_score(em.body, body_kw)
        breakdown["email_quality"]["body_keywords"] = round(body_score, 4)

        # 3e. No forbidden text (0.10)
        fb = exp.get("email_body_forbidden", [])
        if fb:
            violations = sum(_ci(em.body, f) for f in fb)
            nf_score = max(0, 1 - violations / len(fb))
        else:
            nf_score = 1.0
        breakdown["email_quality"]["no_forbidden"] = round(nf_score, 4)

        # 3f. Minimum length (0.10)
        min_len = exp.get("email_min_length", 200)
        bl = len(em.body)
        ml_score = 1.0 if bl >= min_len else (bl / min_len if min_len > 0 else 1.0)
        breakdown["email_quality"]["min_length"] = round(ml_score, 4)

        # 3g. Coherence (0.20)
        co = 0.0
        sents = [x.strip() for x in em.body.replace("\n", " ").split(".") if x.strip()]
        if len(sents) >= 5:
            co += 0.4
        elif len(sents) >= 3:
            co += 0.2
        if any(_ci(em.body[:80], g) for g in ["hi ", "hello", "dear"]):
            co += 0.3
        if any(_ci(em.body[-150:], g) for g in ["thanks", "regards", "best", "sincerely"]):
            co += 0.3
        breakdown["email_quality"]["coherence"] = round(co, 4)

        email_score = (0.12 * r_score + 0.08 * cc_score + 0.10 * subj_score +
                       0.30 * body_score + 0.10 * nf_score + 0.10 * ml_score +
                       0.20 * co)

    breakdown["email_quality"]["score"] = round(email_score, 4)

    # ── 4. MEETING SCHEDULING (0.20) ─────────────────────────────────
    mtg_score = 0.0
    if ws.scheduled_meetings:
        m = ws.scheduled_meetings[-1]

        # 4a. Attendees (0.30)
        att_s = _overlap(m.attendees, exp.get("meeting_attendees", []))
        breakdown["meeting_scheduling"]["attendees"] = round(att_s, 4)

        # 4b. Duration (0.15)
        dur_s = 0.0
        try:
            from datetime import datetime
            st_dt = datetime.fromisoformat(m.start_time)
            et_dt = datetime.fromisoformat(m.end_time)
            dur = (et_dt - st_dt).total_seconds() / 60
            target = exp.get("meeting_duration_minutes", 30)
            if abs(dur - target) <= 5:
                dur_s = 1.0
            elif abs(dur - target) <= 15:
                dur_s = 0.5
        except Exception:
            pass
        breakdown["meeting_scheduling"]["duration"] = dur_s

        # 4c. Title (0.20)
        tk = exp.get("meeting_title_must_contain", [])
        title_s = _kw_score(m.title, tk)
        breakdown["meeting_scheduling"]["title"] = round(title_s, 4)

        # 4d. Description/agenda (0.15)
        dk = exp.get("meeting_description_must_contain", [])
        desc_s = 0.0
        if dk and m.description:
            desc_s = _kw_score(m.description, dk)
        elif not dk:
            desc_s = 1.0
        breakdown["meeting_scheduling"]["description"] = round(desc_s, 4)

        # 4e. Location (0.10)
        loc_s = 1.0 if (exp.get("meeting_must_have_location") and m.location) else 0.0
        breakdown["meeting_scheduling"]["location"] = loc_s

        # 4f. Date range (0.10)
        dr_s = 0.0
        try:
            from datetime import date, datetime as dt
            sd = dt.fromisoformat(m.start_time).date()
            rs = date.fromisoformat(exp.get("meeting_date_range_start", "2000-01-01"))
            re_ = date.fromisoformat(exp.get("meeting_date_range_end", "2099-12-31"))
            if rs <= sd <= re_:
                dr_s = 1.0
        except Exception:
            pass
        breakdown["meeting_scheduling"]["date_range"] = dr_s

        mtg_score = (0.30 * att_s + 0.15 * dur_s + 0.20 * title_s +
                     0.15 * desc_s + 0.10 * loc_s + 0.10 * dr_s)

    breakdown["meeting_scheduling"]["score"] = round(mtg_score, 4)

    # ── Combined: task 0.30, assignments 0.20, email 0.30, meeting 0.20
    s = (0.30 * tb_score + 0.20 * assign_score +
         0.30 * email_score + 0.20 * mtg_score)

    score = round(min(1.0, max(0.0, s)), 4)
    return score, breakdown


# ═══════════════════════════════════════════════════════════════════════
#  DISPATCHER
# ═══════════════════════════════════════════════════════════════════════

_GRADERS = {
    # Phase 1
    TaskType.EMAIL_DRAFT: _grade_email_draft,
    TaskType.BUG_TRIAGE: _grade_bug_triage,
    TaskType.MEETING_SCHEDULE: _grade_meeting_schedule,
    # Phase 3/4
    TaskType.INBOX_TRIAGE: _grade_inbox_triage,
    TaskType.MEETING_COORDINATION: _grade_meeting_coordination,
    TaskType.PROJECT_RESCUE: _grade_project_rescue,
}


def grade_task(ws: WorkspaceState, spec: TaskSpec) -> float:
    """Return 0.0–1.0 score for the current workspace state vs. task spec."""
    g = _GRADERS.get(spec.task_type)
    if g is None:
        raise ValueError(f"No grader for {spec.task_type}")
    score, _ = g(ws, spec)
    return score


def grade_task_detailed(ws: WorkspaceState, spec: TaskSpec) -> Tuple[float, Dict[str, Any]]:
    """Return (score, breakdown) for full grader introspection."""
    g = _GRADERS.get(spec.task_type)
    if g is None:
        raise ValueError(f"No grader for {spec.task_type}")
    return g(ws, spec)
