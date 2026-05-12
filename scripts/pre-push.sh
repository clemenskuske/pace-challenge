#!/usr/bin/env sh
set -eu

cd "$(git rev-parse --show-toplevel)"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

main_pushes="$tmp_dir/main-pushes"
touch "$main_pushes"

while read local_ref local_sha remote_ref remote_sha
do
  if [ "$remote_ref" = "refs/heads/main" ] && [ "$local_sha" != "0000000000000000000000000000000000000000" ]; then
    printf '%s %s %s %s\n' "$local_ref" "$local_sha" "$remote_ref" "$remote_sha" >> "$main_pushes"
  fi
done

scripts/check-big.sh

if [ ! -s "$main_pushes" ]; then
  exit 0
fi

computed="$tmp_dir/current-score.json"
scripts/score-exact.py --write "$computed" --check-file scores/current-score.json

while read local_ref local_sha remote_ref remote_sha
do
  if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
    continue
  fi

  previous="$tmp_dir/previous-score.json"
  if git show "$remote_sha:scores/current-score.json" > "$previous" 2>/dev/null; then
    scripts/score-exact.py --previous-file "$previous"
  fi
done < "$main_pushes"
