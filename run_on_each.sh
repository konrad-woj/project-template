# Example usage: ./run_on_each.sh "uv sync"         # continues on error
#                ./run_on_each.sh -b "uv sync"      # break on error

# Check if the -b flag is present
BREAK_ON_ERROR=0
if [ "$1" = "-b" ]; then
  BREAK_ON_ERROR=1
  shift
fi

# Check if a command is provided
if [ -z "$1" ]; then
  echo "Usage: $0 [-b] <command>"
  exit 1
fi

for dir in ./*/; do
  if [ -d "$dir" ]; then
    echo "Running '$1' in $dir"
    if [ "$BREAK_ON_ERROR" -eq 1 ]; then
      (cd "$dir" && $1) || break
    else
      (cd "$dir" && $1) || echo "Command failed in $dir, continuing..."
    fi
  fi
done
