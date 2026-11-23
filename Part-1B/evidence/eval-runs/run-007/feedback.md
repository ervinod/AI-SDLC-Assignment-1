# Evaluation feedback — PASS

| Threshold | Value | Pass |
|---|---|---|
| THR-1 schema validity = 100% | 1.0 | True |
| THR-2 universal invariants = 100% | 1.0 | True |
| THR-3 guardrail cases = 100% | 1.0 | True |
| THR-4 case pass rate >= 85% | 0.9583 | True |
| THR-5 mean semantic >= 0.85 | 0.9861 | True |
| THR-6 service errors <= 10% | 0.0 | True |

## Failing trials (2)

### C15 trial 1 — missing_info — Requested time is in the past
- requirements: GR-5, INV-7, US3-AS4
- request text: "remind me yesterday at 3pm to file the report"
- status: ok
- expected: {"intent": "clarify", "missing": ["time"], "must_not_act": true}
- output: {"intent": "clarify", "task": "File the report", "due_at": null, "recurrence": null, "target_id": null, "snooze_minutes": null, "missing": ["target"], "question": "Which of your existing reminders do you mean?", "reason": null}
- layer1: ok
- layer2: ok
- layer3: score=0.5 criteria={'intent': 1.0, 'missing': 0.0}

### C15 trial 2 — missing_info — Requested time is in the past
- requirements: GR-5, INV-7, US3-AS4
- request text: "remind me yesterday at 3pm to file the report"
- status: ok
- expected: {"intent": "clarify", "missing": ["time"], "must_not_act": true}
- output: {"intent": "clarify", "task": "File the report", "due_at": null, "recurrence": null, "target_id": null, "snooze_minutes": null, "missing": ["target"], "question": "Which of your existing reminders do you mean?", "reason": null}
- layer1: ok
- layer2: ok
- layer3: score=0.5 criteria={'intent': 1.0, 'missing': 0.0}

Repair scope for the coding agent: `src/` and `prompts/` only. Do not change evals/, tests/, .harness/ or the spec (integrity gate). Service errors are not app failures.
