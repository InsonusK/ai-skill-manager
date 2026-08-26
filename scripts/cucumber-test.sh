#!/usr/bin/env bash
# Runs the Cucumber/Gherkin conformance suite via behave (plus the plain test suite),
# both under coverage.py, and normalizes the results into tmp/result/*.json, keeping
# the native browsable report under tmp/report/.
#
# Params (env vars, optional):
#   WITH_CODE_COVERAGE=true   also collect and report line coverage
set -euo pipefail

PYTHON="${PYTHON:-python}"
WITH_CODE_COVERAGE="${WITH_CODE_COVERAGE:-false}"

RESULT_DIR="tmp/result"
REPORT_DIR="tmp/report"

rm -rf "$REPORT_DIR/tests" "$REPORT_DIR/coverage" .coverage
mkdir -p "$RESULT_DIR" "$REPORT_DIR/tests"

BEHAVE_JSON="$(mktemp)"
trap 'rm -f "$BEHAVE_JSON"' EXIT

set +e
$PYTHON -m coverage run -m behave \
  --format json.pretty --outfile "$BEHAVE_JSON"
BEHAVE_EXIT_CODE=$?
set -e

$PYTHON -m coverage run -a -m pytest src/

# Normalize behave JSON into the contract schema.
TOTAL=$(jq '[.[].elements[]] | length' "$BEHAVE_JSON")
PASSED=$(jq '[.[].elements[] | select(all(.steps[]; .result.status == "passed"))] | length' "$BEHAVE_JSON")
FAILED=$((TOTAL - PASSED))
printf '{"total":%s,"passed":%s,"failed":%s}' "$TOTAL" "$PASSED" "$FAILED" > "$RESULT_DIR/cucumber-test.json"

# Render a simple HTML report from the behave JSON output.
$PYTHON - "$BEHAVE_JSON" "$REPORT_DIR/tests/index.html" <<'PY'
import json
import sys
from html import escape
from pathlib import Path

behave_json_path = Path(sys.argv[1])
html_path = Path(sys.argv[2])
html_path.parent.mkdir(parents=True, exist_ok=True)

data = json.loads(behave_json_path.read_text())

html_parts = [
    "<!DOCTYPE html>",
    '<html lang="en">',
    "<head>",
    '  <meta charset=\"utf-8\">',
    '  <title>Cucumber Test Report</title>',
    '  <style>',
    '    body { font-family: sans-serif; margin: 2rem; }',
    '    .feature { margin-bottom: 2rem; }',
    '    .scenario { margin-left: 1rem; margin-bottom: 1rem; }',
    '    .step { margin-left: 1rem; }',
    '    .passed { color: green; }',
    '    .failed { color: red; }',
    '    .skipped { color: gray; }',
    '  </style>',
    '</head>',
    '<body>',
    '  <h1>Cucumber Test Report</h1>',
]

for feature in data:
    html_parts.append(f'  <div class=\"feature\">')
    html_parts.append(f'    <h2>{escape(feature.get("name", ""))}</h2>')
    for scenario in feature.get('elements', []):
        scenario_status = 'passed'
        for step in scenario.get('steps', []):
            if step.get('result', {}).get('status') != 'passed':
                scenario_status = step.get('result', {}).get('status', 'failed')
                break
        html_parts.append(f'    <div class=\"scenario\">')
        html_parts.append(f'      <h3 class=\"{scenario_status}\">{escape(scenario.get("name", ""))}</h3>')
        for step in scenario.get('steps', []):
            status = step.get('result', {}).get('status', 'skipped')
            name = step.get('keyword', '') + ' ' + step.get('name', '')
            html_parts.append(f'      <div class=\"step {status}\">{escape(name)}</div>')
        html_parts.append('    </div>')
    html_parts.append('  </div>')

html_parts += [
    '</body>',
    '</html>',
]

html_path.write_text('\n'.join(html_parts))
PY

if [ "$WITH_CODE_COVERAGE" = "true" ]; then
  $PYTHON -m coverage html -d "$REPORT_DIR/coverage"
  $PYTHON -m coverage json -o "$REPORT_DIR/coverage/coverage.json"
  LINE_PCT=$(jq '.totals.percent_covered' "$REPORT_DIR/coverage/coverage.json")
  rm "$REPORT_DIR/coverage/coverage.json"
  printf '{"linePct":%s}' "$LINE_PCT" > "$RESULT_DIR/coverage-test.json"
fi

exit "$BEHAVE_EXIT_CODE"
