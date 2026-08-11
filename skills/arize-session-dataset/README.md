# arize-session-dataset

Export Arize session traces, pivot multi-turn conversations into **one dataset row per session**, upload to Arize with the `ax` CLI, then **always** create an annotation queue over all dataset examples for human review.

**Version:** 1.2

## What it does

1. Export spans for a `session_id`
2. Pivot into one dataset row (`conversation` JSON array)
3. Create or append a dataset
4. Ensure a default **Session Quality** annotation config (`good` / `bad` / `needs_review`)
5. Create an annotation queue with **all** dataset examples (requires an Arize user email as annotator)

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
- **Annotator email** — an existing Arize user email in the space (not just Git `user.email`)

```bash
export ARIZE_API_KEY="your-api-key"
export ARIZE_SPACE_ID="U3BhY2U6..."   # or export ARIZE_SPACE="my-workspace"
ax profiles create --api-key "$ARIZE_API_KEY"
```

See [references/credentials.md](references/credentials.md) for resolution order and troubleshooting.

## CLI notes (from E2E)

- **Uppercase enums:** `--type CATEGORICAL`, `--optimization-direction NONE`, `--assignment-method ALL`
- **Session Quality config:** use `--optimization-direction NONE` (not `MAXIMIZE` — that needs scores on labels)
- **Annotator email:** must exist in the Arize space; on `404 Annotator email not found`, ask again or list emails via `ax annotation-queues list`
- **Export fallback:** if `--all` (Arrow Flight) fails with auth/denied, retry with REST `--limit 500`

## Install

**Recommended (`npx skills`):**

```bash
npx skills add Yusful33/arize-session-dataset --skill arize-session-dataset --yes
```

**Manual (Cursor):**

```bash
git clone https://github.com/Yusful33/arize-session-dataset.git ~/agent-skills
mkdir -p ~/.cursor/skills/arize-session-dataset
cp -r ~/agent-skills/skills/arize-session-dataset/{SKILL.md,scripts,references,README.md} \
  ~/.cursor/skills/arize-session-dataset/
```

For Claude Code, use `~/.claude/skills/` instead of `~/.cursor/skills/`.

## Quick start (agent prompt)

After install, paste this into Cursor or Claude Code:

> Use the **arize-session-dataset** skill. Export session `SESSION_ID` from project `PROJECT` in space `SPACE`, upload to a dataset, and create an annotation queue. My annotator email is `you@company.com`.

## Manual CLI outline

```bash
SPACE="${ARIZE_SPACE:-$ARIZE_SPACE_ID}"
PROJECT="my-agent"
SESSION_ID="your-session-id"
ANNOTATOR_EMAIL="you@company.com"
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

# Then follow SKILL.md Steps 6–9: collect example IDs, ensure Session Quality
# config (CATEGORICAL + NONE), create the annotation queue with
# --annotator-email "$ANNOTATOR_EMAIL" and --assignment-method ALL.
```

Full end-to-end commands (including queue create) are in [references/schema.md](references/schema.md).

## Files

| Path | Purpose |
|------|---------|
| `SKILL.md` | Agent instructions (copy with this folder) |
| `scripts/session_to_dataset.py` | Pivot spans → dataset row |
| `references/credentials.md` | API key & space resolution |
| `references/schema.md` | Columns, span rules, queue record sources, CLI notes, troubleshooting |

## Trigger phrases

Use in Cursor or Claude: *session to dataset*, *pivot session traces*, *conversation dataset*, *export session traces*, *session annotation queue*.
