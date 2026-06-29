# Repo skill conventions

Rules for skills in this repository (`skills/<skill-name>/`).

---

## Naming

| Rule | Example |
|------|---------|
| Lowercase + hyphens only | `arize-session-dataset` |
| Max 64 characters | — |
| `name` in frontmatter = directory name | `name: arize-session-dataset` |

---

## Required files

| File | Required | Purpose |
|------|----------|---------|
| `SKILL.md` | yes | Agent instructions + YAML frontmatter |
| `README.md` | no | Human docs, prerequisites, examples |
| `scripts/` | no | Helper scripts the agent executes |
| `references/` | no | Long docs loaded on demand |

---

## SKILL.md rules

- Start with YAML frontmatter (`name`, `description`; optional `metadata`, `compatibility`)
- **Description** in third person; include WHAT and WHEN (trigger terms)
- Keep body **under 500 lines** — move detail to `references/`
- Prefer repo-relative paths (`skills/my-skill/scripts/...`) or `$SKILL_ROOT`, not hardcoded home dirs
- Python scripts in `scripts/` should be executable (`chmod +x`)

---

## Catalog update

After adding a skill, add a row to the **Skills** table in the [root README](../../README.md):

```markdown
| [my-skill-name](skills/my-skill-name/) | One-line description |
```

---

## Validation

```bash
python skills/add-repo-skill/scripts/validate_skill.py skills/my-skill-name
```

---

## Reference skills in this repo

| Skill | Why reference it |
|-------|------------------|
| [arize-session-dataset](../arize-session-dataset/) | Full skill with scripts + references |
| [add-repo-skill](../add-repo-skill/) | Meta-skill for adding skills |
