#!/bin/sh
# Bootstraps a clone of this template into a new named project.
#
# Automates the deterministic identity rename (README, package.json name) and
# flags package descriptions that still say "template". Everything else in
# the "Quick start" section of README.md needs a judgment call (which
# reference packages to keep, which env vars/Dockerfiles/skills to set up)
# and is printed as a checklist at the end instead of being scripted here.
#
# Example usage: sh bootstrap.sh my-new-project

set -e

PROJECT_NAME="$1"
if [ -z "$PROJECT_NAME" ]; then
  echo "Usage: $0 <project-name>" >&2
  exit 2
fi

REPO_ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
cd "$REPO_ROOT"

if [ -f README_TEMPLATE.md ]; then
  mv README_TEMPLATE.md README.md
  echo "Renamed README_TEMPLATE.md -> README.md (fill in TL;DR/TOC/Installation/Usage)"
else
  echo "README_TEMPLATE.md not found, skipping (already renamed?)"
fi

if [ -f package.json ]; then
  tmp="$(mktemp)"
  sed 's/"name": *"project-template"/"name": "'"$PROJECT_NAME"'"/' package.json > "$tmp"
  mv "$tmp" package.json
  echo "Set package.json name -> $PROJECT_NAME"
fi

for pyproject in packages/*/pyproject.toml; do
  [ -f "$pyproject" ] || continue
  if grep -qi "template" "$pyproject"; then
    echo "NOTE: $pyproject still mentions 'template' - update its description manually."
  fi
done

cat <<EOF

Mechanical rename done. Remaining steps (see README.md "Quick start"):
  - Decide what to do with packages/data-utils, example-library, example-service
    (keep data-utils, copy the library/service shape, delete once unneeded)
  - Copy packages/pyproject.toml.example + tach.toml.example for each new package
  - Copy Dockerfile.example -> Dockerfile.{package_name} for deployable services
  - Copy .env.example -> .env (repo root + any package that needs its own keys)
  - sh sync_skills.sh [skill ...]
  - npx openwiki --init
  - Copy docs/DESIGN_DOC_TEMPLATE.md -> {FEATURE_NAME}.md before the first feature
  - Verify: sh run_on_each.sh -b "uv sync --all-groups" && sh run_on_each.sh -b "uv run task ci"
EOF
