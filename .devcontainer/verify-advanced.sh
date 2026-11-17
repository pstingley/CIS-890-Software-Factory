#!/usr/bin/env bash
# Verify tools installed by setup-advanced.sh; reports version and smoke checks.
set -euo pipefail
export PATH="${HOME}/.elan/bin:${HOME}/.cargo/bin:${HOME}/.local/bin:${PATH}"

check() {
  local name="$1"
  shift
  printf '%-18s ' "${name}:"
  "$@"
}

check 'Java' java -version
check 'Lean' lean --version
check 'Lake' lake --version
check 'Quint' quint --version
check 'Kani / CBMC' cargo kani --version

# TLC returns exit code 1 when displaying help, even when working correctly.
tlc_output="$(java -cp /opt/tlaplus/tla2tools.jar tlc2.TLC -help 2>&1 || true)"
if [[ "${tlc_output}" != *"TLC - provides model checking"* ]]; then
  echo "ERROR: TLC verification failed." >&2
  exit 1
fi

printf 'TLC:               CLI verified\n'
check 'Alloy' java -jar /opt/alloy/alloy.jar version
check 'Apalache' apalache-mc version
printf '\nAll Advanced formal-methods command checks passed.\n'
