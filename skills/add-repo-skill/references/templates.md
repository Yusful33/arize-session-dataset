# Skill templates

Copy and adapt when adding a skill to this repo.

---

## SKILL.md template

```markdown
---
name: my-skill-name
description: Third-person description of what the skill does and when to trigger it. Include trigger terms.
---

# My Skill Name

Brief one-line purpose.

---

## When to use

- Bullet list of user intents that should invoke this skill

---

## Workflow

Copy this checklist:

\`\`\`
Task Progress:
- [ ] Step 1: ...
- [ ] Step 2: ...
\`\`\`

### Step 1: ...

Instructions here.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ... | ... |

---

## Related skills

- **other-skill** — when to use instead
```

---

## README.md template (optional)

```markdown
# my-skill-name

One paragraph: what it does and who it's for.

## Prerequisites

- Tool or env var requirements

## Quick start

\`\`\`bash
# Minimal example
\`\`\`

## Trigger phrases

*phrase one*, *phrase two*
```

---

## Minimal skill (SKILL.md only)

```
skills/my-skill-name/
└── SKILL.md
```

## Full skill (with scripts and references)

```
skills/my-skill-name/
├── SKILL.md
├── README.md
├── scripts/
│   └── helper.py
└── references/
    └── details.md
```

Use [arize-session-dataset](../arize-session-dataset/) as a reference implementation.
