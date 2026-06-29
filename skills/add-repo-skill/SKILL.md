---
name: add-repo-skill
description: Adds a new agent skill to this personal skills repository under skills/. Scaffolds SKILL.md, optional README/scripts/references, validates naming and frontmatter, and updates the root catalog. Use when the user wants to add a skill, create a new skill in this repo, scaffold a skill, or extend the skills collection.
---

# Add Repo Skill

Add a new skill to **this repository** under `skills/<skill-name>/`.

For general Cursor skill authoring (outside this repo), see Cursor's built-in create-skill guidance. This skill is **repo-specific**.

---

## When to use

- User wants to add a new skill to their personal skills collection
- User asks to scaffold, create, or document a skill in this repo
- User is extending `skills/` with another workflow

---

## Workflow

```
Task Progress:
- [ ] Step 1: Gather requirements
- [ ] Step 2: Scaffold skill directory
- [ ] Step 3: Write SKILL.md
- [ ] Step 4: Add optional files
- [ ] Step 5: Validate
- [ ] Step 6: Update catalog
- [ ] Step 7: Commit (if user asks)
```

### Step 1: Gather requirements

Ask if missing (use AskQuestion when available):

| Input | Required | Notes |
|-------|----------|-------|
| Skill name | yes | Lowercase + hyphens, e.g. `my-new-skill` |
| Purpose | yes | One sentence: what does it do? |
| Trigger terms | yes | Phrases that should invoke it |
| Scripts needed? | no | Helper scripts the agent runs |
| References needed? | no | Long docs for progressive disclosure |

Pick a name that does not already exist under `skills/`.

### Step 2: Scaffold skill directory

From the **repository root**:

```bash
SKILL_NAME="my-new-skill"
mkdir -p "skills/$SKILL_NAME"/{scripts,references}
touch "skills/$SKILL_NAME/SKILL.md"
```

Add `README.md` when the skill has prerequisites, install steps, or examples humans will read.

Templates: [references/templates.md](references/templates.md)

### Step 3: Write SKILL.md

Required frontmatter:

```yaml
---
name: my-new-skill
description: Third-person description with WHAT and WHEN (trigger terms).
---
```

Conventions: [references/conventions.md](references/conventions.md)

Use [skills/arize-session-dataset/](../arize-session-dataset/SKILL.md) as a structural reference for multi-step workflows.

If the user provided exact wording for the skill body, use it **verbatim**.

### Step 4: Add optional files

| Need | Add |
|------|-----|
| Runnable helper | `scripts/<name>.py` + `chmod +x` |
| Long reference docs | `references/<topic>.md` |
| Human setup guide | `README.md` |

Keep `SKILL.md` under 500 lines. Link to `references/` for detail.

### Step 5: Validate

```bash
python skills/add-repo-skill/scripts/validate_skill.py "skills/$SKILL_NAME"
```

Fix all errors before proceeding.

### Step 6: Update catalog

Add a row to the **Skills** table in [README.md](../../README.md) at the repo root:

```markdown
| [my-new-skill](skills/my-new-skill/) | One-line description |
```

Keep rows sorted alphabetically by skill name.

### Step 7: Commit

Only commit when the user explicitly asks. Suggested message:

```
Add <skill-name> skill to skills collection.
```

---

## Checklist (quick reference)

- [ ] `skills/<name>/SKILL.md` with matching `name` in frontmatter
- [ ] Third-person `description` with trigger terms
- [ ] Optional `README.md`, `scripts/`, `references/` as needed
- [ ] `validate_skill.py` passes
- [ ] Root `README.md` Skills table updated

---

## Related

- [references/conventions.md](references/conventions.md) — naming and layout rules
- [references/templates.md](references/templates.md) — copy-paste templates
- [skills/arize-session-dataset/](../arize-session-dataset/) — example full skill
