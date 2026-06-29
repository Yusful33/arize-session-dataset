---
name: arize-session-dataset
description: Exports all traces for a single Arize session, pivots them into one dataset row with a conversation JSON array, and uploads via ax datasets create or append. Use when the user wants session to dataset, pivot session traces, conversation dataset, export session traces, or a multi-turn dataset row from one session_id.
metadata:
  author: arize
  version: "1.0"
compatibility: Requires the ax CLI and a configured Arize profile.
---

# Arize Session-to-Dataset Skill

> **`SPACE`** — All `--space` flags accept a space **name** (e.g., `my-workspace`) or a base64 space **ID**. Find yours with `ax spaces list`.

Export all traces for **one session**, pivot them into a single dataset row with a `conversation` JSON array, and upload to Arize.

**Direction:** Spans export → pivot script → dataset create/append. There is no single native `ax` command for this workflow.

---

## Prerequisites

Requires the `ax` CLI. Resolve credentials and space in **Step 1** before running export or dataset commands.

If an `ax` command fails, troubleshoot based on the error:
- `command not found` or version error → see **arize-trace** skill `references/ax-setup.md`
- `401 Unauthorized` / missing API key → see [references/credentials.md](references/credentials.md)
- `project not found` / space resolution error → pass `--space` on every `ax` command; see [references/credentials.md](references/credentials.md)
- Project unclear → ask the user, or run `ax projects list --space SPACE -o json --limit 100`
- **Security:** Never read `.env` files or search the filesystem for credentials. Use `ax profiles`, `$ARIZE_API_KEY`, `$ARIZE_SPACE`, and `$ARIZE_SPACE_ID` from the shell only.

---

## Concepts

| Term | Meaning |
|------|---------|
| **Session** | Traces sharing `attributes.session.id` (multi-turn conversation) |
| **Trace** | One request/response cycle; one row in the pivoted `conversation` array |
| **Root span** | Span with null/empty `parent_id`; source of input/output per trace |
| **Dataset row** | One session collapsed into `session_id`, `turn_count`, and `conversation` |

Output row shape:

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

For column definitions and span-selection rules, see [references/schema.md](references/schema.md).

---

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Resolve credentials, space, and inputs
- [ ] Step 2: Export session spans
- [ ] Step 3: Pivot to one row
- [ ] Step 4: Validate output
- [ ] Step 5: Upload dataset
- [ ] Step 6: Verify upload
```

### Step 1: Resolve credentials, space, and inputs

#### 1a. Resolve API key

Check whether authentication is already configured:

```bash
ax profiles show
test -n "$ARIZE_API_KEY" && echo "ARIZE_API_KEY is set"
```

| Condition | Action |
|-----------|--------|
| Active profile has an API key | Proceed |
| Profile missing but `$ARIZE_API_KEY` is set | `ax profiles create --api-key "$ARIZE_API_KEY"` (or `update`) |
| Neither available | **Ask the user** to export `ARIZE_API_KEY` in their terminal and configure a profile — see [references/credentials.md](references/credentials.md) |

#### 1b. Resolve space

**Never hardcode a space.** Resolve from the user or environment:

```bash
echo "${ARIZE_SPACE:-${ARIZE_SPACE_ID:-not_set}}"
```

| Priority | Source |
|----------|--------|
| 1 | Space name or ID the user provided in their request |
| 2 | `$ARIZE_SPACE` env var (name or base64 ID) |
| 3 | `$ARIZE_SPACE_ID` env var (base64 ID) |

If none are available, run `ax spaces list -o json` and **ask the user** which space to use (AskQuestion when multiple apply). Full details: [references/credentials.md](references/credentials.md).

Store the resolved value as `SPACE` and pass `--space "$SPACE"` on **every** `ax` command below.

#### 1c. Resolve workflow inputs

Collect if still missing:

| Input | Required | Notes |
|-------|----------|-------|
| `PROJECT` | yes | Arize project name or base64 ID |
| `SESSION_ID` | yes | Value of `attributes.session.id` |
| `SPACE` | yes | From step 1b — never omit on `ax` calls |
| Dataset target | yes | New dataset name **or** existing dataset to append |

If the user only has a trace ID, export that trace first and read `attributes.session.id` (see **arize-trace**):

```bash
ax spans export PROJECT \
  --space SPACE \
  --trace-id TRACE_ID \
  --stdout | jq '.[0].attributes."session.id" // .[0].attributes.session.id'
```

### Step 2: Export session spans

Use targeted export. Default output directory: `.arize-tmp-traces`. Always include `--space`.

```bash
mkdir -p .arize-tmp-traces

ax spans export PROJECT \
  --space SPACE \
  --session-id SESSION_ID \
  --output-dir .arize-tmp-traces \
  --stdout > .arize-tmp-traces/spans.json
```

**Targeted export rule:** If span count equals the default limit (100), re-run with `--all`:

```bash
ax spans export PROJECT \
  --session-id SESSION_ID \
  --space SPACE \
  --all \
  --output-dir .arize-tmp-traces \
  --stdout > .arize-tmp-traces/spans.json
```

Confirm spans were exported:

```bash
jq 'length' .arize-tmp-traces/spans.json
```

### Step 3: Pivot to one row

Run the bundled script (from repo checkout or installed skill dir):

```bash
# Installed under ~/.cursor/skills/ or ~/.claude/skills/
python ~/.cursor/skills/arize-session-dataset/scripts/session_to_dataset.py \
  --spans .arize-tmp-traces/spans.json \
  --session-id SESSION_ID \
  --project PROJECT \
  --output .arize-tmp-traces/session_row.json

# Or from this repo without installing
python skills/arize-session-dataset/scripts/session_to_dataset.py \
  --spans .arize-tmp-traces/spans.json \
  --session-id SESSION_ID \
  --project PROJECT \
  --output .arize-tmp-traces/session_row.json
```

### Step 4: Validate output

The script exits non-zero if:
- No spans in the export file
- `attributes.session.id` is missing or does not match `--session-id`
- No trace IDs or conversation turns could be extracted

Inspect the pivoted row:

```bash
jq '.[0] | {session_id, turn_count, first_turn_at, last_turn_at, conversation: [.conversation[] | {turn, trace_id}]}' \
  .arize-tmp-traces/session_row.json
```

### Step 5: Upload dataset

**Create a new dataset:**

```bash
ax datasets create \
  --name "session-SESSION_ID" \
  --space SPACE \
  --file .arize-tmp-traces/session_row.json
```

**Append to an existing dataset:**

```bash
ax datasets append EXISTING_DATASET \
  --space SPACE \
  --file .arize-tmp-traces/session_row.json
```

Do not include server-managed fields (`id`, `created_at`, `updated_at`) in the upload file.

### Step 6: Verify upload

```bash
ax datasets export DATASET_NAME --space SPACE --stdout | jq '.[0].additional_properties // .[0] | {session_id, turn_count, project, conversation: (.conversation | if type == "string" then fromjson else . end | length)}'
```

Confirm `session_id`, `turn_count`, and `conversation` match the pivoted row. On export, user fields may appear under `additional_properties` and `conversation` may be a JSON string — see [schema.md](references/schema.md).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ax: command not found` | See **arize-trace** `references/ax-setup.md` |
| `401 Unauthorized` | Configure API key via profile or `$ARIZE_API_KEY` — [credentials.md](references/credentials.md) |
| `project not found` | Add `--space SPACE`; never rely on a hardcoded space |
| No space in env or request | Ask user or run `ax spaces list`; see [credentials.md](references/credentials.md) |
| Export returns 0 spans | Verify `SESSION_ID`, `PROJECT`, and `SPACE`; check time window with `--days` or `--start-time` |
| Export hits limit | Re-run with `--all --space SPACE` |
| `No spans contain attributes.session.id` | Agent must set `session.id` on spans; see **arize-instrumentation** |
| Empty input/output in turns | Root span may lack I/O fields; inspect export with `jq` and see [schema.md](references/schema.md) |
| `session_id mismatch` | Confirm the correct session ID from a trace export |
| Dataset field rejected | Avoid reserved columns: `time`, `count`, `source_record_*` |

---

## Related Skills

- **arize-trace**: Export spans by session ID, resolve session ID from trace ID
- **arize-dataset**: Dataset CRUD, append, export verification
- **arize-experiment**: Run evaluations against the uploaded session dataset
- **arize-evaluator**: Session-granularity LLM-as-judge evaluators on live traces
