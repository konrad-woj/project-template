#!/bin/sh
# Vendors shared Claude Code skills from the skillset repo into .claude/skills/.
#
# .claude/skills/ is gitignored: skills are owned by the skillset repo, never
# copy-pasted into this one. Re-run this after cloning and whenever skillset
# changes.
#
# Example usage: sh sync_skills.sh                       # sync every skill
#                sh sync_skills.sh feature-coder code-reviewer   # sync a subset

set -e

SKILLSET_REPO="${SKILLSET_REPO:-https://github.com/konrad-woj/skillset.git}"
SKILLSET_REF="${SKILLSET_REF:-main}"
REPO_ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
TARGET_DIR="$REPO_ROOT/.claude/skills"
CHECKOUT_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$CHECKOUT_DIR"
}
trap cleanup EXIT

echo "Fetching $SKILLSET_REPO@$SKILLSET_REF"
git clone --depth 1 --branch "$SKILLSET_REF" "$SKILLSET_REPO" "$CHECKOUT_DIR/skillset" >/dev/null 2>&1 || {
  echo "Could not clone $SKILLSET_REPO. Check network access and repo permissions." >&2
  exit 1
}

SOURCE_DIR="$CHECKOUT_DIR/skillset"
if [ -d "$SOURCE_DIR/skills" ]; then
  SOURCE_DIR="$SOURCE_DIR/skills"
fi

mkdir -p "$TARGET_DIR"

if [ "$#" -eq 0 ]; then
  set -- $(cd "$SOURCE_DIR" && ls -d */ 2>/dev/null | sed 's#/##')
fi

if [ "$#" -eq 0 ]; then
  echo "No skills found in $SKILLSET_REPO." >&2
  exit 1
fi

for skill in "$@"; do
  if [ ! -f "$SOURCE_DIR/$skill/SKILL.md" ]; then
    echo "Skipping '$skill': no SKILL.md in the skillset repo." >&2
    continue
  fi
  rm -rf "$TARGET_DIR/$skill"
  cp -R "$SOURCE_DIR/$skill" "$TARGET_DIR/$skill"
  echo "Synced $skill"
done

echo "Skills are in .claude/skills/ (gitignored). Re-run this script to update."
