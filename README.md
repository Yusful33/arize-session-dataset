# Agent Skills

Personal collection of [Cursor](https://cursor.com) and [Claude Code](https://docs.anthropic.com/en/docs/claude-code) agent skills.

Clone once, install individual skills or the whole set into `~/.cursor/skills/` or `~/.claude/skills/`.

---

## Skills

| Skill | Description |
|-------|-------------|
| [arize-session-dataset](skills/arize-session-dataset/) | Export Arize session traces, pivot to one dataset row with a `conversation` JSON array, upload via `ax datasets` |

---

## Installation

### Install one skill

```bash
git clone https://github.com/Yusful33/arize-session-dataset.git ~/agent-skills
SKILL=arize-session-dataset   # change per skill

mkdir -p ~/.cursor/skills/$SKILL
cp -r ~/agent-skills/skills/$SKILL/{SKILL.md,scripts,references} ~/.cursor/skills/$SKILL/ 2>/dev/null || \
cp -r ~/agent-skills/skills/$SKILL/SKILL.md ~/.cursor/skills/$SKILL/
```

For Claude Code, use `~/.claude/skills/` instead of `~/.cursor/skills/`.

### Install all skills

```bash
git clone https://github.com/Yusful33/arize-session-dataset.git ~/agent-skills

mkdir -p ~/.cursor/skills
cp -R ~/agent-skills/skills/* ~/.cursor/skills/
```

### Install into a project (share with team)

```bash
mkdir -p .cursor/skills
cp -R skills/<skill-name> .cursor/skills/
git add .cursor/skills/
```

### One-liner (single skill, no clone)

```bash
SKILL=arize-session-dataset
DEST=~/.cursor/skills/$SKILL
BASE=https://raw.githubusercontent.com/Yusful33/arize-session-dataset/main/skills/$SKILL
mkdir -p "$DEST/scripts" "$DEST/references"
curl -fsSL "$BASE/SKILL.md" -o "$DEST/SKILL.md"
curl -fsSL "$BASE/scripts/session_to_dataset.py" -o "$DEST/scripts/session_to_dataset.py"
curl -fsSL "$BASE/references/credentials.md" -o "$DEST/references/credentials.md"
curl -fsSL "$BASE/references/schema.md" -o "$DEST/references/schema.md"
chmod +x "$DEST/scripts/session_to_dataset.py"
```

---

## Usage

After installing, invoke by name in chat:

> Use the **arize-session-dataset** skill to export session `SESSION_ID` from project `PROJECT`.

Each skill's `README.md` has prerequisites and examples.

---

## Repository layout

```
.
├── README.md                 # This file — catalog + install
├── skills/
│   ├── README.md             # How to add new skills
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── README.md
│       ├── scripts/
│       └── references/
└── .gitignore
```

See [skills/README.md](skills/README.md) for conventions when adding skills.

---

## Related

- [Arize-ai/solutions-resources](https://github.com/Arize-ai/solutions-resources) — Arize Solutions team skills (upstream for some Arize skills)
