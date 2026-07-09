param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TargetPath
)

$ErrorActionPreference = "Stop"
$source = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "Android AI Agent - Sync to Project"
Write-Host "===================================="
Write-Host "Source: $source"
Write-Host "Target: $TargetPath"
Write-Host ""

if (-not (Test-Path $TargetPath)) {
    Write-Host "ERROR: Target path does not exist: $TargetPath"
    exit 1
}

# Sync core config
Copy-Item -Path "$source\opencode.json" -Destination $TargetPath -Force
Copy-Item -Path "$source\AGENTS.md" -Destination $TargetPath -Force
Write-Host "  OK: opencode.json"
Write-Host "  OK: AGENTS.md"

# Sync agents (the prompt files)
Copy-Item -Path "$source\.opencode\agents\*" -Destination "$TargetPath\.opencode\agents\" -Force
Write-Host "  OK: .opencode/agents/ (all agent prompts)"

# Sync rules
Copy-Item -Path "$source\.opencode\rules\*" -Destination "$TargetPath\.opencode\rules\" -Force
Write-Host "  OK: .opencode/rules/"

# Sync skills
Copy-Item -Path "$source\.opencode\skills\*" -Destination "$TargetPath\.opencode\skills\" -Force
Write-Host "  OK: .opencode/skills/"

# Sync memory (calibration, patterns, etc.) — but NOT plans or goals (those are project-specific)
Copy-Item -Path "$source\.opencode\memory\parametric\*" -Destination "$TargetPath\.opencode\memory\parametric\" -Force
Copy-Item -Path "$source\.opencode\memory\procedural\*" -Destination "$TargetPath\.opencode\memory\procedural\" -Force
Write-Host "  OK: .opencode/memory/parametric/ (calibration)"
Write-Host "  OK: .opencode/memory/procedural/ (learned patterns)"

Write-Host ""
Write-Host "===================================="
Write-Host "SYNC DONE. Restart OpenCode to pick up changes."
Write-Host ""
