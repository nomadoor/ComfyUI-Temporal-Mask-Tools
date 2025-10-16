# ComfyUI Temporal Mask Tools

Utility collection for ComfyUI focused on stabilizing per-frame segmentation masks.

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

## Usage
1. Clone into `ComfyUI/custom_nodes` and restart ComfyUI.
2. Drop `Temporal Mask Union` into your graph and point it at a mask sequence batch.
3. Optional: enable `debug_output` when tuning parameters; disable for production runs.

## Roadmap / TODO
- Implement `Temporal Mask Fill Gaps`.
- Implement `Temporal Mask Denoise`.
- Add automated tests under `tests/nodes/` once additional nodes land.