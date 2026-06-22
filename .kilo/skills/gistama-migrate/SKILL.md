---
name: gistama-migrate
description: >
  Agent for migrating selected pyRevit tools from PrasKaaPyKitv2 (personal toolkit) into the
  GistamaBIM.extension handover extension. Use this skill whenever Pras wants to copy, clean,
  or adapt a personal tool for colleague handover — including stripping personal references,
  sanitizing lib/ dependencies, audit-checking for IronPython compatibility, and preparing
  the target pushbutton folder. Trigger on phrases like "migrate this tool", "add this to
  handover", "copy to Gistama extension", "prepare for handover", or "which tools can I share".
---

# Gistama Migration Agent

## Purpose

Migrate chosen tools from `PrasKaaPyKitv2.extension` into `GistamaBIM.extension`.
Output must be clean, self-contained, and colleague-safe — no personal references,
no broken lib imports, no PrasKaaPyKitv2-specific dependencies.

---

## Project Context

### Local Paths (Pras's machine)

```
SOURCE (personal toolkit, portable disk):
F:\1_STUDI\_PrasKaa Python Kit\PrasKaaPyKitv2.extension\

TARGET (handover extension, fixed local path):
F:\Data Prasetyo Kristiawan\GISTAMA WFH\_GistamaBIM
```

The target path is fixed — always use `F:\Data Prasetyo Kristiawan\GISTAMA WFH\_GistamaBIM`.
Do not suggest any other target path unless Pras explicitly changes it.

### GitHub Repo

```
Repo URL:      https://github.com/praskaa/GistamaBIM.extension  (private)
Branch:        master
ZIP API URL:   https://api.github.com/repos/praskaa/GistamaBIM.extension/zipball/master
```

This repo is what colleagues download via the in-Revit Updater button.
Every file pushed to `master` is what colleagues get on next update.

### Update System (already built — do not redesign)

Two buttons live inside the extension:

**`SetupUpdater.pushbutton/script.py`** — one-time setup per colleague machine.
Asks colleague to paste a GitHub PAT token. Saves it to:
`C:\Users\[name]\.gistamabim\token.dat`
Token is read-only, scoped to this repo only, never committed to GitHub.

**`Updater.pushbutton/script.py`** — colleague runs this to get updates.
- Downloads ZIP from GitHub private API using stored token
- Uses short temp path `C:\gbim_tmp\` to avoid Windows 260-char MAX_PATH limit
- Strips GitHub prefix folder (`praskaa-GistamaBIM.extension-<hash>/`) during extraction
- Overwrites local extension files
- Shows Indonesian-language messages to colleagues

Do not modify the updater logic unless Pras explicitly asks.

---

## Migration Checklist (run every tool through this)

### 1. Strip Personal Identity
- Replace `# Author: PrasKaa` → `# Author: GistamaBIM`
- Remove any reference to `PrasKaaPyKitv2`, `PrasKaa`, personal file paths
- Replace hardcoded personal paths (`F:\1_STUDI\...`) with relative `os.path` logic

### 2. Resolve lib/ Dependencies
Scan imports for anything from `PrasKaaPyKitv2/lib/`. For each dependency:
- **Option A** — Inline the function directly into the script (preferred for single-use helpers)
- **Option B** — Copy the module into `GistamaBIM.extension/lib/` (preferred if 2+ tools use it)

Flag which modules need to be copied and which can be inlined.

```python
# PrasKaaPyKitv2 import pattern to detect:
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
from compat import get_element_id_value

# Replace with GistamaBIM lib path (tab/panel/pushbutton = 3 levels up):
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
from compat import get_element_id_value
```

### 3. IronPython 2.7 Audit
Check every script for:
- [ ] f-strings → convert to `.format()`
- [ ] `ElementId.IntegerValue` → wrap in try/except with `.Value` fallback
- [ ] `requests`, `pandas`, `numpy`, or other CPython-only imports → flag and remove
- [ ] Type hints → strip them
- [ ] Walrus operator `:=` → rewrite as separate assignment
- [ ] `urllib.request` → must use `urllib2` in IronPython

### 4. Revit Version Safety (2024 / 2025 / 2026)
- `.Value` / `.IntegerValue` → apply compat try/except pattern
- Any API changed between versions → add try/except fallback
- Do not assume a single Revit version

### 5. Self-Containment Check
After migration, the script must run with ZERO dependency on PrasKaaPyKitv2.
Trace every import. If any path still points outside `GistamaBIM.extension/`, flag it.

### 6. Sensitivity / Privacy Check
Remove or redact:
- Internal project names, client names, file server paths
- Any hardcoded credentials, tokens, URLs to internal systems
- Google Sheets logger references (personal infrastructure — never migrate)
- Comments referencing personal workflow context not useful to colleagues

### 7. Preserve Source Folder Structure
Do NOT redesign or rename the folder structure. Keep the tool's existing tab/panel/pushbutton
folder names exactly as-is from PrasKaaPyKitv2. Only the root path changes:

```
FROM:  F:\1_STUDI\_PrasKaa Python Kit\PrasKaaPyKitv2.extension\[Tab]\[Panel]\[Tool].pushbutton\
TO:    F:\Data Prasetyo Kristiawan\GISTAMA WFH\_GistamaBIM\[Tab]\[Panel]\[Tool].pushbutton\
```

Files to place in the target pushbutton folder:
- `script.py` — the cleaned/migrated version
- `icon.png` — copy as-is from source
- `bundle.yaml` — copy as-is if present in source
- Any other non-`.pyc` files from the source pushbutton folder

Do not suggest renaming tabs, panels, or pushbutton folders unless Pras explicitly asks.

---

## Output Format

For each tool migrated, produce:

```
## [ToolName] Migration Report

**Source**: [original path or "pasted content"]
**Target path**: F:\Data Prasetyo Kristiawan\GISTAMA WFH\_GistamaBIM\[Tab]\[Panel]\[Tool].pushbutton\

### Changes Made
- [bullet list of every change: stripped X, inlined Y, fixed Z]

### lib/ modules needed in GistamaBIM.extension/lib/
- [list, or "none"]

### Warnings / Manual Steps Required
- [anything the agent couldn't fix automatically]

### Final script.py
[clean script, ready to paste]
```

---

## Decision: Inline vs lib/ Copy

| Situation | Decision |
|---|---|
| Helper used only by this one tool | Inline at bottom of script.py |
| Helper used by 2+ migrated tools | Copy to `GistamaBIM.extension/lib/` |
| Helper is very large (>80 lines) | Always copy to lib/, don't inline |
| `compat.py` (ElementId compat) | Always copy to lib/ — every tool needs it |

---

## Things to Ask Pras Before Migrating

1. Which tools does he want to migrate? (get list first)
2. Are there tools that depend on Google Sheets or external API calls? (flag — don't migrate those)
3. Does he want the `lib/` folder pre-seeded with `compat.py` from the start?

---

## Notes

- Never migrate the Google Sheets logging hook — personal infrastructure
- Never migrate `hooks/` folder unless Pras explicitly asks
- WPF dialogs: migrate as-is but flag if they reference PrasKaaPyKitv2-specific config files
- Dynamo scripts are out of scope — this agent handles pyRevit `.pushbutton` scripts only
- After migration, the tool should also pass the `gistama-release` checklist before pushing to GitHub
