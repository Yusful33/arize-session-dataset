# Arize Session-to-Dataset Skill

Export Arize session traces, pivot multi-turn conversations into **one dataset row per session**, and upload to Arize with the `ax` CLI.

Each dataset row includes a `conversation` JSON array:

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

Also available upstream in [Arize-ai/solutions-resources](https://github.com/Arize-ai/solutions-resources/tree/main/.claude/skills/arize-session-dataset).

---

## Prerequisites

1. **`ax` CLI** — [Arize AX CLI](https://arize.com/docs/ax/cli)
2. **API key** — create at [app.arize.com/admin](https://app.arize.com/admin) → API Keys
3. **Space ID or name** — find with `ax spaces list`

Configure credentials:

```bash
export ARIZE_API_KEY="your-api-key"
export ARIZE_SPACE_ID="U3BhY2U6..."   # or export ARIZE_SPACE="my-workspace"

ax profiles create --api-key "$ARIZE_API_KEY"
ax profiles show
```

---

## Installation

### Option A — Cursor (recommended)

Clone this repo and copy the skill into your personal Cursor skills directory:

```bash
git clone https://github.com/Yusful33/arize-session-dataset.git
mkdir -p ~/.cursor/skills/arize-session-dataset
cp -r arize-session-dataset/{SKILL.md,scripts,references} ~/.cursor/skills/arize-session-dataset/
```

Then invoke in Cursor chat:

> Use the **arize-session-dataset** skill to export session `SESSION_ID` from project `PROJECT` in space `SPACE`.

### Option B — Claude Code / Claude Desktop

```bash
git clone https://github.com/Yusful33/arize-session-dataset.git
mkdir -p ~/.claude/skills/arize-session-dataset
cp -r arize-session-dataset/{SKILL.md,scripts,references} ~/.claude/skills/arize-session-dataset/
```

### Option C — Install from a project repo

Copy into a project so teammates get it with the codebase:

```bash
mkdir -p .cursor/skills/arize-session-dataset
cp -r /path/to/arize-session-dataset/{SKILL.md,scripts,references} .cursor/skills/arize-session-dataset/
```

Commit `.cursor/skills/arize-session-dataset/` to share with the team.

### Option D — One-liner (no clone)

```bash
DEST=~/.cursor/skills/arize-session-dataset
BASE=https://raw.githubusercontent.com/Yusful33/arize-session-dataset/main
mkdir -p "$DEST/scripts" "$DEST/references"
curl -fsSL "$BASE/SKILL.md" -o "$DEST/SKILL.md"
curl -fsSL "$BASE/scripts/session_to_dataset.py" -o "$DEST/scripts/session_to_dataset.py"
curl -fsSL "$BASE/references/credentials.md" -o "$DEST/references/credentials.md"
curl -fsSL "$BASE/references/schema.md" -o "$DEST/references/schema.md"
chmod +x "$DEST/scripts/session_to_dataset.py"
```

After install, verify:

```bash
python ~/.cursor/skills/arize-session-dataset/scripts/session_to_dataset.py --help
```

---

## Quick start (manual)

```bash
SPACE="${ARIZE_SPACE:-$ARIZE_SPACE_ID}"
PROJECT="my-agent"
SESSION_ID="your-session-id"

mkdir -p .arize-tmp-traces

# 1. Export session spans
ax spans export "$PROJECT" \
  --space "$SPACE" \
  --session-id "$SESSION_ID" \
  --stdout > .arize-tmp-traces/spans.json

# 2. Pivot to one dataset row
python ~/.cursor/skills/arize-session-dataset/scripts/session_to_dataset.py \
  --spans .arize-tmp-traces/spans.json \
  --session-id "$SESSION_ID" \
  --project "$PROJECT" \
  --output .arize-tmp-traces/session_row.json

# 3. Upload
ax datasets create \
  --name "session-$SESSION_ID" \
  --space "$SPACE" \
  --file .arize-tmp-traces/session_row.json
```

---

## Repository layout

```
arize-session-dataset/
├── README.md              # This file — installation & quick start
├── SKILL.md               # Agent skill instructions (copy to skills dir)
├── scripts/
│   └── session_to_dataset.py
└── references/
    ├── credentials.md     # API key & space resolution
    └── schema.md          # Output columns & span-selection rules
```

---

## Related skills

- [Arize-ai/solutions-resources](https://github.com/Arize-ai/solutions-resources) — internal Solutions skills collection
- **arize-trace** — export spans by session ID
- **arize-dataset** — dataset CRUD and verification

---

## License

MIT
