#requires -Version 5.1
<#
.SYNOPSIS
    Build and verify the DOI-CIO Software Factory 1.0 Docker image.
.DESCRIPTION
    Run from the work/doi-cio checkout on Windows with Docker Desktop (Linux engine)
    and Node.js. Uses existing .devcontainer/devcontainer.json and Dockerfile.work.
    Does not embed credentials or upload an image to GitHub.
.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-doi-cio-image.ps1
.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-doi-cio-image.ps1 -ExportPath 'C:\Users\cover\Projects\DOI-CIO-Software-Factory-1.0.tar'
#>
[CmdletBinding()]
param(
    [string]$ExportPath,
    [switch]$ForceExport
)

$ErrorActionPreference = 'Stop'
$BaseImage = 'doi-cio-base:1.0'
$FinalImage = 'doi-cio-software-factory:1.0'

function Invoke-CheckedCommand {
    param([string]$Description, [scriptblock]$Command)
    Write-Host "`n==> $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed (exit code $LASTEXITCODE)."
    }
}

try {
    if (-not $PSScriptRoot) { throw 'This script must be saved as a .ps1 file before execution.' }
    Push-Location -LiteralPath $PSScriptRoot
    try {
        foreach ($path in @('Dockerfile.work', '.dockerignore', '.devcontainer/devcontainer.json', '.devcontainer/setup.sh', '.devcontainer/setup-advanced.sh', '.devcontainer/verify-advanced.sh')) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
                throw "Required repository file not found: $path"
            }
        }

        if (-not (Get-Command 'docker.exe' -ErrorAction SilentlyContinue)) {
            throw 'Docker CLI was not found. Install and start Docker Desktop.'
        }
        if (-not (Get-Command 'npx.cmd' -ErrorAction SilentlyContinue)) {
            throw 'npx.cmd was not found. Install Node.js for Windows.'
        }

        # Refuse to build student/other branches as the DOI-CIO work image.
        if (Get-Command 'git.exe' -ErrorAction SilentlyContinue) {
            $insideRepo = (& git.exe rev-parse --is-inside-work-tree 2>$null)
            if ($LASTEXITCODE -eq 0 -and $insideRepo -eq 'true') {
                $branch = (& git.exe branch --show-current).Trim()
                if ($branch -ne 'work/doi-cio') {
                    throw "Expected branch 'work/doi-cio'; found '$branch'. Switch to the DOI-CIO work branch first."
                }
                Write-Host "Source branch: $branch"
                Write-Host "Source commit: $(& git.exe rev-parse --short HEAD)"
                $status = & git.exe status --short
                if ($status) {
                    Write-Warning 'The repository has uncommitted or untracked files. Review the build context and .dockerignore for secrets before distributing.'
                    $status | ForEach-Object { Write-Host "  $_" }
                }
            }
        }

        $engine = (& docker.exe info --format '{{.OSType}}' 2>&1)
        if ($LASTEXITCODE -ne 0) { throw "Docker Desktop is not responding: $engine" }
        if (($engine | Out-String).Trim() -ne 'linux') {
            throw 'Docker is not using Linux containers. Switch Docker Desktop to Linux containers.'
        }
        Write-Host "Docker engine: linux"
        Write-Host 'Review .dockerignore and repository files before distribution; filename exclusions do not guarantee that all secrets are excluded.' -ForegroundColor Yellow

        Invoke-CheckedCommand 'Build Dev Containers base image' {
            & npx.cmd --yes '@devcontainers/cli' build --workspace-folder . --image-name $BaseImage
        }
        Invoke-CheckedCommand 'Build complete DOI-CIO Software Factory image' {
            & docker.exe build --progress=plain -f Dockerfile.work -t $FinalImage .
        }
        Invoke-CheckedCommand 'Verify Advanced Software Factory tools in final image' {
            & docker.exe run --rm $FinalImage bash -lc 'bash .devcontainer/verify-advanced.sh'
        }
        Invoke-CheckedCommand 'Verify OpenSpec, Claude Code, and Kiro CLI' {
            & docker.exe run --rm $FinalImage bash -c 'openspec --version && claude --version && kiro-cli --version'
        }

        if ($ExportPath) {
            $archive = [System.IO.Path]::GetFullPath($ExportPath)
            $parent = Split-Path -Path $archive -Parent
            if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
                New-Item -ItemType Directory -Force -Path $parent | Out-Null
            }
            if ((Test-Path -LiteralPath $archive) -and (-not $ForceExport)) {
                throw "Archive already exists: $archive. Use -ForceExport to overwrite it."
            }
            Invoke-CheckedCommand "Save Docker archive to $archive" {
                & docker.exe save -o $archive $FinalImage
            }
            if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
                throw "Docker reported success, but archive is missing: $archive"
            }
            $saved = Get-Item -LiteralPath $archive
            if ($saved.Length -le 0) { throw "Docker archive is empty: $archive" }
            Write-Host ("Archive: {0} ({1:N2} GB)" -f $archive, ($saved.Length / 1GB)) -ForegroundColor Green
            Write-Host 'SHA-256 checksum:'
            Get-FileHash -LiteralPath $archive -Algorithm SHA256 | Format-List Algorithm,Hash,Path
        }

        Write-Host "`nSUCCESS: $FinalImage is built and verified." -ForegroundColor Green
        if (-not $ExportPath) {
            Write-Host 'To make an offline archive, rerun this script with -ExportPath <path-to-tar>.'
        }
    }
    finally { Pop-Location }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
