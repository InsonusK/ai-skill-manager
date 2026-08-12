#!/usr/bin/env bash
# Runs mutmut mutation testing and normalizes the results into
# tmp/result/mutation-test.json, keeping the native browsable report under
# tmp/report/mutation.
#
# Params (env vars):
#   ONLY_DELTA=true   only mutate source files changed since DELTA_BASE (for PRs);
#                     default is a full run, which is report-only and never gates.
#   DELTA_BASE=<ref>  git ref to diff against; required when ONLY_DELTA=true.
set -euo pipefail

PYTHON="${PYTHON:-python}"
ONLY_DELTA="${ONLY_DELTA:-false}"
DELTA_BASE="${DELTA_BASE:-}"

RESULT_DIR="tmp/result"
REPORT_DIR="tmp/report/mutation"

mkdir -p "$RESULT_DIR"
rm -rf "$REPORT_DIR" mutants .mutmut-cache

DELTA_FILES=()
if [ "$ONLY_DELTA" = "true" ]; then
  if [ -z "$DELTA_BASE" ]; then
    echo "DELTA_BASE is required when ONLY_DELTA=true" >&2
    exit 1
  fi

  mapfile -t DELTA_FILES < <(git diff --name-only --diff-filter=ACMR "$DELTA_BASE" HEAD -- 'src/**/*.py')
  if [ "${#DELTA_FILES[@]}" -eq 0 ]; then
    echo "No changes in src/**/*.py since $DELTA_BASE — skipping mutation testing."
    mkdir -p "$REPORT_DIR"
    printf '{"killed":0,"survived":0,"timedout":0,"noCoverage":0,"score":"0.0"}' > "$RESULT_DIR/mutation-test.json"
    cat > "$REPORT_DIR/index.html" <<'HTML'
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mutation Test Report</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; }
  </style>
</head>
<body>
  <h1>Mutation Test Report</h1>
  <p>No source files changed since the delta base — mutation testing was skipped.</p>
</body>
</html>
HTML
    exit 0
  fi
fi

# Temporarily scope mutmut to changed files for delta runs by writing only_mutate
# into pyproject.toml and restoring it afterwards.
PYPROJECT_BACKUP="$(mktemp)"
cp pyproject.toml "$PYPROJECT_BACKUP"
trap 'if [ -s "$PYPROJECT_BACKUP" ]; then cp "$PYPROJECT_BACKUP" pyproject.toml; fi; rm -f "$PYPROJECT_BACKUP"' EXIT

if [ "$ONLY_DELTA" = "true" ]; then
  ONLY_MUTATE_JSON=$(printf '%s\n' "${DELTA_FILES[@]}" | jq -R . | jq -s .)
  export ONLY_MUTATE_JSON
  $PYTHON - <<'PY'
import json
import os
import tomllib
import tomli_w

files = json.loads(os.environ["ONLY_MUTATE_JSON"])

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

data.setdefault("tool", {}).setdefault("mutmut", {})["only_mutate"] = files

with open("pyproject.toml", "wb") as f:
    tomli_w.dump(data, f)
PY
fi

set +e
$PYTHON -m mutmut run
MUTMUT_EXIT_CODE=$?
set -e

# Generate a machine-readable stats file and a minimal HTML report.
$PYTHON -m mutmut export-cicd-stats
mkdir -p "$REPORT_DIR"
cp mutants/mutmut-cicd-stats.json "$REPORT_DIR/mutmut-cicd-stats.json"

$PYTHON - <<'PY'
import json
from pathlib import Path

report_dir = Path("tmp/report/mutation")
report_dir.mkdir(parents=True, exist_ok=True)
stats_file = report_dir / "mutmut-cicd-stats.json"
stats = json.loads(stats_file.read_text())

killed = stats.get("killed", 0)
survived = stats.get("survived", 0)
timedout = stats.get("timeout", 0)
no_coverage = stats.get("no_tests", 0)
tested = killed + survived + timedout + no_coverage
score = "0.0" if tested == 0 else f"{killed / tested * 100:.1f}"

result = {
    "killed": killed,
    "survived": survived,
    "timedout": timedout,
    "noCoverage": no_coverage,
    "score": score,
}
Path("tmp/result/mutation-test.json").write_text(json.dumps(result))

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mutation Test Report</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem 1rem; text-align: left; }}
    .score {{ font-size: 2rem; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Mutation Test Report</h1>
  <p class="score">Score: {score}%</p>
  <table>
    <tr><th>Killed</th><td>{killed}</td></tr>
    <tr><th>Survived</th><td>{survived}</td></tr>
    <tr><th>Timed out</th><td>{timedout}</td></tr>
    <tr><th>No coverage</th><td>{no_coverage}</td></tr>
    <tr><th>Total tested</th><td>{tested}</td></tr>
  </table>
</body>
</html>
"""
(report_dir / "index.html").write_text(html)
PY

# On PR delta runs, enforce the threshold: any surviving mutant in changed code fails the gate.
if [ "$ONLY_DELTA" = "true" ]; then
  SURVIVED=$(jq '.survived' "$RESULT_DIR/mutation-test.json")
  if [ "$SURVIVED" -gt 0 ]; then
    echo "Mutation testing found $SURVIVED surviving mutant(s) in changed code." >&2
    exit 1
  fi
  # Propagate mutmut's own exit code for real tool failures / untested changed code.
  exit "$MUTMUT_EXIT_CODE"
fi

# Full run (master push) is report-only: always exit 0 once the report exists.
exit 0
