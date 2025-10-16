---
version: 1.0
created: 2025-10-16
status: draft
related_adr: null
---

# 002: Temporal Mask Fill Gaps

## Purpose
Fill short gaps (≤ N frames) between active mask segments to ensure temporal continuity.

## Inputs
| Name | Type | Required | Default | Description |
|------|------|-----------|----------|-------------|
| mask_batch | MASK | Yes | — | Input temporal mask sequence |
| max_gap_frames | INT | No | 3 | Maximum gap to fill |
| interpolation | STRING | No | "hold" | Fill strategy ("hold"/"linear") |
| min_duration | INT | No | 2 | Minimum valid segment length |
| debug_output | BOOL | No | False | Debug visualization mask |

## Outputs
| Name | Type | Description |
|------|------|-------------|
| mask_batch_out | MASK | Gap-filled mask sequence |

## Processing Logic
1. Detect inactive spans shorter than `max_gap_frames`.  
2. If found, fill based on `interpolation`.  
3. Respect `min_duration` to avoid overfilling.  
4. Return smoothed mask sequence.

## Dependencies
- **Internal**: None  
- **External**: `torch`  
- **Optional**: Works with `Temporal Mask Union` output  

## Test Cases
### TC-001: Fill short gap
gap=2 → filled  
### TC-002: Ignore long gap
gap=4 → unchanged  
### TC-003: Apply min_duration
short activations removed  

## Validation Checklist
- [ ] Schema V3 compliant  
- [ ] Handles edge frames  
- [ ] GPU compatible  
- [ ] No unsafe imports  
- [ ] Unit test in `tests/nodes/test_fill_gaps.py`  
- [ ] ADR entry exists  
