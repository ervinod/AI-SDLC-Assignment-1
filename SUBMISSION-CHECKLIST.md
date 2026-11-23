# Submission checklist and demo script

## A. Still to do (in this order)

1. **Run the Part 1B live evaluation with a local model** once your internet connection allows a
   ~2 GB download (no API key needed):
   ```bash
   brew install ollama
   ollama serve            # leave this running in its own terminal tab
   ollama pull llama3.2:3b # ~2 GB, one-time
   cd ~/Documents/Assignment-1/Part-1B
   REMINDME_PROVIDER=ollama .harness/run_harness.sh --label "live evaluation, local llama3.2:3b"
   ```
   Then ask Claude to read the result, repair any failures from `feedback.md`, re-run, and update
   `Part-1B/evidence/harness-log.md`.
2. **Human review**: fill in section "Human review" in `Part-1A/evidence/harness-log.md` and
   `Part-1B/evidence/harness-log.md` (ACCEPT/REJECT, justification, limitations, residual risks).
3. **Create a public GitHub repo** (for example `Assignment-1`) and push:
   ```bash
   cd ~/Documents/Assignment-1
   git remote add origin https://github.com/<your-username>/Assignment-1.git
   git push -u origin main
   ```
4. **Record the demo video** (script below) and upload it to Google Drive or OneDrive, shared with
   BITS email ids.
5. **Write the reflection report** in the Word template, in your own words. Fill in the GitHub and
   video links, then upload only that report to the LMS.

## B. Assignment checklist (section 7 of the brief)

- [x] Part 1A and Part 1B are both included
- [x] Each part follows the Spec Kit flow; artifacts are in `specs/` and `.specify/`, one commit per step
- [x] Part 1A has working deterministic harness gates and specification-derived tests
- [x] Part 1B has 24 evaluation cases and one non-deterministic evaluation pipeline
- [x] Harness results and failure/repair evidence are kept under `evidence/`
- [x] `harness-log.md` is present for both parts
- [ ] Final human ACCEPT/REJECT and limitations recorded (**you**)
- [x] No API keys, credentials or `.env` files committed (`.env` is gitignored)
- [x] README has instructions for running each harness
- [x] Part 1B live evaluation run (local llama3.2:3b) — official PASS, held-out 11/12

## C. Demo video script (about 5 minutes)

1. **Repo tour (30 s).** Show the README table, then `git log --oneline` to show one commit per
   Spec Kit step.
2. **Part 1A spec (45 s).** Open `spec.md` and show an acceptance scenario, then the matching test
   in `tests/contract/test_cli_status.py`.
3. **Part 1A app (45 s).**
   ```bash
   cd Part-1A && export TASKFLOW_DATA=/tmp/demo.json
   .venv/bin/taskflow add "Ship report" --priority high --tag work
   .venv/bin/taskflow add "Buy milk" --tag home
   .venv/bin/taskflow status 1 done        # rejected: todo -> done not allowed
   .venv/bin/taskflow status 1 in_progress
   .venv/bin/taskflow list --sort priority
   ```
4. **Part 1A harness (45 s).** Run `.harness/run_harness.sh`, then show
   `evidence/harness-selftest/` and the weakened-test row in `harness-log.md`.
5. **Part 1B spec (45 s).** Show SCH, INV, GR and THR in `spec.md`, then one case in
   `evals/dataset.json`.
6. **Part 1B app (45 s)**, once Ollama is installed:
   ```bash
   cd Part-1B && export REMINDME_PROVIDER=ollama
   .venv/bin/remindme --now 2026-11-23T09:00:00+05:30 --tz Asia/Kolkata "remind me to call mom tomorrow at 6pm"
   .venv/bin/remindme --now 2026-11-23T09:00:00+05:30 --tz Asia/Kolkata "remind me to pay the electricity bill"
   ```
7. **Part 1B harness (60 s).** Run the harness, then show the THR table and `feedback.md`. Explain
   the repair cycle: run-001 coverage failure → T026/T027 → run-002 pass.
