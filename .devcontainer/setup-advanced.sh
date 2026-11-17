#!/usr/bin/env bash
# CIS 890 Software Factory — Advanced formal-methods installer.
# Run AFTER .devcontainer/setup.sh, on the 'advanced' branch only.
# Idempotent; requires network access on first installation.
set -euo pipefail

readonly LEAN_VERSION='v4.36.0'
readonly QUINT_VERSION='0.33.1'
readonly KANI_VERSION='0.68.0'
readonly ALLOY_VERSION='6.2.0'
readonly APALACHE_VERSION='0.63.0'
readonly TLA_RELEASE='v1.8.0'
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${HOME}/.elan/bin:${HOME}/.cargo/bin:${HOME}/.local/bin:${PATH}"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "Missing prerequisite: $1"; }

install_java() {
  log 'Checking Java 21+'
  local major=0
  if command -v java >/dev/null 2>&1; then
    major="$(java -version 2>&1 | sed -nE '1s/.*version "([0-9]+).*/\1/p')"
    major="${major:-0}"
  fi
  if (( major < 21 )); then
    sudo apt-get update
    sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openjdk-21-jdk
  fi
  java -version
}

install_lean() {
  log "Installing / checking Lean ${LEAN_VERSION}"
  if ! command -v elan >/dev/null 2>&1; then
    curl -fsSL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain "leanprover/lean4:${LEAN_VERSION}"
  fi
  # elan's installer can configure a toolchain without downloading it.
  elan toolchain install "leanprover/lean4:${LEAN_VERSION}"
  # Restrict the default for this container user to the verified version.
  elan default "leanprover/lean4:${LEAN_VERSION}"
  lean --version
  lake --version
}

install_quint() {
  log "Installing / checking Quint ${QUINT_VERSION}"
  need npm
  if ! command -v quint >/dev/null 2>&1 || [[ "$(quint --version 2>/dev/null)" != "${QUINT_VERSION}" ]]; then
    npm install -g "@informalsystems/quint@${QUINT_VERSION}"
  fi
  quint --version
}

install_kani() {
  log "Installing / checking Kani ${KANI_VERSION}"
  need cargo

  local version_output
  version_output="$(cargo kani --version 2>/dev/null || true)"

  if [[ "${version_output}" != *"Kani Rust Verifier ${KANI_VERSION}"* ]]; then
    cargo install --locked kani-verifier --version "${KANI_VERSION}"
    cargo kani setup
  elif [[ "${version_output}" != *"CBMC"* ]]; then
    cargo kani setup
  else
    echo "Kani ${KANI_VERSION} and CBMC already installed."
  fi

  cargo kani --version
}

install_tlc() {
  log "Installing / checking TLA+ tools (${TLA_RELEASE})"
  if [[ ! -s /opt/tlaplus/tla2tools.jar ]]; then
    sudo mkdir -p /opt/tlaplus
    local tmp
    tmp="$(mktemp)"
    curl -fL --retry 3 "https://github.com/tlaplus/tlaplus/releases/download/${TLA_RELEASE}/tla2tools.jar" -o "${tmp}"
    sudo install -m 0644 "${tmp}" /opt/tlaplus/tla2tools.jar
    rm -f "${tmp}"
  fi
  local tlc_output

  tlc_output="$(java -cp /opt/tlaplus/tla2tools.jar tlc2.TLC -help 2>&1 || true)"

  if [[ "${tlc_output}" != *"TLC - provides model checking"* ]]; then
    echo "ERROR: TLC verification failed." >&2
    return 1
  fi

  echo "TLA+ / TLC verified."
}

install_alloy() {
  log "Installing / checking Alloy ${ALLOY_VERSION}"
  if [[ ! -s /opt/alloy/alloy.jar ]]; then
    sudo mkdir -p /opt/alloy
    local tmp
    tmp="$(mktemp)"
    curl -fL --retry 3 "https://github.com/AlloyTools/org.alloytools.alloy/releases/download/v${ALLOY_VERSION}/org.alloytools.alloy.dist.jar" -o "${tmp}"
    sudo install -m 0644 "${tmp}" /opt/alloy/alloy.jar
    rm -f "${tmp}"
  fi
  java -jar /opt/alloy/alloy.jar help >/dev/null
  echo 'Alloy CLI verified'
}

install_apalache() {
  log "Installing / checking Apalache ${APALACHE_VERSION}"
  if [[ ! -x /opt/apalache/bin/apalache-mc ]]; then
    local tmpdir archive
    tmpdir="$(mktemp -d)"
    archive="${tmpdir}/apalache.tgz"
    curl -fL --retry 3 \
      "https://github.com/apalache-mc/apalache/releases/download/v${APALACHE_VERSION}/apalache-${APALACHE_VERSION}.tgz" \
      -o "${archive}"
    tar -tzf "${archive}" >/dev/null
    mkdir -p "${tmpdir}/unpack"
    tar -xzf "${archive}" -C "${tmpdir}/unpack" --strip-components=1
    [[ -f "${tmpdir}/unpack/bin/apalache-mc" ]] || die 'Unexpected Apalache archive layout'
    sudo mkdir -p /opt/apalache
    sudo cp -a "${tmpdir}/unpack/." /opt/apalache/
    sudo chmod +x /opt/apalache/bin/apalache-mc
    rm -rf "${tmpdir}"
  fi
  sudo ln -sfn /opt/apalache/bin/apalache-mc /usr/local/bin/apalache-mc
  apalache-mc version
}

main() {
  need curl
  need tar
  need sudo
  install_java
  install_lean
  install_quint
  install_kani
  install_tlc
  install_alloy
  install_apalache
  log 'Advanced formal-methods tool installation completed.'
  bash "${REPO_ROOT}/.devcontainer/verify-advanced.sh"
}

main "$@"
