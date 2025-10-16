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
| `debug_output` | BOOL | False | Emits a concise log summarizing runtime parameters. |

**Output**: `mask_batch_out` — mask tensor with original shape restored.

### Temporal Mask Fill Gaps (`TemporalMaskFillGaps`)
Removes short-lived activations and fills brief inactive spans so the mask stays continuous from frame to frame. It first prunes active runs shorter than `min_duration`, then fills gaps no longer than `max_gap_frames` by holding the last active frame forward to cover detection dropouts.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `mask_batch` | MASK | required | Accepts `(frames, H, W)`, `(batch, frames, H, W)`, or `(H, W)` tensors. |
| `max_gap_frames` | INT | 3 | Maximum inactive span that will be filled. |
| `min_duration` | INT | 2 | Minimum length of an activation to keep. |
| `debug_output` | BOOL | False | Prints node parameters for quick verification. |

**Output**: `mask_batch_out` — mask tensor with short gaps filled while preserving input shape.

## Usage
1. Clone into `ComfyUI/custom_nodes` and restart ComfyUI.
2. Drop the desired node into your graph and connect it to a mask sequence batch.
3. Optional: enable `debug_output` when tuning parameters; disable for production runs.
