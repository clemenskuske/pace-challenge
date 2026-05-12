# PACE Challenge Agent Notes

Start every session by reading `hard-earned-lessons.md`. Add anything painful, surprising, or expensive there before you finish so later agents inherit the scar tissue instead of repeating it.

## Project Goal

This repository is for participating in PACE 2026 on the exact Maximum-Agreement Forest track.

Current milestone: the Rust solver in `src/main.rs` exactly solves the first three tiny instances from the official tiny test set:

- `data/instances/tiny/tiny01.nw`: optimum size 4
- `data/instances/tiny/tiny02.nw`: optimum size 1
- `data/instances/tiny/tiny03.nw`: optimum size 7

Run:

```sh
cargo test
target/debug/pace_challenge_maf < data/instances/tiny/tiny01.nw
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
- Exact public v2 archive from the 2026 overview, updated 2026-05-08: `data/raw/pace26_exact_pub_v2.tar.gz`, extracted to `data/instances/exact/`.
- Exact public STRIDE list: `data/raw/pace26_exact_pub_v2.lst`.

The tiny summary PDF gives feasible known outputs. The first three sizes match the current exhaustive solver.

## Current Solver

The baseline solver is intentionally small and exact for tiny instances:

1. Parse PACE Newick from stdin.
2. Enumerate every subset of directed edges to cut in each input tree.
3. Clean each resulting forest by contracting degree-1 non-leaf structure.
4. Canonicalize every component by leaf set and sorted Newick shape.
5. Return the smallest canonical forest that appears in every input tree's generated forest set.

This proves optimality for the tiny instances it can enumerate, but it is exponential in the number of edges. It is not viable for the public exact instances yet.

Verification performed:

```sh
cargo test
/private/tmp/pace26stride/target/release/stride check data/instances/tiny/tiny01.nw data/solutions/tiny/tiny01.sol
/private/tmp/pace26stride/target/release/stride check data/instances/tiny/tiny02.nw data/solutions/tiny/tiny02.sol
/private/tmp/pace26stride/target/release/stride check data/instances/tiny/tiny03.nw data/solutions/tiny/tiny03.sol
```

STRIDE reported solution sizes 4, 1, and 7.

## Next Work

The next serious solver step is to replace full edge-subset enumeration with a parameterized exact algorithm. See `ideas.md` for possible directions.
