# Skills catalog

Each subdirectory is one installable agent skill.

## Layout

```
skills/
└── my-skill-name/
    ├── SKILL.md          # Required — agent instructions + YAML frontmatter
    ├── README.md         # Optional — human docs, examples, prerequisites
    ├── scripts/          # Optional — helper scripts the agent runs
    └── references/       # Optional — detailed docs loaded on demand
```

## Adding a new skill

1. Create `skills/<skill-name>/` (lowercase, hyphens only).
2. Add `SKILL.md` with frontmatter:

```yaml
---
name: my-skill-name
description: Third-person description of what it does and when to trigger it.
---
```

3. Add a short `README.md` if the skill needs setup steps or examples.
4. Update the **Skills** table in the [root README](../README.md).
5. Open a PR.

## Conventions

- Keep `SKILL.md` under ~500 lines; put long reference material in `references/`.
- Scripts should be runnable with stdlib or document dependencies in the skill README.
- Use `$SKILL_ROOT` or paths relative to the installed skill dir, not hardcoded home paths.
