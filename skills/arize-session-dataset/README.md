# arize-session-dataset

Export Arize session traces, pivot multi-turn conversations into **one dataset row per session**, and upload to Arize with the `ax` CLI.

Also available upstream in [Arize-ai/solutions-resources](https://github.com/Arize-ai/solutions-resources/tree/main/.claude/skills/arize-session-dataset).

## Output shape

```json
{
  "session_id": "sess_abc123",
  "turn_count": 3,
  "conversation": [
    {"turn": 1, "input": "...", "output": "...", "trace_id": "..."},
    {"turn": 2, "input": "...", "output": "...", "trace_id": "..."}
  ],
  "project": "my-agent",
  "first_turn_at": "2026-06-20T10:00:00Z",
  "last_turn_at": "2026-06-20T10:05:00Z"
}
```

## Prerequisites

- **`ax` CLI** — [Arize AX CLI](https://arize.com/docs/ax/cli)
- **API key** — [app.arize.com/admin](https://app.arize.com/admin) → API Keys
- **Space ID or name** — `ax spaces list`

```bash
export ARIZE_API_KEY="your-api-key"
export ARIZE_SPACE_ID="U3BhY2U6..."   # or export ARIZE_SPACE="my-workspace"
ax profiles create --api-key "$ARIZE_API_KEY"
```

See [references/credentials.md](references/credentials.md) for resolution order and troubleshooting.

## Quick start

```bash
SPACE="${ARIZE_SPACE:-$ARIZE_SPACE_ID}"
PROJECT="my-agent"
SESSION_ID="your-session-id"
SKILL_ROOT="${SKILL_ROOT:-$HOME/.cursor/skills/arize-session-dataset}"

mkdir -p .arize-tmp-traces

ax spans export "$PROJECT" \
  --space "$SPACE" \
  --session-id "$SESSION_ID" \
  --stdout > .arize-tmp-traces/spans.json

python "$SKILL_ROOT/scripts/session_to_dataset.py" \
  --spans .arize-tmp-traces/spans.json \
  --session-id "$SESSION_ID" \
  --project "$PROJECT" \
  --output .arize-tmp-traces/session_row.json

ax datasets create \
  --name "session-$SESSION_ID" \
  --space "$SPACE" \
  --file .arize-tmp-traces/session_row.json
```

## Files

| Path | Purpose |
|------|---------|
| `SKILL.md` | Agent instructions (copy with this folder) |
| `scripts/session_to_dataset.py` | Pivot spans → dataset row |
| `references/credentials.md` | API key & space resolution |
| `references/schema.md` | Columns, span rules, troubleshooting |

## Trigger phrases

Use in Cursor or Claude: *session to dataset*, *pivot session traces*, *conversation dataset*, *export session traces*.
