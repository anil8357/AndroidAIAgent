#!/bin/bash
# setup_project.sh — Copy AI Agent config to a target Android project
# Usage: ./scripts/setup_project.sh /path/to/your/android/project

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: ./scripts/setup_project.sh <target_path>"
    exit 1
fi

TARGET="$1"
SOURCE="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "🤖 Android AI Agent — Project Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Source: $SOURCE"
echo "Target: $TARGET"
echo ""

# Validate target exists
if [ ! -d "$TARGET" ]; then
    echo "❌ Target path does not exist: $TARGET"
    exit 1
fi

# Step 1: Core config files
echo "📋 Copying core config files..."
cp "$SOURCE/opencode.json" "$TARGET/"
cp "$SOURCE/AGENTS.md" "$TARGET/"
echo "   ✅ opencode.json"
echo "   ✅ AGENTS.md"

# Step 2: .opencode directory (agents + rules + memory)
echo "📋 Copying .opencode/ (agents, rules, memory)..."
cp -r "$SOURCE/.opencode" "$TARGET/"
echo "   ✅ .opencode/agents/ (11 agents)"
echo "   ✅ .opencode/rules/ (TESTING.md, ARCHITECTURE.md)"
echo "   ✅ .opencode/skills/ (16 reusable skill files)"
echo "   ✅ .opencode/memory/ (6 memory types)"

# Step 3: Helper scripts (doc watcher + screenshot→UI extractor)
echo "📋 Copying helper scripts..."
mkdir -p "$TARGET/scripts"
cp "$SOURCE/scripts/doc_watcher.py" "$TARGET/scripts/"
cp "$SOURCE/scripts/screenshot_to_ui.py" "$TARGET/scripts/"
cp "$SOURCE/scripts/requirements-docwatcher.txt" "$TARGET/scripts/"
echo "   ✅ scripts/doc_watcher.py (for @doc-reader)"
echo "   ✅ scripts/screenshot_to_ui.py (for @ui-builder)"
echo "   ✅ scripts/requirements-docwatcher.txt"

# Step 4: Docs folders
echo "📋 Creating docs folders..."
mkdir -p "$TARGET/docs/input" "$TARGET/docs/parsed"
echo "   ✅ docs/input/"
echo "   ✅ docs/parsed/"

# Step 5: .gitignore for agent files
echo "📋 Copying agent .gitignore..."
cp "$SOURCE/scripts/agent.gitignore" "$TARGET/agent.gitignore"
echo "   ✅ agent.gitignore (merge into your .gitignore)"

# Done
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Merge agent.gitignore into your project's .gitignore"
echo "  2. Run: @memory-manager update-index (to index your project)"
echo "  3. (One-time) pip install pymupdf4llm python-docx watchdog requests Pillow"
echo ""
