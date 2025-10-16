---
version: 1.0
created: 2025-10-16
status: draft
related_adr: null
---

# 003: Temporal Mask Denoise

## Purpose
Remove transient detections lasting fewer than `min_duration` frames to stabilize segmentation masks.

## Inputs
| Name | Type | Required | Default | Description |
|------|------|-----------|----------|-------------|
| mask_batch | MASK | Yes | — | Input temporal mask sequence |
| min_duration | INT | No | 3 | Minimum allowed activation duration |
| mode | STRING | No | "strict" | Filtering mode ("strict"/"loose") |
| edge_behavior | STRING | No | "keep" | Behavior for start/end frames |
| debug_output | BOOL | No | False | Optional visualization mask |

## Outputs
| Name | Type | Description |
|------|------|-------------|
| mask_batch_out | MASK | Denoised temporal mask sequence |

## Processing Logic
1. Identify contiguous active segments.  
2. If segment length < `min_duration`, remove or weaken per `mode`.  
3. Handle boundaries per `edge_behavior`.  
4. Return cleaned mask sequence.

## Dependencies
- **Internal**: None  
- **External**: `torch`  
- **Optional**: `Temporal Mask Fill Gaps` (for pre-smoothed input)  

## Test Cases
### TC-001: Short burst removal
min_duration=3 → 1-frame activations removed  
### TC-002: Edge retention
edge_behavior="keep" → retain start/end frames  
### TC-003: Loose mode
mode="loose" → fewer removals  

## Validation Checklist
- [ ] Schema V3 compliant  
- [ ] Edge handling correct  
- [ ] No unsafe imports  
- [ ] GPU support verified  
- [ ] Unit test in `tests/nodes/test_denoise.py`  
- [ ] ADR entry exists  
