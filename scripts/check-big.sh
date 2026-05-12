#!/usr/bin/env sh
set -eu

cd "$(git rev-parse --show-toplevel)"

cargo test
cargo test -- --ignored parses_all_public_exact_instances

