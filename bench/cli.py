"""`python -m bench` entry point."""

import argparse
import sys

from .runner import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run llm-bench eval suite.")
    parser.add_argument("--task", action="append", help="Run only this task category (repeatable).")
    parser.add_argument("--model", action="append", help="Run only this model id (repeatable).")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, no API calls.")
    parser.add_argument("--out", default="results", help="Output directory (default: results/).")
    args = parser.parse_args(argv)

    run(
        task_filter=args.task,
        model_filter=args.model,
        dry_run=args.dry_run,
        out_dir=args.out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
