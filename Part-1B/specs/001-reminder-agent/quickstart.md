# Quickstart: RemindMe Agent

```bash
cd Part-1B
uv venv && uv pip install -e ".[dev]"
cp .env.example .env        # then put your own ANTHROPIC_API_KEY in .env (never commit it)
set -a; source .env; set +a

.venv/bin/remindme --now 2026-11-23T09:00:00+05:30 --tz Asia/Kolkata "remind me to call mom tomorrow at 6pm"
.venv/bin/remindme --now 2026-11-23T09:00:00+05:30 --tz Asia/Kolkata \
    --reminders examples/reminders.json "snooze my medicine reminder by 15 minutes"
```

Full harness (integrity → lint → offline tests → live evaluation, k = 3):

```bash
.harness/run_harness.sh
```

Re-score recorded model outputs without an API key:

```bash
.venv/bin/python .harness/run_eval.py --replay evidence/final-generation/raw-outputs.json
```
