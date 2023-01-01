# 220604
param()

# This script file cannot be run directly, you should "source" it into current shell.
if (-not $($MyInvocation.Line.StartsWith(". "))) {
    Write-Host "Usage: . $($MyInvocation.InvocationName)"
    exit 1
}

if ($env:VIRTUAL_ENV) {
    Write-Host "already in virtualenv ${env:VIRTUAL_ENV}"
    return
}

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

$venvCandidates = @(
    "$PSScriptRoot/venv/",
    "$PSScriptRoot/.venv/",
    "$PSScriptRoot/../venv/",
    "$PSScriptRoot/../.venv/",
    "$HOME/.local/venv/",
    "$HOME/.venv/"
)

foreach ($venvPath in $venvCandidates) {
    $path = Join-Path $venvPath "./Scripts/Activate.ps1"
    if (Test-Path $path) {
        . $path
        return
    }
}
Write-Error "Failed to source Activate.ps1"
