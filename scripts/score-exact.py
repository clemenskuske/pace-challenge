#!/usr/bin/env python3
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "data" / "benchmarks" / "exact_public.tsv"
DEFAULT_SOLVER = ROOT / "target" / "debug" / "pace_challenge_maf"
DEFAULT_SCORE_FILE = ROOT / "scores" / "current-score.json"
DEFAULT_RESET_FILE = ROOT / "scores" / "reset.json"
SCORING_SOURCE = "https://pacechallenge.org/2026/#scoring"
GROUND_TRUTH_REVIEW_MESSAGE = (
    "STRIDE accepted a solution smaller than the local ground truth; "
    "analyze whether the stored expected_size is too high or whether "
    "the solver/checker/model has a bug."
)


def exact_score(correct, unsolved, disqualified):
    if disqualified:
        return 0
    return correct


def lower_bound_score(runtime_seconds, timeout_seconds=600, grace_seconds=10):
    if runtime_seconds > timeout_seconds + grace_seconds:
        return 0.0
    return (2 - runtime_seconds / (timeout_seconds + grace_seconds)) / 2


def heuristic_score(n, k_star, k):
    u = min(n, 2 * k_star)
    return max(0.0, (u - k) / (u - k_star)) ** 2


def self_test():
    assert exact_score(correct=7, unsolved=3, disqualified=False) == 7
    assert exact_score(correct=7, unsolved=0, disqualified=True) == 0
    assert lower_bound_score(0) == 1.0
    assert lower_bound_score(610) == 0.5
    assert lower_bound_score(611) == 0.0
    assert heuristic_score(n=10, k_star=3, k=3) == 1.0
    assert heuristic_score(n=10, k_star=3, k=6) == 0.0
    review_tasks = []
    case = {"instance": "demo.nw", "expected_size": 5, "actual_size": 4}
    correct_delta, disqualified = classify_checked_solution(
        case, expected_size=5, actual_size=4, ground_truth_review_tasks=review_tasks
    )
    assert correct_delta == 1
    assert disqualified is False
    assert case["outcome"] == "better_than_ground_truth"
    assert review_tasks == [
        {
            "instance": "demo.nw",
            "expected_size": 5,
            "actual_size": 4,
            "task": GROUND_TRUTH_REVIEW_MESSAGE,
        }
    ]


def classify_checked_solution(case, expected_size, actual_size, ground_truth_review_tasks):
    if expected_size is None:
        case["outcome"] = "valid_unscored_unknown_optimum"
        return 0, False
    if actual_size == expected_size:
        case["outcome"] = "correct"
        return 1, False
    if actual_size < expected_size:
        case["outcome"] = "better_than_ground_truth"
        case["ground_truth_review_task"] = GROUND_TRUTH_REVIEW_MESSAGE
        ground_truth_review_tasks.append(
            {
                "instance": case["instance"],
                "expected_size": expected_size,
                "actual_size": actual_size,
                "task": GROUND_TRUTH_REVIEW_MESSAGE,
            }
        )
        return 1, False

    case["outcome"] = "suboptimal_or_unexpected_size"
    return 0, True


def find_stride(explicit):
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("STRIDE_BIN")
    if env:
        candidates.append(Path(env))
    path_stride = shutil.which("stride")
    if path_stride:
        candidates.append(Path(path_stride))
    candidates.append(Path("/private/tmp/pace26stride/target/release/stride"))

    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    raise SystemExit(
        "Could not find the STRIDE binary. Set STRIDE_BIN or build pace26stride; "
        "the previous local build path was /private/tmp/pace26stride/target/release/stride."
    )


def load_benchmark(path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for row in reader:
            expected_size = row.get("expected_size", "").strip()
            rows.append(
                {
                    "instance": row["instance"],
                    "expected_size": int(expected_size) if expected_size else None,
                }
            )
    return rows


def run_solver(solver, instance, solution_path, remaining_seconds):
    if remaining_seconds <= 0:
        return {"outcome": "unsolved", "actual_size": None}

    with instance.open("rb") as stdin, solution_path.open("wb") as stdout:
        try:
            completed = subprocess.run(
                [str(solver)],
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                timeout=remaining_seconds,
                cwd=ROOT,
                check=False,
                start_new_session=True,
            )
        except subprocess.TimeoutExpired:
            return {"outcome": "unsolved", "actual_size": None}

    if completed.returncode != 0:
        return {
            "outcome": "unsolved",
            "actual_size": None,
        }

    return None


def check_solution(stride, instance, solution_path):
    completed = subprocess.run(
        [str(stride), "check", str(instance), str(solution_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "outcome": "infeasible",
            "actual_size": None,
            "stderr": completed.stderr.strip(),
        }

    for line in completed.stdout.splitlines():
        if line.startswith("#s solution_size "):
            return int(line.rsplit(" ", 1)[1])

    return {
        "outcome": "checker_error",
        "actual_size": None,
        "stderr": "STRIDE did not report #s solution_size",
    }


def compute_score(args):
    subprocess.run(["cargo", "build", "--quiet"], cwd=ROOT, check=True)

    solver = Path(args.solver)
    if not solver.is_absolute():
        solver = ROOT / solver
    stride = find_stride(args.stride_bin)
    benchmark_path = Path(args.benchmark)
    if not benchmark_path.is_absolute():
        benchmark_path = ROOT / benchmark_path

    cases = []
    correct = 0
    unsolved = 0
    disqualified = False
    ground_truth_review_tasks = []
    started_at = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="pace-score-") as temp_dir:
        temp_dir = Path(temp_dir)
        for row in load_benchmark(benchmark_path):
            elapsed = time.monotonic() - started_at
            remaining = args.total_timeout_seconds - elapsed
            instance = ROOT / row["instance"]
            solution_path = temp_dir / (instance.stem + ".sol")
            failed = run_solver(solver, instance, solution_path, remaining)
            case = {
                "instance": row["instance"],
                "expected_size": row["expected_size"],
                "actual_size": None,
                "outcome": None,
            }

            if failed:
                case.update(failed)
                unsolved += 1
                cases.append(case)
                continue

            checked = check_solution(stride, instance, solution_path)
            if isinstance(checked, dict):
                case.update(checked)
                disqualified = True
                cases.append(case)
                continue

            actual_size = checked
            case["actual_size"] = actual_size
            correct_delta, case_disqualified = classify_checked_solution(
                case,
                expected_size=row["expected_size"],
                actual_size=actual_size,
                ground_truth_review_tasks=ground_truth_review_tasks,
            )
            correct += correct_delta
            disqualified = disqualified or case_disqualified
            cases.append(case)

    return {
        "track": "exact",
        "formula_source": SCORING_SOURCE,
        "benchmark": str(benchmark_path.relative_to(ROOT)),
        "total_timeout_seconds": args.total_timeout_seconds,
        "score": exact_score(correct, unsolved, disqualified),
        "max_score": len(cases),
        "correct": correct,
        "unsolved": unsolved,
        "disqualified": disqualified,
        "ground_truth_review_tasks": ground_truth_review_tasks,
        "cases": cases,
    }


def write_json(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def load_json(path):
    return json.loads(path.read_text())


def comparable(result):
    return json.dumps(result, sort_keys=True, separators=(",", ":"))


def reset_changed(args):
    if not args.reset_file or not args.previous_reset_file:
        return False
    reset = load_json(args.reset_file)
    previous_reset = load_json(args.previous_reset_file)
    return comparable(reset) != comparable(previous_reset)


def main():
    parser = argparse.ArgumentParser(description="Score the solver according to PACE 2026 scoring.")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--solver", default=str(DEFAULT_SOLVER))
    parser.add_argument("--stride-bin")
    parser.add_argument("--total-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--check-file", type=Path)
    parser.add_argument("--previous-file", type=Path)
    parser.add_argument("--reset-file", type=Path, default=DEFAULT_RESET_FILE)
    parser.add_argument("--previous-reset-file", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    result = compute_score(args)

    if args.write:
        write_json(args.write, result)

    if args.check_file:
        expected = load_json(args.check_file)
        if comparable(expected) != comparable(result):
            print(f"Computed score does not match {args.check_file}", file=sys.stderr)
            print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
            return 1

    if args.previous_file:
        previous = load_json(args.previous_file)
        if result["disqualified"]:
            print("Current score is disqualified; refusing push.", file=sys.stderr)
            return 1
        if result["score"] <= previous.get("score", -1):
            if reset_changed(args):
                print(
                    f"Score gate reset: allowing score {result['score']} after previous score "
                    f"{previous.get('score', -1)} because the reset file changed.",
                    file=sys.stderr,
                )
                return 0
            print(
                f"Current score {result['score']} is not better than previous score "
                f"{previous.get('score', -1)}.",
                file=sys.stderr,
            )
            return 1

    if not args.write and not args.check_file and not args.previous_file:
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
