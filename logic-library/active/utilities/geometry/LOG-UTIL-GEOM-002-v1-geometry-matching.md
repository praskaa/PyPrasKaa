# LOG-UTIL-GEOM-002-v1: Geometry Matching Library

## Overview
Reusable lib for EXR framing sync: match host/linked beams by intersect vol.

## Interface
`match_beams(...) → {'matches': [(host, linked, vol)], 'stats': {'time_s', 'match_rate'}}`

## Implementation
- get_solid: Union solids from geom/GeomInstance
- find_best_match: Max intersect vol > thresh
- Baseline O(N*M), future bbox opt

## Usage
```python
from lib.geometry_matching import match_beams
res = match_beams()
```

## Perf Baseline
Test w/ [TestGeometryMatching](PrasKaaPyKit.tab/QualityControl.panel/EXR_Framing.pulldown/TestGeometryMatching.pushbutton/script.py)

## Design Decisions
- No transform (assume aligned)
- Vol thresh 1e-9 cu ft
- Preselect/all support

Ref: [geometry_matching_plan.md](lib/geometry_matching_plan.md)