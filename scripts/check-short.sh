#!/usr/bin/env sh
set -eu

cd "$(git rev-parse --show-toplevel)"

cargo test
scripts/score-exact.py --self-test
