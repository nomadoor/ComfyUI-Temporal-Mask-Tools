---
version: 1.0
created: 2025-10-17
status: draft
related_adr: docs/adr/2025-10-17-remove-short-objects.md
---

# 004: Temporal Mask Remove Short Objects

## Purpose
Remove transient or tiny mask activations that appear for a short duration or occupy an extremely small area.  
This node complements `Temporal Mask Union` by cleaning up noisy, one-frame artifacts such as flickering or mis-segmented pixels.

## Motivation
Even after temporal union and interpolation, mask sequences often contain **one-frame blinks** or **tiny specks** caused by unstable object detection.  
These artifacts can degrade downstream consistency in video segmentation, temporal blending, and mask-guided generation.  
This node provides a fast, GPU-optional filtering stage to remove such outliers.

## Inputs
| Name | Type | Required | Default | Description |
|------|------|-----------|----------|-------------|
| mask_batch | MASK | Yes |  | Input temporal mask sequence |
| min_duration | INT | No | 2 | Minimum number of consecutive active frames to keep |
| min_area_pixels | INT | No | 10 | Minimum connected-component area (pixels) to keep |

## Outputs
| Name | Type | Description |
|------|------|-------------|
| mask_batch_out | MASK | Cleaned mask sequence with short or small activations removed |

## Processing Logic
1. Normalize input to `(B, T, H, W)` and ensure boolean mask.
2. For each batch and frame, run `cv2.connectedComponentsWithStats` to detect connected components.
   - Remove any component whose pixel area is below `min_area_pixels`.
3. Compute per-pixel temporal activation lengths and clear runs shorter than `min_duration`.
4. Combine area and duration masks to produce the cleaned result.
5. Restore dtype (bool/float) and original shape.
6. Optionally report removal statistics (implementation-dependent).

## Dependencies
- **Internal:** `torch`, `torch.nn.functional`
- **External:** `opencv-python`, `numpy`
- **Optional:** `Pillow` (only when debug visualization is enabled)

## Test Cases
| ID | Description | Expected |
|----|--------------|-----------|
| TC-001 | Single-frame flicker | Flicker removed; persistent regions kept |
| TC-002 | 3-frame object with `min_duration=5` | Region removed |
| TC-003 | Tiny object (area < min_area_pixels) | Region removed |
| TC-004 | Large stable object | Unchanged |
| TC-005 | Multiple objects, mixed sizes | Only small/short ones removed |

## Validation Checklist
- [x] Schema V3 compliant  
- [x] Handles both 2D and 3D masks  
- [x] Robust to noisy per-frame segmentation  
- [x] Works without GPU acceleration  
- [x] Compatible with Temporal Mask Union output  
- [x] Unit test in `tests/nodes/test_remove_short_objects.py`





