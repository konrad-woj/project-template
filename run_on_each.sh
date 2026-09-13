#!/bin/sh
# Runs a command inside every packages/*/ directory.
#
# Example usage: sh run_on_each.sh "uv sync"                  # continue past failures
#                sh run_on_each.sh -b "uv run task precommits"  # stop at first failure
#
# Exits non-zero if the command failed in any package, so it is usable as a CI gate.

BREAK_ON_ERROR=0
if [ "$1" = "-b" ]; then
  BREAK_ON_ERROR=1
  shift
fi

if [ -z "$1" ]; then
  echo "Usage: $0 [-b] <command>" >&2
  exit 2
fi

COMMAND="$1"
FAILED=""

for dir in ./packages/*/; do
  [ -d "$dir" ] || continue
  echo "Running '$COMMAND' in $dir"
  if (cd "$dir" && sh -c "$COMMAND"); then
    continue
  fi
  FAILED="$FAILED $dir"
  if [ "$BREAK_ON_ERROR" -eq 1 ]; then
    echo "Command failed in $dir, stopping." >&2
    break
  fi
  echo "Command failed in $dir, continuing..." >&2
done

if [ -n "$FAILED" ]; then
  echo "FAILED in:$FAILED" >&2
  exit 1
fi
