# Solver Ideas

- Use the `pace26io` crate for production parsing/output once the core algorithm grows. The current hand parser is useful for bootstrapping but should not become infrastructure debt.
- Implement known FPT branching for rooted MAF on multiple trees, using the current exhaustive solver as an oracle on tiny regression cases.
- Add lower-bound machinery early: incompatible triples, cherry conflicts, or maximum packing of local obstructions.
- Use common pendant subtree and common cherry reductions before branching.
- Exploit the provided `treedecomp` parameter: dynamic programming over the display graph decomposition is likely the intended exact-track angle.
- Consider SAT, MaxSAT, or ILP encodings. PACE allows non-commercial solvers and ILP solvers whose licenses do not restrict free distribution of the submission.
- Build a STRIDE-backed regression harness with `stride run --offline` for local feasibility, then optionally compare against the STRIDE server when uploading is intended.
- Maintain a bank of tiny adversarial instances for cleanup edge cases: single-leaf components, root contraction, identical trees, caterpillars, and forests with several optimal textual representations.
- Add canonical forest normalization tests independent of solving so future algorithm changes can safely reuse output code.
- For public exact instances, inspect which parameter values are actually present and cluster by `n`, tree count, and decomposition width before choosing the next algorithmic attack.
