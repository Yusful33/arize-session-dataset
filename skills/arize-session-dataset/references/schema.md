# Session Dataset Schema

Output produced by `scripts/session_to_dataset.py` — one dataset example per session.

---

## Dataset columns

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | string | Session identifier from `attributes.session.id` |
| `turn_count` | number | Number of traces (turns) in the session |
| `conversation` | array | Ordered turns; see [Conversation turn object](#conversation-turn-object) |
| `project` | string | Arize project name passed via `--project` |
| `first_turn_at` | string | ISO 8601 start time of the earliest trace root span |
| `last_turn_at` | string | ISO 8601 start time of the latest trace root span |

### Conversation turn object

Each element in `conversation`:

| Field | Type | Description |
|-------|------|-------------|
| `turn` | number | 1-based turn index within the session |
| `input` | string | User/request input from the trace root span |
| `output` | string | Agent/response output from the trace root span |
| `trace_id` | string | `context.trace_id` for the turn |

Example:

```json
{
  "session_id": "sess_abc123",
  "turn_count": 2,
  "conversation": [
    {
      "turn": 1,
      "input": "What is our Q1 revenue?",
      "output": "Q1 revenue was $4.2M.",
      "trace_id": "trace_001"
    },
    {
      "turn": 2,
      "input": "Break that down by region.",
      "output": "NA: $2.1M, EMEA: $1.4M, APAC: $0.7M.",
      "trace_id": "trace_002"
    }
  ],
  "project": "business-intel-agent",
  "first_turn_at": "2026-06-20T10:00:00.000Z",
  "last_turn_at": "2026-06-20T10:03:12.000Z"
}
```

---

## Span selection rules

One **turn** = one **trace** (`context.trace_id`).

For each trace:

1. Group all exported spans by `context.trace_id`
2. Select the **root span** (`parent_id` is null or empty)
3. If multiple roots exist, prefer span kind in order: `CHAIN`, then `AGENT`, then earliest `start_time`
4. If no root span exists, use the span with the earliest `start_time`

**Why root span per trace:** In multi-turn agents, each user message typically starts a new trace. The root CHAIN/AGENT span carries the user-facing input and final output for that turn.

Sort traces by root span `start_time` ascending before assigning `turn` numbers.

---

## Input/output extraction

From the selected root span, in priority order:

| Field | Primary source | Fallback |
|-------|----------------|----------|
| Input | `attributes.input.value` or `attributes["input.value"]` | `attributes.llm.input_messages` (JSON-serialized) |
| Output | `attributes.output.value` or `attributes["output.value"]` | `attributes.llm.output_messages` (JSON-serialized) |

**Note:** `ax spans export` returns flat dot-notation keys inside `attributes` (e.g. `"input.value"`, `"session.id"`). The pivot script accepts both flat and nested attribute shapes.

Empty strings are kept when no I/O fields are present — the turn is still included so reviewers can inspect `trace_id` in Arize.

---

## Reserved dataset fields

Never include these in create/append payloads:

| Field | Reason |
|-------|--------|
| `id` | Server-managed example ID |
| `created_at` | Server-managed timestamp |
| `updated_at` | Server-managed timestamp |
| `time` | Reserved column name |
| `count` | Reserved column name |
| `source_record_*` | Reserved prefix |

---

## Dataset export shape

When verifying with `ax datasets export`, user-defined fields may appear under `additional_properties`:

```json
{
  "id": "...",
  "created_at": "...",
  "updated_at": "...",
  "additional_properties": {
    "session_id": "session_133777",
    "turn_count": 6,
    "conversation": "[{\"turn\": 1, \"input\": \"...\", \"output\": \"...\", \"trace_id\": \"...\"}]",
    "project": "liftoff",
    "first_turn_at": "...",
    "last_turn_at": "..."
  }
}
```

The `conversation` field may be stored as a JSON string on export. Parse it when needed:

```bash
ax datasets export DATASET --space SPACE --stdout \
  | jq '.[0].additional_properties | {session_id, turn_count, project}'
```

---

## End-to-end example

Replace `SPACE`, `PROJECT`, and `SESSION_ID` with values from the user or from `$ARIZE_SPACE` / `$ARIZE_SPACE_ID`. Never hardcode a space.

```bash
# Resolve space from env or user input
SPACE="${ARIZE_SPACE:-${ARIZE_SPACE_ID:?Set ARIZE_SPACE or ARIZE_SPACE_ID}}"

mkdir -p .arize-tmp-traces

# 1. Export (always pass --space)
ax spans export PROJECT \
  --space "$SPACE" \
  --session-id SESSION_ID \
  --output-dir .arize-tmp-traces \
  --stdout > .arize-tmp-traces/spans.json

# 2. Pivot
python skills/arize-session-dataset/scripts/session_to_dataset.py \
  --spans .arize-tmp-traces/spans.json \
  --session-id SESSION_ID \
  --project PROJECT \
  --output .arize-tmp-traces/session_row.json

# 3. Upload
ax datasets create \
  --name "session-SESSION_ID" \
  --space "$SPACE" \
  --file .arize-tmp-traces/session_row.json

# 4. Verify
ax datasets export "session-SESSION_ID" --space "$SPACE" --stdout \
  | jq '.[0].additional_properties // .[0] | {session_id, turn_count}'
```

---

## Troubleshooting

### Missing `session.id`

Symptom: `No spans contain attributes.session.id`

Fix: Instrument the agent to set `session.id` on every span in a conversation. See **arize-instrumentation** or **arize-synthetic-demo** `references/openinference.md`.

### Empty conversation I/O

Symptom: Turns exist but `input`/`output` are empty strings.

Inspect the export:

```bash
jq '[.[] | select(.parent_id == null or .parent_id == "") | {
  trace_id: .context.trace_id,
  kind: .attributes.openinference.span.kind,
  input: .attributes.input.value,
  output: .attributes.output.value
}]' .arize-tmp-traces/spans.json
```

If I/O lives on child LLM spans instead of the root, the agent may need to set `attributes.input.value` / `attributes.output.value` on the root CHAIN/AGENT span.

### Export lag / missing recent traces

Time-range exports can lag 6–12 hours in the time-series index. Session ID export (`--session-id`) uses direct lookup and is preferred for known sessions.

If you have a `trace_id`, use:

```bash
ax spans export PROJECT \
  --space SPACE \
  --trace-id TRACE_ID \
  --stdout | jq '.[0].attributes."session.id" // .[0].attributes.session.id'
```

Then re-export with `--session-id`.
