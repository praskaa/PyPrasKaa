# PrasKaaPyKit - Agent Instructions

## Project Overview
PrasKaaPyKit is a pyRevit extension for Autodesk Revit automation. All scripts run exclusively from pyRevit UI — never standalone.

## Architecture Rules
1. **No sys.path manipulation** — pyRevit auto-adds root extension folder to sys.path
2. **Import from `lib/` only** — never import from `logic-library/` (documentation only)
3. **Explicit imports** — no wildcard (`from module import *`)
4. **Import order**: stdlib → pyRevit → Revit API → local lib
5. **Remove unused imports** — especially `sys` and `os` if only used for path setup

## Key Paths
- Root: `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaPyKitv2.extension`
- Shared libs: `lib/`
- Documentation: `logic-library/` (DO NOT import from here)
- Kilo config: `kilo.json`, `.kilo/`

## Commands
- `/lint-imports` - Check Python files for import violations
- `/refactor-imports` - Auto-fix import violations in files
