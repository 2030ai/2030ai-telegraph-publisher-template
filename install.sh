#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p ~/.claude/telegraph ~/.claude/skills/telegraph

cp "$SCRIPT_DIR/publish.py" ~/.claude/telegraph/publish.py
cp "$SCRIPT_DIR/.claude/skills/telegraph/skill.md" ~/.claude/skills/telegraph/skill.md

echo "✓ Installed telegraph-publisher to ~/.claude/"
echo ""
echo "Test it:"
echo "  echo 'Hello Telegraph!' | python3 ~/.claude/telegraph/publish.py create --title 'Test' --format text"
echo ""
echo "In Claude Code, say: 'опубликуй на телеграф' or 'publish to telegraph'"
