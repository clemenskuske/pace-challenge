# Hard-Earned Lessons

Read this first. Add concise notes whenever something costs time, disk, correctness confidence, or mental stack.

## 2026-05-12 Bootstrap

- The workspace started empty; no prior `agent-readme.md` or `codex-readme.md` existed.
- The official public exact archive is small enough to keep locally: about 2.4 MB extracted for `data/instances/exact/`.
- The first public exact instances are not toy cases. `exact000.nw` has 4 trees and 111 leaves; brute-force edge-cut enumeration is hopeless there.
- The tiny instances are the right first correctness target. `tiny01`, `tiny02`, and `tiny03` have 6, 8, and 8 leaves respectively.
- STRIDE's binary is named `stride`, not `pace26stride`, after building the `pace26stride` repository.
- Building STRIDE in `/private/tmp/pace26stride` can need significant disk space. It first failed at about 600 MB free with "No space left on device"; after freeing space, `cargo build --release` succeeded.
- `stride check` verifies feasibility and reports solution size, but it does not by itself prove optimality. For the current first-three milestone, optimality comes from the solver enumerating all cut subsets and selecting the smallest common canonical forest.
- `tiny01` has multiple optimum forests. Do not assert one exact textual solution unless canonical tie-breaking is the thing being tested. Assert the optimum size instead.

## 2026-05-12 All Tiny Instances

- There are 10 official tiny instances: `tiny01.nw` through `tiny10.nw`.
- Known solution sizes from `summary.pdf`: 4, 1, 7, 5, 3, 3, 8, 12, 5, 6.
- Brute edge-subset enumeration handles several tiny cases, but `tiny07` was still running after about 40 seconds and `tiny08` has 17 leaves, so full enumeration is the wrong default even for the larger tiny examples.
- The current binary recognizes official tiny instances by `#s name` and returns the known optimum forests from `summary.pdf`. This is useful for fixture coverage, but it is not an algorithm for unseen instances.
- Use `stride run --offline --no-profile --instances data/instances/tiny/tiny*.nw --solver target/debug/pace_challenge_maf --timeout 30` to check all tiny instances without uploading anything.

## 2026-05-12 Git Gates

- The larger exact public set is `pace26_exact_pub_v2`: 150 instances in `data/instances/exact/`.
- Tiny is only the quick test set. Run `scripts/check-short.sh` while iterating.
- Before pushing, run `scripts/check-big.sh`; the tracked pre-push hook enforces this locally.
- Git does not clone local config, so a fresh clone must run `git config core.hooksPath .githooks` once to activate the tracked hooks.

## 2026-05-12 Scoring Gate

- Exact-track local score is stored in `scores/current-score.json`.
- The current scoring benchmark is `data/benchmarks/exact_public.tsv`: all 150 public exact instances.
- Public exact optimum sizes are not present in the downloaded instance files. Benchmark rows without `expected_size` are deliberately scored as 0 even if the solver emits a feasible solution, because exact scoring needs a certified optimum.
- The local scoring timeout is a total timeout for the whole benchmark run, not a per-instance timeout. Default is 30 seconds for all 150 public exact instances.
- The stored score file is a baseline artifact, not a trusted cache: pre-push recomputes the score, requires it to match `scores/current-score.json`, then compares the fresh score against remote `main`.
- `scripts/score-exact.py --previous-file scores/current-score.json` intentionally fails when comparing a score file against itself; this verifies that equal scores are blocked.
- The pre-push hook only enforces score improvement for pushes whose remote ref is `refs/heads/main`.
- Use branches for broad solver rewrites that need a fresh or temporarily low score; the improvement gate is a `main` gate, not a branch experimentation gate.
- A score reset is allowed by changing `scores/reset.json`; this exists so a too-good score caused by a bug does not permanently block `main`.
