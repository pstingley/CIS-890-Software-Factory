# CIS 890 Development Environment

This Dev Container gives everyone in CIS 890 the same Ubuntu-based toolset, in GitHub Codespaces or in local VS Code with Docker Desktop.

## Files

| File | Purpose |
|---|---|
| `devcontainer.json` | Defines the base image, Python, Node.js, Git, Docker, the VS Code extension, and environment settings |
| `setup.sh` | Installs Doxygen, Graphviz, OpenSpec, and Claude Code, then verifies the environment |
| `README.md` | This guide |
| `../.gitattributes` | Keeps LF line endings on shell scripts, including on Windows |
| `../.gitignore` | Keeps credentials, `.env` files, virtual environments, caches, and local Claude settings out of Git |

## Open the environment

### GitHub Codespaces

1. On the repository page, select **Code > Codespaces > Create codespace on main**.
2. Wait for setup to finish. To follow its progress, run **Codespaces: View Creation Log** from the Command Palette.

### Local VS Code with Docker Desktop

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/), [VS Code](https://code.visualstudio.com/) 1.94 or newer, and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

1. Start Docker Desktop.
2. Clone this repository and open the folder in VS Code. On Windows, clone it inside your WSL 2 file system for better performance.
3. Select **Reopen in Container** when prompted, or run **Dev Containers: Reopen in Container** from the Command Palette.

## Codespaces and Docker Desktop compared

The tools and setup steps are the same. These are the differences you will notice:

| | GitHub Codespaces | Local Docker Desktop |
|---|---|---|
| **Where it runs** | A virtual machine in GitHub's cloud | Docker Desktop on your own computer |
| **What you need** | A GitHub account and a browser or VS Code | Docker Desktop, VS Code, and the Dev Containers extension |
| **Your code** | A clone of the pushed branch, stored in the codespace | Your local clone, mounted into the container |
| **Unpushed work** | Stays in that codespace, and is lost if the codespace is deleted | Stays in your local clone, even if the container is removed |
| **Cost and limits** | Uses your Codespaces quota; stop codespaces you are not using | Uses your own computer; check that Docker Desktop's license terms apply to you |
| **Computing resources** | Set by the machine type you choose | Set in Docker Desktop's settings, limited by your computer |
| **Processor type** | x86-64 | Matches your computer, which means ARM64 on Apple Silicon |
| **Stopping** | Stops after a period of inactivity; files are kept | Runs until you close it or stop Docker Desktop |
| **Git authentication** | Provided by Codespaces | VS Code shares your local Git credential helper with the container |
| **Claude Code sign-in** | Saved in a volume for that codespace; a new codespace needs a new sign-in or a personal Codespaces secret | Saved in a volume on your computer for this project; there is no equivalent of Codespaces secrets |
| **Docker-in-Docker** | Privileged within the codespace's virtual machine | Privileged within Docker Desktop's Linux environment on your computer |
| **Ports** | Forwarded through GitHub, private to you by default | Forwarded to `localhost` on your computer |
| **Rebuild command** | **Codespaces: Rebuild Container** | **Dev Containers: Rebuild Container** |

Because Apple Silicon computers run ARM64, an image built only for x86-64 may run slowly or not at all there, even if it works in Codespaces.

## Installed components

| Component | Version | Installed by |
|---|---|---|
| Ubuntu | 24.04 | `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` |
| Python 3 and pip | Ubuntu's Python 3 | `python` feature |
| Node.js and npm | Latest 22.x | `node` feature |
| Git | Ubuntu's Git | `git` feature |
| Docker CLI, Engine, and Compose | Latest | `docker-in-docker` feature |
| Doxygen | Ubuntu's Doxygen | `setup.sh` (apt) |
| Graphviz | Ubuntu's Graphviz | `setup.sh` (apt) |
| OpenSpec | 1.16.0, telemetry disabled | `setup.sh` (official npm package) |
| Claude Code CLI | Stable channel, updates itself | `setup.sh` (official native installer) |
| Claude Code VS Code extension | Latest | `devcontainer.json` (`anthropic.claude-code`) |

The Dev Container features also add these VS Code extensions:

| Added by | Extensions |
|---|---|
| `docker-in-docker` feature | Container Tools (`ms-azuretools.vscode-containers`) |
| `node` feature | ESLint (`dbaeumer.vscode-eslint`) |
| `python` feature | Python (`ms-python.python`), Pylance (`ms-python.vscode-pylance`), and autopep8 (`ms-python.autopep8`) |

## Validate each tool

Run these commands in a terminal inside the container, from the repository root. `setup.sh` runs the main checks automatically, and these let you confirm each tool yourself.

### Python

```bash
python3 --version
pip3 --version
python3 -m venv /tmp/venv-test && /tmp/venv-test/bin/python -c 'print("Python OK")'
```

**Expected:** a Python 3 version, a pip version, and `Python OK`.

### Git

```bash
git --version
git rev-parse --is-inside-work-tree
git check-attr eol -- .devcontainer/setup.sh
```

**Expected:** a Git version, `true`, and `.devcontainer/setup.sh: eol: lf`.

### Node.js

```bash
node --version
npm --version
test -w "$(npm config get prefix)/lib/node_modules" && echo "npm global OK"
```

**Expected:** `v22.x.x` (22.12 or newer), an npm version, and `npm global OK`. Never use `sudo npm install -g`.

### OpenSpec

```bash
openspec --version
openspec doctor
grep -rho 'generatedBy: .*' .claude/skills | sort -u
echo "OPENSPEC_TELEMETRY=$OPENSPEC_TELEMETRY"
```

**Expected:** `1.16.0`, `OpenSpec root: ok`, `generatedBy: "1.16.0"`, and `OPENSPEC_TELEMETRY=0`.

### Claude Code

```bash
claude --version
claude doctor
mountpoint ~/.claude
```

**Expected:** a version, an installation report without errors, and `/home/vscode/.claude is a mountpoint`. Also open the Extensions view and search for `Claude Code`. It should show as installed in the container or codespace.

### Docker

```bash
docker --version
docker compose version
docker run --rm hello-world
```

**Expected:** a Docker version, a Compose version, and `Hello from Docker!`. The last command proves the daemon works, because it pulls an image and runs a real container.

### Doxygen

```bash
doxygen --version
doxygen -g /tmp/Doxyfile > /dev/null && test -s /tmp/Doxyfile && echo "Doxygen OK"
```

**Expected:** a version number and `Doxygen OK`.

### Graphviz

```bash
dot -V
echo 'digraph { a -> b }' | dot -Tsvg -o /tmp/graph.svg && test -s /tmp/graph.svg && echo "Graphviz OK"
```

**Expected:** a version and `Graphviz OK`.

## Docker-in-Docker uses elevated privileges

This environment runs its own Docker daemon inside the Dev Container, which requires the container to run in **privileged** mode. The `docker-in-docker` feature turns this on automatically.

A privileged container has far fewer isolation protections than a normal one. Software inside it, including anything you or Claude Code run, could affect the machine that hosts the container:

- **In Codespaces,** that machine is the virtual machine for your codespace.
- **With Docker Desktop,** that machine is Docker Desktop's Linux environment on your computer, and your project folder is mounted from your computer.

Because of this:

- Only run code and container images you trust.
- Do not start Claude Code with `--dangerously-skip-permissions` in this environment.
- Do not mount host secrets, such as `~/.ssh` or cloud credential folders, into the container.

Images you pull are stored in Docker volumes for this Dev Container, separate from your Docker Desktop images. A container you start here cannot be seen in the Docker Desktop dashboard.

## Sign in to Claude Code

Claude Code requires a paid Claude plan or an Anthropic Console account. The free Claude plan does not include it.

Run `claude` and follow the prompts. If no browser opens, or the browser shows a `localhost` error, copy the login URL from the terminal, sign in, and paste the code back into the terminal.

### Where your credentials are stored

Your sign-in is stored in a private Docker volume mounted at `~/.claude`. The volume is outside the repository, so Git cannot commit it, and it stays in place when the container is rebuilt.

To carry authentication across different codespaces, you can store `ANTHROPIC_API_KEY` or a token from `claude setup-token` as `CLAUDE_CODE_OAUTH_TOKEN` in your [personal Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces).

The repository's `.claude/` directory holds shared project skills and commands, and it stays tracked in Git. It is separate from `~/.claude` in your home directory, which holds your personal sign-in and settings.

## Keep credentials out of the repository

- Never put tokens, API keys, or passwords in `devcontainer.json`, `setup.sh`, or any other tracked file.
- Use the interactive sign-in or personal Codespaces secrets.
- Do not rely on `.gitignore` alone. It only protects files that match its patterns and have not already been committed.
- Before committing, run `git status` and `git diff --staged`, and check for anything sensitive.
- If you commit a credential, revoke it immediately. Deleting the file does not remove it from Git history.

To check whether a file is ignored:

```bash
git check-ignore -v .env
```

**Expected:** a line showing the `.gitignore` rule that matches `.env`.

## Existing `.claude/` and `openspec/` directories

Setup only reads these directories. It never creates or changes them.

To confirm that nothing changed, run this command. It should print nothing:

```bash
git status --short -- .claude openspec
```

Do not run `openspec init` or `openspec update` unless your instructor asks you to, because they can change these files.

## Rerun setup

```bash
bash .devcontainer/setup.sh
```

The script is safe to rerun. It skips anything already installed, repeats every check, and exits with an error if a check fails.

## Build and test the environment

Run the checklist after changing any file in `.devcontainer/`.

### Test locally

In VS Code, run **Dev Containers: Rebuild Container**, or use the [Dev Container CLI](https://github.com/devcontainers/cli):

```bash
npm install -g @devcontainers/cli
devcontainer up --workspace-folder . --remove-existing-container
devcontainer exec --workspace-folder . bash .devcontainer/setup.sh
```

### Test in Codespaces

A new codespace is built from what has been pushed, so test from a branch:

1. Push your branch.
2. Select that branch on the repository page, then select **Code > Codespaces > Create codespace on \<branch\>**.
3. Run **Codespaces: View Creation Log** and confirm that setup finished without errors.
4. To test later edits in the same codespace, run **Codespaces: Rebuild Container**.

### Checklist

- [ ] The creation log ends with `Setup complete`.
- [ ] Every section of [Validate each tool](#validate-each-tool) gives the expected result.
- [ ] Rerunning `bash .devcontainer/setup.sh` reports `Already installed` for Doxygen and Graphviz, OpenSpec, and Claude Code.
- [ ] The Claude Code panel opens, and `claude` starts in the terminal.
- [ ] After signing in and rebuilding the container, `claude` does not ask you to sign in again.
- [ ] `git status --short -- .claude openspec` prints nothing.
- [ ] `git status` shows no credential files.

## Change tool versions

- **OpenSpec:** change `OPENSPEC_VERSION` in `setup.sh`. Setup fails if it no longer matches the version that generated the skills, so regenerate them in a separate, reviewed change.
- **Node.js or Docker:** change the matching feature in `devcontainer.json`, then rebuild.
- **Doxygen or Graphviz:** add new apt packages to `APT_PACKAGES` in `setup.sh`.

## Privacy

OpenSpec normally collects anonymous usage statistics. This environment turns that off by setting `OPENSPEC_TELEMETRY=0` in `devcontainer.json`.

## Not included yet

Alloy and AWS tooling are not installed. They are covered in later exercises.

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `$'\r': command not found` or `pipefail: invalid option name` | An older clone has `setup.sh` with Windows line endings | Clone the repository again, and reopen it in the container |
| A tool is missing | Setup failed or stopped early | Run `bash .devcontainer/setup.sh` and read the first error |
| `EACCES` from `npm install -g` | npm's global directory is not writable | Do not use `sudo`. Rebuild the container, or add `--prefix ~/.local` to the command |
| `claude: command not found` | The terminal was opened before setup finished | Open a new terminal; if that fails, rerun setup |
| Claude Code asks you to sign in again | The volume was removed, or the codespace is new | Sign in again, or use a personal Codespaces secret |
| `Cannot connect to the Docker daemon` | The inner Docker service has not started | Wait a moment and retry; if it persists, rebuild the container |
| `docker run` reports `toomanyrequests` | Docker Hub is limiting anonymous downloads | Wait and retry, or run `docker login` with your own account |
| `.env` or a key file appears in `git status` | It does not match `.gitignore`, or it is already tracked | Do not commit it. Ask your instructor for help if it is already tracked |
| The container will not start locally | Docker Desktop is not running or is short on resources | Start Docker Desktop and allow it at least 4 GB of memory |
| `.claude/` or `openspec/` is missing | They are not on the branch you opened | Tell your instructor; do not run `openspec init` |
