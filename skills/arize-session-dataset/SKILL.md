---
name: arize-session-dataset
description: Exports all traces for a single Arize session, pivots them into one dataset row with a conversation JSON array, uploads via ax datasets create or append, then always creates an annotation queue with a default Session Quality config for all dataset examples. Use when the user wants session to dataset, pivot session traces, conversation dataset, export session traces, session annotation queue, or a multi-turn dataset row from one session_id.
metadata:
  author: arize
  version: "1.2"
compatibility: Requires the ax CLI and a configured Arize profile.
---

# Arize Session-to-Dataset Skill

> **`SPACE`** — All `--space` flags accept a space **name** (e.g., `my-workspace`) or a base64 space **ID**. Find yours with `ax spaces list`.

Export all traces for **one session**, pivot them into a single dataset row with a `conversation` JSON array, upload to Arize, then **always** create an annotation queue backed by that dataset (all examples) for human review.

**Direction:** Spans export → pivot script → dataset create/append → default annotation config → annotation queue with all dataset examples. There is no single native `ax` command for this workflow.

**CLI note:** `ax` enum flags are **uppercase** — e.g. `--type CATEGORICAL`, `--optimization-direction NONE`, `--assignment-method ALL`. Lowercase values are rejected.

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
| **Annotation config** | Label schema reviewers apply (this skill uses a fixed default: `Session Quality`) |
| **Annotation queue** | Human review workflow over **all** examples in the uploaded dataset |

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

### Default annotation config

This skill **always** attaches the following config (create if missing; reuse if it already exists in the space):

| Field | Value |
|-------|-------|
| Name | `Session Quality` |
| Type | `CATEGORICAL` |
| Labels | `good`, `bad`, `needs_review` |
| Optimization | `NONE` |

Use `--optimization-direction NONE` for this default. `MAXIMIZE` requires scores for categorical labels and fails without them.

Do **not** ask the user to pick a config unless they explicitly override.

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
- [ ] Step 6: Verify upload and collect example IDs
- [ ] Step 7: Ensure default annotation config
- [ ] Step 8: Create annotation queue (all examples)
- [ ] Step 9: Verify queue
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
| `ANNOTATOR_EMAIL` | yes | An **existing Arize user email in the space**. Ask for their Arize account email — do **not** invent one or assume Git/`user.email` is enough if that address is not in Arize. |

Optional overrides (only if the user provides them):

| Input | Default |
|-------|---------|
| Queue name | `session-SESSION_ID-review` |
| Queue instructions | `Review the full multi-turn conversation. Label Session Quality as good, bad, or needs_review.` |
| Assignment method | `ALL` |

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

**If `--all` fails with auth/denied** (e.g. Arrow Flight unauthorized, `model does not exist or denied access`), do **not** stop — retry with a higher REST `--limit` instead:

```bash
ax spans export PROJECT \
  --session-id SESSION_ID \
  --space SPACE \
  --limit 500 \
  --output-dir .arize-tmp-traces \
  --stdout > .arize-tmp-traces/spans.json
```

Confirm spans were exported:

```bash
jq 'length' .arize-tmp-traces/spans.json
```

### Step 3: Pivot to one row

Run the bundled script from this skill directory:

```bash
python ~/.cursor/skills/arize-session-dataset/scripts/session_to_dataset.py \
  --spans .arize-tmp-traces/spans.json \
  --session-id SESSION_ID \
  --project PROJECT \
  --output .arize-tmp-traces/session_row.json
```

Or use the Claude skills path if that is the active skill root:

```bash
python ~/.claude/skills/arize-session-dataset/scripts/session_to_dataset.py \
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

Store the dataset name as `DATASET_NAME` (new or existing).

**Create a new dataset:**

```bash
ax datasets create \
  --name "session-SESSION_ID" \
  --space SPACE \
  --file .arize-tmp-traces/session_row.json \
  -o json
```

**Append to an existing dataset:**

```bash
ax datasets append EXISTING_DATASET \
  --space SPACE \
  --file .arize-tmp-traces/session_row.json
```

Do not include server-managed fields (`id`, `created_at`, `updated_at`) in the upload file.

### Step 6: Verify upload and collect example IDs

```bash
ax datasets export DATASET_NAME --space SPACE --stdout \
  | jq '.[0].additional_properties // .[0] | {session_id, turn_count, project, conversation: (.conversation | if type == "string" then fromjson else . end | length)}'
```

Confirm `session_id`, `turn_count`, and `conversation` match the pivoted row. On export, user fields may appear under `additional_properties` and `conversation` may be a JSON string — see [schema.md](references/schema.md).

Resolve the dataset ID and **all** example IDs (required for the queue):

```bash
DATASET_ID=$(ax datasets get DATASET_NAME --space SPACE -o json | jq -r '.id')

ax datasets export DATASET_NAME --space SPACE --stdout \
  > .arize-tmp-traces/dataset_examples.json

jq -n \
  --arg dataset_id "$DATASET_ID" \
  --argjson example_ids "$(jq '[.[].id]' .arize-tmp-traces/dataset_examples.json)" \
  '[{record_type: "EXAMPLE", dataset_id: $dataset_id, example_ids: $example_ids}]' \
  > .arize-tmp-traces/record_sources.json

jq '{dataset_id: .[0].dataset_id, example_count: (.[0].example_ids | length)}' \
  .arize-tmp-traces/record_sources.json
```

`example_count` must be ≥ 1. If export returns 0 examples, stop and re-check Step 5.

### Step 7: Ensure default annotation config

Reuse `Session Quality` when it already exists; otherwise create it. Enums must be uppercase; use `NONE` (not `MAXIMIZE`) for this label set.

```bash
CONFIG_ID=$(ax annotation-configs list --space SPACE --name "Session Quality" -o json \
  | jq -r 'map(select(.name == "Session Quality")) | .[0].id // empty')

if [ -z "$CONFIG_ID" ]; then
  CONFIG_ID=$(ax annotation-configs create \
    --name "Session Quality" \
    --space SPACE \
    --type CATEGORICAL \
    --value good \
    --value bad \
    --value needs_review \
    --optimization-direction NONE \
    -o json | jq -r '.id')
fi

echo "CONFIG_ID=$CONFIG_ID"
```

If create fails with `409 Conflict`, the name already exists — re-run the list/select snippet above to get `CONFIG_ID`.

### Step 8: Create annotation queue (all examples)

**Always** create a queue after a successful dataset upload. `ANNOTATOR_EMAIL` must be an existing Arize user in the space.

```bash
QUEUE_NAME="session-SESSION_ID-review"

ax annotation-queues create \
  --name "$QUEUE_NAME" \
  --space SPACE \
  --annotation-config-id "$CONFIG_ID" \
  --annotator-email ANNOTATOR_EMAIL \
  --instructions "Review the full multi-turn conversation. Label Session Quality as good, bad, or needs_review." \
  --assignment-method ALL \
  --record-sources .arize-tmp-traces/record_sources.json \
  -o json
```

Repeat `--annotator-email` for each additional reviewer the user provides.

If create fails with `404 Annotator email not found`, the address is not an Arize user in the space. Ask again for a valid Arize account email, or list emails already used on queues in the space:

```bash
ax annotation-queues list --space SPACE -o json \
  | jq -r '[.[].annotators[]?.email // empty] | unique[]'
```

If queue create succeeds **without** records (or `list-records` is empty), add them explicitly:

```bash
ax annotation-queues add-records "$QUEUE_NAME" \
  --space SPACE \
  --record-sources .arize-tmp-traces/record_sources.json
```

If the queue name already exists (`409`), either use a unique name (`session-SESSION_ID-review-$(date +%Y%m%d%H%M%S)`) or add records to the existing queue with `add-records` after confirming with the user.

### Step 9: Verify queue

```bash
ax annotation-queues get "$QUEUE_NAME" --space SPACE -o json \
  | jq '{id, name, instructions, annotation_configs, annotators}'

ax annotation-queues list-records "$QUEUE_NAME" --space SPACE -o json \
  | jq 'length'
```

Confirm:
- Queue exists and references `Session Quality`
- Annotator email matches the user-provided address
- Record count equals the number of dataset examples from Step 6

Offer a UI link via **arize-link** (`/queues/{queue_id}`) when org/space IDs are available.

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
| `--all` unauthorized / denied | Arrow Flight may be denied — retry with REST `--limit 500` (or higher) |
| Invalid enum / unexpected value | Use uppercase: `CATEGORICAL`, `NONE` / `MAXIMIZE`, `ALL` |
| `No spans contain attributes.session.id` | Agent must set `session.id` on spans; see **arize-instrumentation** |
| Empty input/output in turns | Root span may lack I/O fields; inspect export with `jq` and see [schema.md](references/schema.md) |
| `session_id mismatch` | Confirm the correct session ID from a trace export |
| Dataset field rejected | Avoid reserved columns: `time`, `count`, `source_record_*` |
| Missing annotator email | **Ask** for an Arize account email in the space — do not invent or assume Git email |
| `404 Annotator email not found` | Email is not an Arize user in the space — ask again, or list emails from `ax annotation-queues list` |
| `Annotation config not found` | Re-run Step 7; verify with `ax annotation-configs list --space SPACE --name "Session Quality"` |
| Config create fails on `MAXIMIZE` | Use `--optimization-direction NONE` for the default Session Quality labels |
| `409 Conflict` on config create | Config already exists — reuse its ID from list |
| `409 Conflict` on queue create | Pick a unique queue name or `add-records` to the existing queue |
| Queue has 0 records | Rebuild `record_sources.json` from a fresh dataset export; run `add-records` |
| `example_ids` empty | Dataset export returned no rows — re-verify Step 5/6 |

---

## Related Skills

- **arize-trace**: Export spans by session ID, resolve session ID from trace ID
- **arize-dataset**: Dataset CRUD, append, export verification
- **arize-annotation**: Annotation configs/queues deep dive; annotate-record after review
- **arize-link**: Deep links to the dataset and annotation queue in the Arize UI
- **arize-experiment**: Run evaluations against the uploaded session dataset
- **arize-evaluator**: Session-granularity LLM-as-judge evaluators on live traces
