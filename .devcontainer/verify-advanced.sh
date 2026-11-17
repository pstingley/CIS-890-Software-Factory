#!/usr/bin/env bash
# Verify tools installed by setup-advanced.sh; reports version and smoke checks.
set -euo pipefail
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
check 'pytest' "${REPO_ROOT}/.venv-advanced/bin/python" -m pytest --version
check 'pytest-bdd' "${REPO_ROOT}/.venv-advanced/bin/python" -m pip show pytest-bdd
check 'Deal' "${REPO_ROOT}/.venv-advanced/bin/python" -m pip show deal
check 'Cucumber' "${REPO_ROOT}/tools/advanced/cucumber/node_modules/.bin/cucumber-js" --version
printf '\nAll Advanced Software Factory command checks passed.\n'