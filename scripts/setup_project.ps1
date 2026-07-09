param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TargetPath
)

$ErrorActionPreference = "Stop"
$source = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "Android AI Agent - Project Setup"
Write-Host "================================="
Write-Host "Source: $source"
Write-Host "Target: $TargetPath"
Write-Host ""

if (-not (Test-Path $TargetPath)) {
    Write-Host "ERROR: Target path does not exist: $TargetPath"
    exit 1
}

Write-Host "[1/5] Copying core config files..."
Copy-Item -Path "$source\opencode.json" -Destination $TargetPath -Force
Copy-Item -Path "$source\AGENTS.md" -Destination $TargetPath -Force
Write-Host "  OK: opencode.json"
Write-Host "  OK: AGENTS.md"

Write-Host "[2/5] Copying .opencode/ (agents, rules, memory)..."
Copy-Item -Path "$source\.opencode" -Destination $TargetPath -Recurse -Force
Write-Host "  OK: .opencode/agents/ (11 agents)"
Write-Host "  OK: .opencode/rules/ (TESTING.md, ARCHITECTURE.md)"
Write-Host "  OK: .opencode/skills/ (16 reusable skill files)"
Write-Host "  OK: .opencode/memory/ (6 memory types)"

Write-Host "[3/5] Copying helper scripts (doc watcher + screenshot extractor)..."
New-Item -ItemType Directory -Path "$TargetPath\scripts" -Force | Out-Null
Copy-Item -Path "$source\scripts\doc_watcher.py" -Destination "$TargetPath\scripts\" -Force
Copy-Item -Path "$source\scripts\screenshot_to_ui.py" -Destination "$TargetPath\scripts\" -Force
Copy-Item -Path "$source\scripts\requirements-docwatcher.txt" -Destination "$TargetPath\scripts\" -Force
Write-Host "  OK: scripts/doc_watcher.py (for @doc-reader)"
Write-Host "  OK: scripts/screenshot_to_ui.py (for @ui-builder)"
Write-Host "  OK: scripts/requirements-docwatcher.txt"

Write-Host "[4/5] Creating docs folders..."
New-Item -ItemType Directory -Path "$TargetPath\docs\input" -Force | Out-Null
New-Item -ItemType Directory -Path "$TargetPath\docs\parsed" -Force | Out-Null
Write-Host "  OK: docs/input/"
Write-Host "  OK: docs/parsed/"

Write-Host "[5/5] Copying agent.gitignore..."
Copy-Item -Path "$source\scripts\agent.gitignore" -Destination "$TargetPath\agent.gitignore" -Force
Write-Host "  OK: agent.gitignore"

Write-Host ""
Write-Host "================================="
Write-Host "DONE! Setup complete."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Add agent.gitignore entries to your .gitignore:"
Write-Host "     Get-Content $TargetPath\agent.gitignore | Add-Content $TargetPath\.gitignore"
Write-Host "     Remove-Item $TargetPath\agent.gitignore"
Write-Host "  2. Run: @memory-manager update-index (to index your project)"
Write-Host "  3. (One-time) pip install pymupdf4llm python-docx watchdog requests Pillow"
Write-Host ""
