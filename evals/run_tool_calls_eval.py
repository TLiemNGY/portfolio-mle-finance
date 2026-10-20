"""Runs the agent on the tool-call evaluation dataset and reports the scores.

Calls the real agent (Gemini + BigQuery), so it is not part of the unit tests
or the CI. Run with:
    uv run python -m evals.run_tool_calls_eval
    uv run python -m evals.run_tool_calls_eval --case etf_sp500_price
"""

import argparse
import json
import logging
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml

from agents.orchestrator.portfolio_agent import build_agent
from core.clients import get_llm
from evals.scoring import extract_turn_tool_calls, score_case

logger = logging.getLogger(__name__)

EVALS_DIR = Path(__file__).parent
DATASET_PATH = EVALS_DIR / "datasets" / "tool_calls.yaml"
RESULTS_DIR = EVALS_DIR / "results"
# Pause between cases, to stay under the Gemini API rate limits.
DELAY_BETWEEN_CASES_SECONDS = 5


def load_cases(path: Path) -> list[dict]:
    """Loads the evaluation cases from a YAML file."""
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def run_case(agent, case: dict) -> dict:
    """Runs one case in a fresh conversation and scores its tool calls."""
    # A new thread per case: no memory carried over from one case to the next.
    config = {"configurable": {"thread_id": f"eval-{case['id']}-{uuid.uuid4()}"}}
    record = {
        "id": case["id"],
        "tags": case["tags"],
        "question": case["question"],
        "rationale": case.get("rationale", ""),
        "expected": case["expected_tool_calls"],
    }
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": case["question"]}]},
            config=config,
        )
    except Exception as error:  # noqa: BLE001 — one failing case must not stop the evaluation
        logger.error("Case %s failed: %s", case["id"], error)
        return {
            **record,
            "actual": None,
            "tools_ok": False,
            "args_ok": False,
            "error": str(error),
        }

    actual = extract_turn_tool_calls(result["messages"])
    score = score_case(case["expected_tool_calls"], actual, case.get("optional_tools"))
    return {**record, "actual": actual, **score, "error": None}


def summarize_by_tag(results: list[dict]) -> dict[str, dict]:
    """Counts, for each tag, the number of cases and how many passed.

    Returns {tag: {"total": int, "tools_ok": int, "args_ok": int}}.
    """
    summary = {}

    for result in results:
        for tag in result["tags"]:
            counts = summary.setdefault(tag, {"total": 0, "tools_ok": 0, "args_ok": 0})
            counts["total"] += 1
            counts["tools_ok"] += result["tools_ok"]
            counts["args_ok"] += result["args_ok"]

    return summary


def log_report(results: list[dict], summary: dict[str, dict]) -> None:
    """Logs one line per case (with details for failures), then the scores."""
    for result in results:
        status = "PASS" if result["args_ok"] else "FAIL"
        logger.info("%s  %s", status, result["id"])
        if not result["args_ok"]:
            actual = (
                result["actual"]
                if result["error"] is None
                else f"ERROR: {result['error']}"
            )
            logger.info("      question: %s", result["question"])
            logger.info("      expected: %s", result["expected"])
            logger.info("      actual:   %s", actual)
            logger.info("      why it matters: %s", result["rationale"].strip())

    total = len(results)
    tools_ok = sum(result["tools_ok"] for result in results)
    args_ok = sum(result["args_ok"] for result in results)
    logger.info(
        "Overall: tools %d/%d, arguments %d/%d", tools_ok, total, args_ok, total
    )
    for tag, counts in sorted(summary.items()):
        logger.info(
            "  %-22s tools %d/%d   arguments %d/%d",
            tag,
            counts["tools_ok"],
            counts["total"],
            counts["args_ok"],
            counts["total"],
        )


def get_git_sha() -> str:
    """Returns the short hash of the current commit, or 'unknown'."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def save_results(results: list[dict], summary: dict[str, dict]) -> Path:
    """Saves the run to evals/results/, with the model and the code version."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_at = datetime.now(UTC)
    git_sha = get_git_sha()
    path = RESULTS_DIR / f"tool_calls_{run_at:%Y%m%d_%H%M%S}_{git_sha}.json"
    payload = {
        "run_at": run_at.isoformat(),
        "git_sha": git_sha,
        "model": get_llm().model,
        "summary": summary,
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Run a single case, by its id.")
    args = parser.parse_args()

    cases = load_cases(DATASET_PATH)
    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            raise SystemExit(f"No case with id '{args.case}' in {DATASET_PATH}")

    agent = build_agent()
    results = []
    for position, case in enumerate(cases, start=1):
        if position > 1:
            time.sleep(DELAY_BETWEEN_CASES_SECONDS)
        logger.info("Running %s (%d/%d)", case["id"], position, len(cases))
        results.append(run_case(agent, case))

    summary = summarize_by_tag(results)
    log_report(results, summary)
    path = save_results(results, summary)
    logger.info("Results saved to %s", path)


if __name__ == "__main__":
    main()
