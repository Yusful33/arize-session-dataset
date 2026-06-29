# Skills catalog

Each subdirectory under `skills/` is one installable agent skill.

## Adding a new skill

Use the **[add-repo-skill](add-repo-skill/)** skill — it scaffolds the directory, enforces conventions, validates frontmatter, and updates the root catalog.

> Use **add-repo-skill** to add a new skill for ...

Or run manually:

```bash
python skills/add-repo-skill/scripts/validate_skill.py skills/my-skill-name
```

## Layout

```
skills/
└── my-skill-name/
    ├── SKILL.md          # Required
    ├── README.md         # Optional
    ├── scripts/          # Optional
    └── references/       # Optional
```

See [add-repo-skill/references/conventions.md](add-repo-skill/references/conventions.md) for full rules.
