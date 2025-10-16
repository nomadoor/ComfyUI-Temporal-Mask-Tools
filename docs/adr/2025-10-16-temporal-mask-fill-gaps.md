# ADR: Temporal Mask Fill Gaps Node

## Context
- Requirement `docs/requirements/002-temporal-mask-fill-gaps.md` requests a node to bridge brief inactive spans in temporal masks.
- Existing `TemporalMaskUnion` already stabilizes masks but does not reconstruct short drop-outs.
- We must stay compatible with ComfyUI V3 schema and avoid unsafe dependencies.

## Decision
- Implemented `nodes/temporal_mask_fill_gaps.py` with schema-compliant inputs/outputs.
- Normalize masks to `(batch, frames, height, width)` using shared helper functions and process per-pixel sequences on the GPU-friendly tensor path.
- Remove active segments shorter than `min_duration` before filling and interpolate gaps up to `max_gap_frames` via either hold or linear strategies.
- Update extension registry to expose both union and fill-gaps nodes.

## Consequences
- Users can smooth short drop-outs without writing custom graphs.
- Additional unit tests are still pending (`tests/nodes/test_fill_gaps.py`).
- Future nodes should reuse the helper logic; consider refactoring into a shared utility module once the API stabilizes.
