#!/usr/bin/env bash
# Ejecuta todas las pruebas de navegador contra la app servida en localhost:8766.
# Uso: tests/run.sh            (todas)
#      tests/run.sh descanso   (solo las que contengan "descanso" en el nombre)
# Requisitos: node y playwright (Chromium). Las capturas quedan en tests/.out/
set -u
cd "$(dirname "$0")/.."
export FIX="$PWD/tests/fixtures"
export OUT="$PWD/tests/.out"
mkdir -p "$OUT"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"

if ! curl -s -o /dev/null http://localhost:8766/; then
  python3 -m http.server 8766 >/dev/null 2>&1 &
  SERVER=$!
  trap 'kill $SERVER 2>/dev/null' EXIT
  sleep 1
fi

fail=0
for t in tests/*${1:-}*.test.js; do
  name=$(basename "$t" .test.js)
  log="$OUT/$name.log"
  if timeout 150 node "$t" >"$log" 2>&1 && ! grep -qE 'errors:? \[[^]]' "$log"; then
    echo "✓ $name"
  else
    echo "✗ $name  (ver $log)"
    tail -5 "$log" | sed 's/^/    /'
    fail=1
  fi
done
exit $fail
