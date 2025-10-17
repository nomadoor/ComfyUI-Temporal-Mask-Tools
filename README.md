# ComfyUI Temporal Mask Tools

Utility collection of ComfyUI V3 nodes for stabilizing temporal segmentation masks while staying deterministic and torch-only.

## Nodes

### Temporal Mask Union (`TemporalMaskUnion`)
Combines nearby frames in a temporal mask sequence to suppress flicker.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `mask_batch` | MASK | required | Accepts `(frames, H, W)`, `(batch, frames, H, W)`, or `(H, W)` tensors. |
| `radius` | INT | 2 | Temporal half-window size. |
| `mode` | STRING | `"or"` | `"or"` keeps any active frame, `"majority"` uses the threshold. |
| `threshold` | INT | 3 | Minimum active frames within the window when `mode="majority"`. |

**Output**: `mask_batch` ? mask tensor with original shape restored.

### Temporal Mask Remove Short Objects (`TemporalMaskRemoveShortObjects`)
Drops one-frame flicker or tiny specks by combining per-frame connected-component filtering with temporal run-length pruning.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `mask_batch` | MASK | required | Supports `(H, W)`, `(frames, H, W)`, `(batch, frames, H, W)` tensors. |
| `min_duration` | INT | 2 | Minimum consecutive frames required to keep a pixel active. |
| `min_area_pixels` | INT | 10 | Connected components smaller than this pixel count are removed. |

**Output**: `mask_batch`  Emask tensor with transient or tiny activations removed.

## Usage
1. Clone into `ComfyUI/custom_nodes` and restart ComfyUI.
2. Drop the desired node into your graph and connect it to a mask sequence batch.
3. Optional: enable node-level `debug_output` (when available) while tuning parameters.





