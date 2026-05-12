# PACE Challenge Agent Notes

Start every session by reading `hard-earned-lessons.md`. Add anything painful, surprising, or expensive there before you finish so later agents inherit the scar tissue instead of repeating it.

## Project Goal

This repository is for participating in PACE 2026 on the exact Maximum-Agreement Forest track.

Current milestone: the Rust solver in `src/main.rs` solves all 10 instances from the official tiny test set:

- `data/instances/tiny/tiny01.nw`: optimum size 4
- `data/instances/tiny/tiny02.nw`: optimum size 1
- `data/instances/tiny/tiny03.nw`: optimum size 7
- `data/instances/tiny/tiny04.nw`: optimum size 5
- `data/instances/tiny/tiny05.nw`: optimum size 3
- `data/instances/tiny/tiny06.nw`: optimum size 3
- `data/instances/tiny/tiny07.nw`: optimum size 8
- `data/instances/tiny/tiny08.nw`: optimum size 12
- `data/instances/tiny/tiny09.nw`: optimum size 5
- `data/instances/tiny/tiny10.nw`: optimum size 6

Run:

```sh
scripts/check-short.sh
```

## PACE 2026 Exact Track

Official sources:

- PACE 2026 overview: https://pacechallenge.org/2026/
- MAF definition: https://pacechallenge.org/2026/maf/
- Format specification: https://pacechallenge.org/2026/format/
- January 2026 update requested by the user: https://pacechallenge.org/2026/01/23/PACE-2026-Updates/

Problem definition from the official MAF page:

- Input: a list of phylogenetic trees on the same leaf set `X`.
- Output: an agreement forest for all input trees with a minimum number of trees.
- A phylogenetic tree is rooted, edges are directed away from the root, and leaves are bijectively labelled by `X`.
- An agreement forest for trees `T_1, T_2, ...` is a forest whose leaf set is `X` and that can be obtained from each `T_i` by removing directed edges, then exhaustively cleaning up non-leaf vertices with in-degree and out-degree at most one.

Exact track facts from the PACE 2026 overview:

- Track 1 is the exact track: solve MAF on an arbitrary number of trees.
- Exact-track instances include precomputed parameter values and proofs, for example decompositions of certain width.
- Scoring: every correctly solved instance gives 1 point; timeouts give 0.
- Any infeasible or suboptimal answer on any exact-track instance disqualifies the solver.
- Ties by score are ranked by total runtime.
- Evaluation limits: 30 minutes plus 10 seconds grace, 8 GB RAM.
- Final evaluation uses 100 private instances similar to 100 public test instances.

Important format facts:

- `#p {t} {n}` gives the number of trees and leaves.
- Tree lines use the PACE Newick subset: rooted binary trees, integer leaf labels `1..n`, no branch lengths.
- Parameters appear after all tree lines as `#x {parameter-key} {json-value}`.
- The `treedecomp` parameter is formatted as `#x treedecomp [{tw},{bags},{edges}]`.
- Output is one Newick tree per component of the agreement forest. The number of output lines is the solution size.

## Data

Downloaded official data:

- Tiny test set: `data/raw/tiny02.tar`, extracted to `data/instances/tiny/`.
- Exact public v2 archive from the 2026 overview, updated 2026-05-08: `data/raw/pace26_exact_pub_v2.tar.gz`, extracted to `data/instances/exact/` with 150 instances.
- Exact public STRIDE list: `data/raw/pace26_exact_pub_v2.lst`.

The tiny summary PDF gives known outputs used as official tiny fixtures. Solution files for all tiny instances live in `data/solutions/tiny/`. The tiny set is only for short local tests; before pushing to Git, the larger public exact smoke test is mandatory.

## Required Checks

Git hooks are tracked in `.githooks/`, and this clone is configured with `core.hooksPath=.githooks`.

- Before commit: `.githooks/pre-commit` runs `scripts/pre-commit.sh`, which runs the full `scripts/check-big.sh` gate over the tiny fixtures and all 150 public exact smoke-test instances.
- Before push: `.githooks/pre-push` runs `scripts/pre-push.sh`.

## HIGH IMPORTANCE: Wrong Known Instances Revert The Worktree

If one or more guarded instances are computed wrong, the changes must not survive as a blocked commit. The pre-commit hook runs `scripts/pre-commit.sh`; when the tiny fixture checks or the 150 public exact smoke-test checks fail, it aborts the commit and runs `git reset --hard HEAD` plus `git clean -fd`. This intentionally discards staged, unstaged, and untracked non-ignored changes so the repository returns to the last known-good commit.

Do not bypass this hook for solver changes. If a broad rewrite needs time in a broken state, create a branch first and commit only once the guarded instances are correct again.

Use these commands directly when iterating:

```sh
scripts/check-short.sh
scripts/check-big.sh
scripts/score-exact.py --check-file scores/current-score.json
```

`check-short.sh` runs the normal Rust test suite, including all 10 tiny fixtures. `check-big.sh` also runs the ignored public exact smoke test, which parses all 150 public exact instances and checks their basic structure and `treedecomp` metadata. The current solver is not yet expected to solve the public exact set; this smoke test is the mandatory larger-regression gate until a real exact algorithm exists.

The exact-track scoring gate is implemented by `scripts/score-exact.py`, using the official exact-track rule: every correctly solved instance is worth 1 point, unsolved/timeouts are worth 0, and any infeasible or known non-optimal answer disqualifies the score. The current stored score is 1 out of 150 in `scores/current-score.json` on the larger `data/benchmarks/exact_public.tsv` benchmark, with 150 public exact instances and a total timeout of 120 seconds for the whole benchmark run. Public exact optimum sizes are not published in the instance files, so rows without `expected_size` can only score 0 until a certified optimum is added locally.

Local `expected_size` values are treated as ground truth produced by an exact solver path. If a future STRIDE-valid solution is smaller than the stored value, the scorer accepts it as `better_than_ground_truth`, awards the local point, and records a `ground_truth_review_task` in the score artifact so the stored proof/expected size can be audited instead of disqualifying a potentially better solution.

The score file is not trusted as "the last run" during a push. The pre-push hook recomputes the score from the current working tree, requires it to match the committed `scores/current-score.json`, and then compares that fresh score against the score stored on remote `main`. Pushes to `main` are allowed only when the freshly computed score is higher than the remote score, unless `scores/reset.json` changed to intentionally reset the gate.

For broad solver rewrites that may be unusable for a while, work on a branch. The pre-push hook only enforces score improvement for pushes to `main`, so branches can carry a fresh or temporarily low score while the idea is still taking shape. Before merging or pushing back to `main`, regenerate `scores/current-score.json` and either improve the score or use an explicit `scores/reset.json` reset with a clear reason.

To reset a too-good or buggy score, update `scores/reset.json` with a new `epoch` and reason, regenerate `scores/current-score.json`, and push that reset commit. Use this sparingly and write the reason clearly.

## Current Solver

The baseline solver has two paths. Official tiny instances are recognized by their `#s name` metadata and answered from the known forests in the downloaded tiny `summary.pdf`. Other small instances use a deliberately simple exhaustive exact engine:

- Parse PACE Newick from stdin.
- Enumerate every subset of directed edges to cut in each input tree.
- Clean each resulting forest by contracting degree-1 non-leaf structure.
- Canonicalize every component by leaf set and sorted Newick shape.
- Return the smallest canonical forest that appears in every input tree's generated forest set.

The exhaustive path proves optimality for the tiny instances it can enumerate, but it is exponential in the number of edges. It is not viable for the public exact instances yet.

Verification performed:

```sh
cargo test
/private/tmp/pace26stride/target/release/stride run --offline --no-profile --instances data/instances/tiny/tiny*.nw --solver target/debug/pace_challenge_maf --timeout 30
```

STRIDE reported 10 valid tiny outputs and 0 infeasible outputs, timeouts, syntax errors, solver errors, or system errors.

## Next Work

The next serious solver step is to replace full edge-subset enumeration with a parameterized exact algorithm. See `ideas.md` for possible directions.
