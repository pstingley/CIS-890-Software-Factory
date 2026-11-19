# DOI-CIO Software Factory 1.0 — Docker build package

Patrick Stingley   patrick\_stingley@ios.doi.gov

This package distributes **build instructions, not the multi-gigabyte Docker image**. The build script uses the project's existing `Dockerfile.work` and `.devcontainer` configuration. It builds and verifies a local Docker image named `doi-cio-software-factory:1.0`.

## What to put in GitHub

Commit these two files to the **`work/doi-cio`** branch, at the repository root:

* `build-doi-cio-image.ps1`
* `DOI-CIO-BUILD-README.md`

The branch must also contain the **tested** versions of:

* `Dockerfile.work` (based on `doi-cio-base:1.0`)
* `.dockerignore`
* `.devcontainer/devcontainer.json`
* `.devcontainer/setup.sh`, `setup-advanced.sh`, and `verify-advanced.sh`
* Project source, including `tools/codeflow`

**Do not upload** a Docker `.tar` archive, account credentials, local virtual environments, or generated image layers to the Git repository. Review the tracked files and `.dockerignore` for sensitive material before distributing to users.

## Prerequisites

* Windows PowerShell 5.1 or newer
* Docker Desktop running with Linux containers
* Node.js (for `npx.cmd`)
* Git and an internet connection for the initial clone/build
* Ample free local disk space; the built image and Docker build cache can consume many GB
* Permission to install and use the included software in the destination environment

The GitLab address is intentionally not configured. Claude Code and Kiro CLI are installed without signing in or embedding credentials.

## Build from a new Windows checkout

Run each command in **Windows PowerShell**, not in a GitHub Codespace Bash terminal:

```powershell
git clone --branch work/doi-cio https://github.com/pstingley/CIS-890-Software-Factory.git DOI-CIO-Software-Factory
Set-Location .\\\\DOI-CIO-Software-Factory
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\\\build-doi-cio-image.ps1
```

The execution-policy bypass applies to this PowerShell invocation; review the script before running it. The script does not require administrator PowerShell privileges, though Docker Desktop and software installation may have their own requirements.

## Optional: export a portable archive

Prefer exporting locally first (not directly to a mapped network drive):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\\\build-doi-cio-image.ps1 -ExportPath 'C:\\\\Users\\\\cover\\\\Projects\\\\DOI-CIO-Software-Factory-1.0.tar'
```

It validates the archive exists and prints its size and SHA-256 hash. To overwrite an existing archive, pass `-ForceExport`.

After verifying the archive, copy it to the desired storage location (for example, `H:\\\\Docker-Archives`). Check the copied file's SHA-256 hash against the original. Keep archives outside the Git repository.

## Use an existing archive at work

```powershell
docker load -i 'DOI-CIO-Software-Factory-1.0.tar'
docker run --rm -it doi-cio-software-factory:1.0
```

The `--rm` example is ephemeral; mount a writable workspace for any development work that must persist. This image offers a command-line container, **not** a self-hosted browser-based Codespaces service. Desktop VS Code can be configured to attach to a running container.

## Scope and limitations

* The script builds the **`work/doi-cio`** version, not the student `advanced` branch.
* It includes the Basic and Advanced setup scripts, CodeFlow, OpenSpec, Claude Code, and Kiro, as specified by the existing Dockerfile. It verifies installed tools; it does **not** certify CodeFlow's planned PHP semantic analysis or automatic PHP-to-Python/Rust migration.
* GitHub/GitLab integration still needs user-specific authentication and the relevant server address. Do not bake credentials into the Docker image.
* Docker's use of cached layers may speed up repeat builds. Third-party downloads can change; this is a build recipe, not a guarantee of byte-for-byte identical output.
* Follow DOI's security, licensing, software approval, and data-handling requirements before installation or distribution.

