#!/usr/bin/env python3
"""Pivot exported Arize session spans into a single dataset row."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_KIND_PRIORITY = ("CHAIN", "AGENT")
CURSOR_INPUT_SPAN_NAMES = ("User Prompt",)
CURSOR_OUTPUT_SPAN_NAMES = ("Agent Response", "Agent Stop")


def _nested_get(obj: dict[str, Any], *keys: str) -> Any:
    current: Any = obj
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _attribute(span: dict[str, Any], dotted_key: str) -> Any:
    """Read an attribute from flat export keys or nested attributes."""
    flat_prefixed = f"attributes.{dotted_key}"
    if flat_prefixed in span:
        return span[flat_prefixed]

    attributes = span.get("attributes")
    if isinstance(attributes, dict):
        flat = attributes.get(dotted_key)
        if flat is not None:
            return flat
        return _nested_get(attributes, *dotted_key.split("."))

    return None


def _trace_id(span: dict[str, Any]) -> str | None:
    trace_id = span.get("context.trace_id")
    if isinstance(trace_id, str) and trace_id:
        return trace_id
    nested = _nested_get(span, "context", "trace_id")
    return nested if isinstance(nested, str) and nested else None


def _is_root_span(span: dict[str, Any]) -> bool:
    parent_id = span.get("parent_id")
    return parent_id is None or parent_id == ""


def _span_kind(span: dict[str, Any]) -> str | None:
    kind = _attribute(span, "openinference.span.kind")
    return kind if isinstance(kind, str) else None


def _parse_start_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        return datetime.min
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min


def _serialize_messages(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def _extract_input(span: dict[str, Any]) -> str:
    direct = _attribute(span, "input.value")
    if isinstance(direct, str) and direct.strip():
        return direct

    messages = _attribute(span, "llm.input_messages")
    serialized = _serialize_messages(messages)
    return serialized or ""


def _extract_output(span: dict[str, Any]) -> str:
    direct = _attribute(span, "output.value")
    if isinstance(direct, str) and direct.strip():
        return direct

    messages = _attribute(span, "llm.output_messages")
    serialized = _serialize_messages(messages)
    return serialized or ""


def _session_id_from_span(span: dict[str, Any]) -> str | None:
    session_id = _attribute(span, "session.id") or _attribute(
        span, "cursor.conversation.id"
    )
    return session_id if isinstance(session_id, str) and session_id else None


def _span_name(span: dict[str, Any]) -> str:
    name = span.get("name")
    return name if isinstance(name, str) else ""


def _select_named_span(
    spans: list[dict[str, Any]], names: tuple[str, ...]
) -> dict[str, Any] | None:
    for target in names:
        matches = [span for span in spans if _span_name(span) == target]
        if matches:
            return min(
                matches, key=lambda span: _parse_start_time(span.get("start_time"))
            )
    return None


def _select_turn_io_spans(
    trace_spans: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Return input span, output span, and sort key time for a trace."""
    input_span = _select_named_span(trace_spans, CURSOR_INPUT_SPAN_NAMES)
    output_span = _select_named_span(trace_spans, CURSOR_OUTPUT_SPAN_NAMES)

    if input_span is None:
        input_span = _select_root_span(trace_spans)

    if output_span is None:
        with_output = [span for span in trace_spans if _extract_output(span).strip()]
        if with_output:
            output_span = max(
                with_output, key=lambda span: _parse_start_time(span.get("start_time"))
            )
        else:
            output_span = _select_root_span(trace_spans)

    sort_span = input_span or _select_root_span(trace_spans)
    return input_span, output_span, sort_span.get("start_time")


def _select_root_span(spans: list[dict[str, Any]]) -> dict[str, Any]:
    roots = [span for span in spans if _is_root_span(span)]
    if not roots:
        return min(spans, key=lambda span: _parse_start_time(span.get("start_time")))

    for kind in ROOT_KIND_PRIORITY:
        matches = [span for span in roots if _span_kind(span) == kind]
        if matches:
            return min(
                matches, key=lambda span: _parse_start_time(span.get("start_time"))
            )

    return min(roots, key=lambda span: _parse_start_time(span.get("start_time")))


def _load_spans(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array in {path}")

    spans = [item for item in payload if isinstance(item, dict)]
    if not spans:
        raise ValueError(f"No spans found in {path}")

    return spans


def _group_by_trace(spans: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for span in spans:
        trace_id = _trace_id(span)
        if not trace_id:
            continue
        grouped[trace_id].append(span)
    return grouped


def _validate_session_id(spans: list[dict[str, Any]], expected_session_id: str) -> None:
    observed = {
        session_id
        for span in spans
        if (session_id := _session_id_from_span(span)) is not None
    }

    if not observed:
        raise ValueError(
            "No spans contain attributes.session.id. "
            "Ensure the agent sets session.id on exported spans."
        )

    if expected_session_id not in observed:
        observed_list = ", ".join(sorted(observed))
        raise ValueError(
            f"Expected session_id '{expected_session_id}' but found: {observed_list}"
        )


def pivot_session_to_row(
    spans: list[dict[str, Any]],
    *,
    session_id: str,
    project: str,
) -> dict[str, Any]:
    _validate_session_id(spans, session_id)

    trace_groups = _group_by_trace(spans)
    if not trace_groups:
        raise ValueError("No spans with context.trace_id were found.")

    turns: list[dict[str, Any]] = []
    for trace_id, trace_spans in trace_groups.items():
        input_span, output_span, start_time = _select_turn_io_spans(trace_spans)
        input_text = _extract_input(input_span)
        output_text = _extract_output(output_span)

        # Skip non-turn traces (e.g. Session Start) with no user I/O
        if not input_text.strip() and not output_text.strip():
            if _select_named_span(trace_spans, CURSOR_INPUT_SPAN_NAMES) is None:
                continue

        turns.append(
            {
                "trace_id": trace_id,
                "start_time": start_time,
                "input": input_text,
                "output": output_text,
            }
        )

    turns.sort(key=lambda turn: _parse_start_time(turn["start_time"]))

    conversation = [
        {
            "turn": index,
            "input": turn["input"],
            "output": turn["output"],
            "trace_id": turn["trace_id"],
        }
        for index, turn in enumerate(turns, start=1)
    ]

    if not conversation:
        raise ValueError("No conversation turns could be extracted from the session.")

    first_turn_at = turns[0]["start_time"]
    last_turn_at = turns[-1]["start_time"]

    return {
        "session_id": session_id,
        "turn_count": len(conversation),
        "conversation": conversation,
        "project": project,
        "first_turn_at": first_turn_at,
        "last_turn_at": last_turn_at,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pivot exported Arize session spans into one dataset row."
    )
    parser.add_argument(
        "--spans", required=True, type=Path, help="Exported spans JSON file"
    )
    parser.add_argument("--session-id", required=True, help="Expected session ID")
    parser.add_argument("--project", required=True, help="Arize project name")
    parser.add_argument(
        "--output", type=Path, help="Write dataset JSON array to this file"
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print dataset JSON array to stdout instead of writing a file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.stdout and args.output is None:
        parser.error("Provide --output or pass --stdout")

    spans = _load_spans(args.spans)
    row = pivot_session_to_row(spans, session_id=args.session_id, project=args.project)
    payload = [row]
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)

    if args.stdout:
        print(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{rendered}\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
