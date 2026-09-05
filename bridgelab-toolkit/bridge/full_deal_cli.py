"""Standalone command-line adapter for the full-deal application boundary."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from .full_deal_application import (
    FullDealApplicationErrorCode,
    FullDealApplicationResponse,
    analyze_full_deal_application,
    full_deal_application_request_from_dict,
    full_deal_application_response_to_dict,
)
from .sayc_route_configuration import create_standard_sayc_router

EXIT_SUCCESS = 0
EXIT_INTERNAL_ERROR = 1
EXIT_CLI_PARSE_ERROR = 2
EXIT_APPLICATION_ERROR = 3
EXIT_PRODUCTION_ERROR = 4

Analyzer = Callable[..., FullDealApplicationResponse]


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="python -m bridge.full_deal_cli",
        description="Analyze a full-deal JSON application request.",
        epilog=(
            "Exit codes: 0 success, 1 internal error, 2 input/JSON error, "
            "3 application validation error, 4 production error. "
            "Example: python -m bridge.full_deal_cli --input request.json --format json"
        ),
    )
    parser.add_argument(
        "--input", required=True, metavar="PATH", help="UTF-8 JSON file, or - for stdin"
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    return parser


def _error_json(code: str, message: str) -> str:
    return json.dumps(
        {
            "success": False,
            "status": "error",
            "errors": ({"code": code, "message": message},),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _emit_error(code: str, message: str, output_format: str, stream: TextIO) -> None:
    stream.write(
        (
            _error_json(code, message)
            if output_format == "json"
            else f"Error: {code}\n{message}"
        )
        + "\n"
    )


def run_cli(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    analyzer: Analyzer = analyze_full_deal_application,
) -> int:
    """Execute one CLI request; expected failures never expose tracebacks."""

    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except ValueError as exc:
        _emit_error("CLI_PARSE_ERROR", str(exc), "text", stderr)
        return EXIT_CLI_PARSE_ERROR
    try:
        raw = (
            stdin.read()
            if args.input == "-"
            else Path(args.input).read_text(encoding="utf-8")
        )
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise TypeError("Top-level JSON value must be an object.")
        request = full_deal_application_request_from_dict(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        _emit_error("CLI_PARSE_ERROR", str(exc), args.format, stderr)
        return EXIT_CLI_PARSE_ERROR
    try:
        response = analyzer(request, bidding_router=create_standard_sayc_router())
    except Exception as exc:  # noqa: BLE001 - defensive presentation boundary
        _emit_error("INTERNAL_ERROR", str(exc), args.format, stderr)
        return EXIT_INTERNAL_ERROR
    if not response.success:
        production = any(
            error.code is FullDealApplicationErrorCode.PRODUCTION_ERROR
            for error in response.errors
        )
        code = EXIT_PRODUCTION_ERROR if production else EXIT_APPLICATION_ERROR
        if args.format == "json":
            stderr.write(
                json.dumps(
                    full_deal_application_response_to_dict(response),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
        else:
            first = response.errors[0]
            _emit_error(first.code.name, first.message, "text", stderr)
        return code
    if args.format == "json":
        stdout.write(
            json.dumps(
                full_deal_application_response_to_dict(response),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
    else:
        stdout.write(f"Status: {response.status.upper()}\n\n{response.rendered_text}")
        if response.rendered_text and not response.rendered_text.endswith("\n"):
            stdout.write("\n")
    return EXIT_SUCCESS


def main() -> int:
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
