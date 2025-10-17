# ADR: Temporal Mask Remove Short Objects

## Context
- Requirement `docs/requirements/004-Temporal-Mask-Remove-Short-Objects.md` calls for eliminating tiny or short-lived activations that slip past union/interpolation stages.
- Temporal flicker and single-frame specks degrade downstream temporal consistency, so we need a lightweight cleanup node compatible with Torch-only pipelines.

## Decision
- Implemented `nodes/temporal_mask_remove_short_objects.py`:
  - Normalizes masks to `(B,T,H,W)`, then filters each frame with OpenCV `connectedComponentsWithStats`, removing components below `min_area_pixels`.
  - Performs temporal run-length pruning per pixel to drop activations shorter than `min_duration`.
  - Exposes schema inputs (`min_duration`, `min_area_pixels`) matching the requirement.
- Added unit coverage in `tests/nodes/test_remove_short_objects.py` for flicker removal, large-object retention, and tiny-component rejection.
- Registered the node in `TemporalMaskToolsExtension` so it loads with the existing temporal mask toolset.

## Consequences
- Users can chain the node after union/morph to suppress residual noise without rewriting graphs.
- Dependency footprint stays minimal (torch + numpy/OpenCV already present); Pillow remains optional for future visualization tooling if needed.
- Temporal helpers (normalization, dtype restoration) remain consistent across nodes, easing maintenance.


