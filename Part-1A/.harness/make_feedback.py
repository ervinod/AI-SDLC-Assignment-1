"""Turn raw gate output into structured evidence for the coding agent and the harness log.

Writes <run>/summary.json and <run>/feedback.md. Exit code 0 = all gates passed, 1 = otherwise.
"""

import json
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses junit.xml produced locally by pytest
from pathlib import Path

TAIL = 60


def tail(path: Path, n: int = TAIL) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])


def failed_tests(junit: Path) -> list[dict]:
    if not junit.exists():
        return []
    root = ET.parse(junit).getroot()  # nosec B314 - trusted local file
    out = []
    for case in root.iter("testcase"):
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is not None:
                out.append(
                    {
                        "test": f"{case.get('classname')}::{case.get('name')}",
                        "kind": kind,
                        "message": (node.get("message") or "")[:500],
                        "detail": (node.text or "")[-1500:],
                    }
                )
    return out


def main() -> int:
    out, run_id, start, label, names, codes = sys.argv[1:7]
    out_dir = Path(out)
    gates = []
    for name, code in zip(names.split(), codes.split(), strict=True):
        gates.append(
            {"gate": name, "exit_code": int(code), "result": "PASS" if code == "0" else "FAIL"}
        )
    overall = "PASS" if all(g["result"] == "PASS" for g in gates) else "FAIL"
    fails = failed_tests(out_dir / "junit.xml")
    summary = {
        "run": run_id,
        "started_utc": start,
        "label": label,
        "overall": overall,
        "gates": gates,
        "failed_tests": [{k: f[k] for k in ("test", "kind", "message")} for f in fails],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    md = [f"# Harness feedback — {run_id} ({overall})", ""]
    if label:
        md += [f"Label: {label}", ""]
    md += ["| Gate | Result | Exit |", "|------|--------|------|"]
    md += [f"| {g['gate']} | {g['result']} | {g['exit_code']} |" for g in gates]
    for g in gates:
        if g["result"] == "FAIL" and g["gate"] != "tests":
            md += ["", f"## Gate `{g['gate']}` failed", "", "```text"]
            md += [
                tail(out_dir / f"{g['gate']}.stdout.txt"),
                tail(out_dir / f"{g['gate']}.stderr.txt"),
            ]
            md += ["```"]
    if fails:
        md += ["", f"## Failed tests ({len(fails)})"]
        for f in fails:
            md += ["", f"### {f['test']}", "", f"- kind: {f['kind']}", f"- message: {f['message']}"]
            md += ["", "```text", f["detail"].strip(), "```"]
    tests_gate = next((g for g in gates if g["gate"] == "tests"), None)
    if tests_gate and tests_gate["result"] == "FAIL" and not fails:
        md += [
            "",
            "## Gate `tests` failed (no individual test failures — e.g. coverage)",
            "",
            "```text",
        ]
        md += [tail(out_dir / "tests.stdout.txt", 30), "```"]
    md += [
        "",
        "Instructions to the coding agent: repair `src/` only. Do not edit tests, the spec, "
        "or anything under `.harness/` (integrity gate).",
    ]
    (out_dir / "feedback.md").write_text("\n".join(md) + "\n")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
