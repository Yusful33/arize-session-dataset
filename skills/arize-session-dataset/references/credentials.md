# Credentials and Space Resolution

Use this when Step 1 cannot resolve an API key or space from the user's request or shell environment.

---

## API key resolution

Check in order — stop at the first success:

| Priority | Source | How to check |
|----------|--------|--------------|
| 1 | Active `ax` profile | `ax profiles show` — API key line is set (not `(not set)`) |
| 2 | `$ARIZE_API_KEY` env var | `test -n "$ARIZE_API_KEY" && echo set` |

If the profile is missing but `$ARIZE_API_KEY` is set:

```bash
ax profiles create --api-key "$ARIZE_API_KEY"
# or, if a profile exists but key is wrong:
ax profiles update --api-key "$ARIZE_API_KEY"
```

If **neither** is available, ask the user:

1. Export their key in their terminal: `export ARIZE_API_KEY="..."`
2. Find the key at https://app.arize.com/admin > API Keys (space-scoped service key recommended)
3. Run `ax profiles create --api-key "$ARIZE_API_KEY"`
4. Confirm with `ax profiles show`

**Never** ask the user to paste an API key into chat. **Never** read `.env` files from disk.

---

## Space resolution

Check in order — stop at the first success:

| Priority | Source | Notes |
|----------|--------|-------|
| 1 | User request | Space name or base64 ID the user provided |
| 2 | `$ARIZE_SPACE` | Accepts name or base64 ID (`ax` CLI convention) |
| 3 | `$ARIZE_SPACE_ID` | Base64 space ID (SDK convention) |

Check env vars without reading files:

```bash
echo "${ARIZE_SPACE:-${ARIZE_SPACE_ID:-}}"
```

If **none** are set, ask the user for their space name or ID. Optionally list available spaces first:

```bash
ax spaces list -o json | jq '[.spaces[] | {name, id}]'
```

Present the list with **AskQuestion** when multiple spaces could apply.

---

## Usage in commands

Once resolved, export the space for all subsequent commands:

```bash
SPACE="${ARIZE_SPACE:-${ARIZE_SPACE_ID:-USER_PROVIDED_SPACE}}"
```

Pass `--space "$SPACE"` on **every** `ax spans export`, `ax datasets create`, `ax datasets append`, and `ax datasets export` call. Project names are not globally unique — omitting `--space` causes resolution failures.

---

## Save for future sessions

If the user provided credentials during this conversation and they were not already saved, offer to persist them at the end:

- **API key** → `ax profiles create` or `ax profiles update` with `$ARIZE_API_KEY`
- **Space** → add `export ARIZE_SPACE="..."` to `~/.zshrc` or `~/.bashrc`

Skip the offer if values were already loaded from profile or env vars.
