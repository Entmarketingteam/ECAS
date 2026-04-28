#!/usr/bin/env python3
"""
verification/parallel_runner.py — Parallel pipeline orchestrator.

Splits the input CSV into N chunks and launches N worker processes
simultaneously, each calling pipeline.py on its slice.

Results from each worker are merged into combined output files:
  verified_output/auto_combined_{date}.csv
  verified_output/review_combined_{date}.csv
  verified_output/hold_combined_{date}.csv

Usage:
  # Run 8 workers on all 557 leads (~70 leads each)
  python verification/parallel_runner.py --input signals/output/epc_leads_2026-04-28.csv

  # Specific number of workers
  python verification/parallel_runner.py --input leads.csv --workers 4

  # Entity resolution only (fastest pass, skips content generation)
  python verification/parallel_runner.py --input leads.csv --stage entity signal

  # Dry run — shows what would run, no API calls
  python verification/parallel_runner.py --input leads.csv --dry-run

  # With Doppler (required for API keys)
  doppler run --project example-project --config prd -- py -3.12 verification/parallel_runner.py --input signals/output/epc_leads_2026-04-28.csv
"""

import argparse
import csv
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("parallel_runner")

ROOT = Path(__file__).parent.parent
PIPELINE = ROOT / "verification" / "pipeline.py"
OUTPUT_DIR = ROOT / "verification" / "verified_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def count_rows(csv_path: str) -> int:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f)) - 1  # subtract header


def run_worker(args: dict) -> dict:
    """
    Called in a subprocess. Runs pipeline.py for one chunk.
    Returns dict with worker_id, return_code, output_prefix, elapsed.
    """
    worker_id = args["worker_id"]
    cmd = [
        sys.executable, str(PIPELINE),
        "--input", args["input"],
        "--offset", str(args["offset"]),
        "--batch-size", str(args["batch_size"]),
        "--output-prefix", args["output_prefix"],
    ]
    if args.get("stages"):
        cmd += ["--stage"] + args["stages"]
    if args.get("content_type"):
        cmd += ["--content-type", args["content_type"]]
    if args.get("dry_run"):
        cmd.append("--dry-run")

    logger.info("[worker %d] starting: offset=%d size=%d",
                worker_id, args["offset"], args["batch_size"])

    start = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start

    logger.info("[worker %d] finished in %.0fs (exit %d)",
                worker_id, elapsed, result.returncode)

    return {
        "worker_id": worker_id,
        "return_code": result.returncode,
        "output_prefix": args["output_prefix"],
        "offset": args["offset"],
        "batch_size": args["batch_size"],
        "elapsed": elapsed,
    }


def merge_csvs(pattern_suffix: str, worker_prefixes: list[str], combined_path: Path) -> int:
    """
    Merge worker output CSVs matching *{pattern_suffix} into a single combined file.
    Returns number of rows merged.
    """
    rows = []
    header = None

    for prefix in worker_prefixes:
        candidate = OUTPUT_DIR / f"{prefix}_{pattern_suffix}"
        if not candidate.exists():
            continue
        with open(candidate, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if header is None:
                header = reader.fieldnames
            for row in reader:
                rows.append(row)

    if not rows or header is None:
        return 0

    with open(combined_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Parallel verification pipeline runner")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers (default: 8)")
    parser.add_argument("--stage", nargs="+",
                        choices=["entity", "signal", "contact", "content", "route"],
                        help="Stages to run (default: all)")
    parser.add_argument("--content-type",
                        choices=["physical_mail", "email_personalization",
                                 "linkedin_post", "connection_request", "dm_message"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run — no API calls, no DB writes")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    total_rows = count_rows(str(input_path))
    logger.info("Total leads: %d | Workers: %d", total_rows, args.workers)

    if total_rows == 0:
        logger.error("No data rows found in %s", input_path)
        sys.exit(1)

    # Calculate chunk sizes
    num_workers = min(args.workers, total_rows)
    base_size = total_rows // num_workers
    remainder = total_rows % num_workers

    today = date.today().isoformat()
    worker_configs = []

    offset = 0
    for i in range(num_workers):
        chunk_size = base_size + (1 if i < remainder else 0)
        if chunk_size == 0:
            continue
        prefix = f"worker{i:02d}_{today}"
        worker_configs.append({
            "worker_id": i,
            "input": str(input_path.resolve()),
            "offset": offset,
            "batch_size": chunk_size,
            "output_prefix": prefix,
            "stages": args.stage,
            "content_type": args.content_type,
            "dry_run": args.dry_run,
        })
        logger.info("  Worker %02d: rows %d–%d (%d leads) → %s",
                    i, offset, offset + chunk_size - 1, chunk_size, prefix)
        offset += chunk_size

    if args.dry_run:
        logger.info("DRY RUN — would launch %d workers, no execution", len(worker_configs))
        return

    # Launch all workers concurrently
    logger.info("Launching %d workers in parallel...", len(worker_configs))
    wall_start = time.time()

    results = []
    # Use threads to launch subprocesses (avoids pickle issues with ProcessPoolExecutor on Windows)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(worker_configs)) as executor:
        futures = {executor.submit(run_worker, cfg): cfg["worker_id"] for cfg in worker_configs}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                wid = futures[future]
                logger.error("Worker %d raised exception: %s", wid, e)
                results.append({"worker_id": wid, "return_code": -1, "elapsed": 0})

    wall_elapsed = time.time() - wall_start
    succeeded = sum(1 for r in results if r.get("return_code") == 0)
    failed = len(results) - succeeded

    logger.info("All workers done in %.0fs | %d succeeded | %d failed",
                wall_elapsed, succeeded, failed)

    if failed:
        failed_workers = [r["worker_id"] for r in results if r.get("return_code") != 0]
        logger.warning("Failed workers: %s", failed_workers)

    # Merge outputs
    logger.info("Merging worker outputs...")
    worker_prefixes = [cfg["output_prefix"] for cfg in worker_configs]

    for suffix, label in [
        ("auto.csv", "AUTO"),
        ("review.csv", "REVIEW"),
        ("hold.csv", "HOLD"),
    ]:
        combined = OUTPUT_DIR / f"combined_{today}_{label.lower()}.csv"
        count = merge_csvs(suffix, worker_prefixes, combined)
        if count:
            logger.info("  %s: %d records → %s", label, count, combined)
        else:
            logger.info("  %s: 0 records", label)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("PARALLEL RUN COMPLETE")
    logger.info("  Total leads:     %d", total_rows)
    logger.info("  Workers:         %d", len(worker_configs))
    logger.info("  Wall time:       %.0fs (%.1f min)", wall_elapsed, wall_elapsed / 60)
    logger.info("  Sequential est:  %.0fs (%.1f min)", total_rows * 60, total_rows)
    logger.info("  Speedup:         ~%.1fx", (total_rows * 60) / max(wall_elapsed, 1))
    logger.info("  Output dir:      %s", OUTPUT_DIR)
    logger.info("=" * 60)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
