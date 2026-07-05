#!/bin/zsh
# Sequential swegen create over the 4 selected hard PRs.
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
set -a; source .env; set +a
export GITHUB_TOKEN=$(gh auth token)
mkdir -p tasks logs

run() {
  local repo=$1 pr=$2
  local slug=${repo//\//__}
  echo "=== $(date '+%H:%M:%S') START $repo #$pr ==="
  swegen create --repo "$repo" --pr "$pr" --output tasks --state-dir .swegen -v \
    > "logs/${slug}-${pr}.log" 2>&1
  echo "=== $(date '+%H:%M:%S') DONE $repo #$pr (exit $?) ==="
}

run sqlfluff/sqlfluff 7604
run sqlfluff/sqlfluff 7578
run pymc-devs/pymc 7380
run pymc-devs/pymc 8047

echo "=== BATCH COMPLETE ==="
ls -la tasks/ 2>/dev/null
