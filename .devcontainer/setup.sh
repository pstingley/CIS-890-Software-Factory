#!/usr/bin/env bash
#
# Installs the CIS 890 tools that are not provided by Dev Container features
# (Doxygen, Graphviz, OpenSpec, and Claude Code), then verifies the environment.
#
# Runs automatically after the container is created, and is safe to rerun:
#   bash .devcontainer/setup.sh
#
# This script never writes to the repository. In particular, it does not run
# `openspec init` or `openspec update`, which could change .claude/ or openspec/.
# Do not add `set -x` here, and do not handle credentials in this script.

set -euo pipefail

# Must match the "generatedBy" version in .claude/skills/*/SKILL.md.
# verify_openspec_pin reports a mismatch.
readonly OPENSPEC_VERSION="1.16.0"
readonly CLAUDE_CHANNEL="stable"
readonly APT_PACKAGES=(doxygen graphviz)
readonly DOCKER_WAIT_SECONDS=60
readonly DOCKER_RUN_TIMEOUT_SECONDS=180

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly REPO_ROOT
readonly CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}"

# The Claude Code native installer puts its launcher here.
export PATH="${HOME}/.local/bin:${PATH}"

failures=0

log() { printf '\n==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
fail() {
  printf 'FAILED: %s\n' "$*" >&2
  failures=$((failures + 1))
}
die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

# OpenSpec requires Node.js 22.12.0 or newer. Fail early with a clear message.
require_node() {
  log "Checking Node.js"
  command -v node >/dev/null 2>&1 || die "Node.js was not found. Rebuild the container."
  node -e 'const [a, b] = process.versions.node.split(".").map(Number); process.exit(a === 22 && b >= 12 ? 0 : 1)' ||
    die "Node.js 22.12 or newer in the 22.x line is required; found $(node --version)."
  echo "Node.js $(node --version) is suitable."
}

install_apt_packages() {
  log "Installing Doxygen and Graphviz"
  local missing=() pkg
  for pkg in "${APT_PACKAGES[@]}"; do
    if ! dpkg-query -W -f='${Status}' "${pkg}" 2>/dev/null | grep -q 'install ok installed'; then
      missing+=("${pkg}")
    fi
  done

  if [[ ${#missing[@]} -eq 0 ]]; then
    echo "Already installed: ${APT_PACKAGES[*]}"
    return
  fi

  sudo apt-get update
  sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
}

# The Node.js feature gives vscode write access to npm's global directory, so
# sudo is never needed. If that directory is not writable, install under
# ~/.local/bin, which is on PATH, instead of using sudo.
install_openspec() {
  log "Installing OpenSpec ${OPENSPEC_VERSION}"
  local installed npm_prefix
  installed="$(openspec --version 2>/dev/null || true)"

  if [[ "${installed}" == "${OPENSPEC_VERSION}" ]]; then
    echo "Already installed."
    return
  fi

  npm_prefix="$(npm config get prefix)"
  if [[ -w "${npm_prefix}/lib/node_modules" ]]; then
    npm install -g "@fission-ai/openspec@${OPENSPEC_VERSION}"
  else
    warn "${npm_prefix} is not writable by $(id -un). Installing to ~/.local instead."
    npm install -g --prefix "${HOME}/.local" "@fission-ai/openspec@${OPENSPEC_VERSION}"
  fi
  hash -r
}

# A new named volume can be owned by root. Claude Code stores its sign-in and
# settings here, so make it writable without ever reading what it contains.
prepare_claude_config_dir() {
  if [[ ! -d "${CLAUDE_DIR}" || ! -w "${CLAUDE_DIR}" ]]; then
    sudo mkdir -p "${CLAUDE_DIR}"
    sudo chown "$(id -u):$(id -g)" "${CLAUDE_DIR}"
  fi
}

install_claude_code() {
  log "Installing Claude Code (${CLAUDE_CHANNEL} channel)"
  prepare_claude_config_dir

  if command -v claude >/dev/null 2>&1; then
    echo "Already installed. Claude Code updates itself."
    return
  fi

  curl -fsSL https://claude.ai/install.sh | bash -s "${CLAUDE_CHANNEL}"
  hash -r
}

# Only reports on these directories. It must never create or change them.
check_project_dirs() {
  log "Checking existing project directories"
  local dir
  for dir in .claude openspec; do
    if [[ -d "${REPO_ROOT}/${dir}" ]]; then
      echo "Found ${dir}/ (left unchanged)."
    else
      warn "${dir}/ was not found. It has probably not been committed. Setup will not create it."
    fi
  done
}

check() {
  local label="$1" output
  shift
  if output="$("$@" 2>&1)"; then
    printf '  %-16s %s\n' "${label}" "${output%%$'\n'*}"
  else
    printf '  %-16s FAILED: %s\n' "${label}" "$*"
    failures=$((failures + 1))
  fi
}

verify_tools() {
  log "Verifying installed tools"
  check "Python" python3 --version
  check "pip" pip3 --version
  check "Node.js" node --version
  check "npm" npm --version
  check "Git" git --version
  check "Docker CLI" docker --version
  check "Docker Compose" docker compose version
  check "Doxygen" doxygen --version
  check "Graphviz" dot -V
  check "OpenSpec" openspec --version
  check "Claude Code" claude --version
}

verify_openspec_pin() {
  log "Verifying the OpenSpec version against the generated skills"
  local generated
  generated="$(grep -rhoE 'generatedBy: "[^"]+"' "${REPO_ROOT}/.claude/skills" 2>/dev/null |
    sed -E 's/.*"([^"]+)"/\1/' | sort -u || true)"

  if [[ -z "${generated}" ]]; then
    warn "No generated OpenSpec skills were found to compare."
  elif [[ "${generated}" == "${OPENSPEC_VERSION}" ]]; then
    echo "Skills and the pinned CLI both use ${OPENSPEC_VERSION}."
  else
    fail "The pinned CLI is ${OPENSPEC_VERSION}, but the skills were generated by: ${generated//$'\n'/, }."
  fi
}

verify_openspec_telemetry() {
  log "Verifying that OpenSpec telemetry is disabled"
  if [[ "${OPENSPEC_TELEMETRY:-}" == "0" ]]; then
    echo "OPENSPEC_TELEMETRY=0"
  else
    fail "OPENSPEC_TELEMETRY is not 0. Check containerEnv in devcontainer.json and rebuild."
  fi
}

verify_claude_storage() {
  log "Verifying Claude Code credential storage"
  if mountpoint -q "${CLAUDE_DIR}"; then
    echo "${CLAUDE_DIR} is a mounted volume outside the repository."
  else
    fail "${CLAUDE_DIR} is not a mounted volume, so your sign-in would not survive a rebuild."
  fi
}

# Checks the daemon end to end: start a container, read its output, remove it.
verify_docker_daemon() {
  log "Verifying the Docker daemon by running a container"
  local waited=0 output

  until docker info >/dev/null 2>&1; do
    if [[ ${waited} -ge ${DOCKER_WAIT_SECONDS} ]]; then
      fail "The Docker daemon did not respond within ${DOCKER_WAIT_SECONDS} seconds."
      return
    fi
    sleep 2
    waited=$((waited + 2))
  done

  if output="$(timeout "${DOCKER_RUN_TIMEOUT_SECONDS}" docker run --rm hello-world 2>&1)" &&
    grep -q 'Hello from Docker!' <<<"${output}"; then
    echo "Container ran and printed: Hello from Docker!"
  else
    fail "docker run --rm hello-world did not succeed: ${output}"
  fi
}

report_result() {
  if [[ ${failures} -gt 0 ]]; then
    die "${failures} check(s) failed. See .devcontainer/README.md, then rerun this script."
  fi
  log "Setup complete. Run 'claude' to sign in. Never commit credentials."
}

main() {
  require_node
  install_apt_packages
  install_openspec
  install_claude_code
  check_project_dirs
  verify_tools
  verify_openspec_pin
  verify_openspec_telemetry
  verify_claude_storage
  verify_docker_daemon
  report_result
}

main "$@"
