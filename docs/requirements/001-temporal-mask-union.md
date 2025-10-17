
---
version: 1.0
created: 2025-10-16
status: draft
related_adr: null
---

# 001: Temporal Mask Union

## Purpose
Combine nearby temporal mask frames using logical OR or majority voting to stabilize transient detections.

## Inputs
| Name | Type | Required | Default | Description |
|------|------|-----------|----------|-------------|
| mask_batch | MASK | Yes |  E| Input temporal mask sequence |
| radius | INT | No | 2 | Frame range for merging |
| mode | STRING | No | "or" | Merge mode ("or" / "majority") |
| threshold | INT | No | 3 | Frame count threshold |
| debug_output | BOOL | No | False | Output visualization mask |

## Outputs
| Name | Type | Description |
|------|------|-------------|
| mask_batch_out | MASK | Merged temporal mask |

## Processing Logic
1. For each frame, aggregate neighbor masks within ±radius.  
2. If `mode="or"` ↁEunion of all masks.  
3. If `mode="majority"` ↁEpixel active if ≥ `threshold` frames are active.  
4. Return batched mask tensor.

## Dependencies
- **Internal**: None  
- **External**: `torch`  
- **Optional**: None

## Test Cases
### TC-001: OR mode
Input: radius=1, mode="or" ↁEExpect union across neighbors  
### TC-002: Majority mode
Input: threshold=3 ↁEExpect tighter filtering  
### TC-003: Single frame
Expect unchanged output  

## Validation Checklist
- [ ] Schema V3 compliant  
- [ ] dtype=bool or float  
- [ ] torch operations only  
- [ ] No unsafe imports  
- [ ] Test coverage complete  
- [ ] ADR created if logic modified  



