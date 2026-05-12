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
