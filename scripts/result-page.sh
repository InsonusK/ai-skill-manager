#!/usr/bin/env bash
# Assembles public/ (the GitHub Pages site) purely from tmp/result/*.json summaries and
# tmp/report/* native reports - no test/build tooling involved, so this can run as its
# own CI job (or locally) once cucumber-test/mutation-test have populated tmp/.
set -euo pipefail

RESULT_DIR="tmp/result"
REPORT_DIR="tmp/report"
PUBLIC_DIR="public"

for required in "$RESULT_DIR/cucumber-test.json" "$RESULT_DIR/mutation-test.json" "$REPORT_DIR/tests" "$REPORT_DIR/mutation"; do
  if [ ! -e "$required" ]; then
    echo "result-page: expected $required to exist - did cucumber-test/mutation-test run (and their artifacts get downloaded) first?" >&2
    exit 1
  fi
done

mkdir -p "$PUBLIC_DIR"
cp .github/pages/index.html "$PUBLIC_DIR/index.html"

for name in tests coverage mutation; do
  if [ -d "$REPORT_DIR/$name" ]; then
    rm -rf "${PUBLIC_DIR:?}/$name"
    cp -r "$REPORT_DIR/$name" "$PUBLIC_DIR/$name"
  fi
done

score_color() {
  awk -v s="$1" 'BEGIN { if (s >= 80) print "brightgreen"; else if (s >= 60) print "yellowgreen"; else print "red" }'
}

TOTAL=$(jq '.total' "$RESULT_DIR/cucumber-test.json")
PASSED=$(jq '.passed' "$RESULT_DIR/cucumber-test.json")
COLOR="red"
[ "$PASSED" = "$TOTAL" ] && COLOR="brightgreen"
printf '{"schemaVersion":1,"label":"tests","message":"%s/%s passed","color":"%s"}' \
  "$PASSED" "$TOTAL" "$COLOR" > "$PUBLIC_DIR/tests-badge.json"

if [ -f "$RESULT_DIR/coverage-test.json" ]; then
  PCT=$(jq '.linePct' "$RESULT_DIR/coverage-test.json")
  printf '{"schemaVersion":1,"label":"coverage","message":"%s%%","color":"%s"}' \
    "$PCT" "$(score_color "$PCT")" > "$PUBLIC_DIR/coverage-badge.json"
fi

SCORE=$(jq '.score' "$RESULT_DIR/mutation-test.json")
printf '{"schemaVersion":1,"label":"mutation score","message":"%s%%","color":"%s"}' \
  "$SCORE" "$(score_color "$SCORE")" > "$PUBLIC_DIR/mutation-badge.json"
