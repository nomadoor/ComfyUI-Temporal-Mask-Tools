"""Temporal Mask Union node implementation for ComfyUI."""
from __future__ import annotations

from typing import Final

import torch
from torch import Tensor

from comfy_api.latest import io

CATEGORY: Final[str] = "TemporalMask/Operations"


def _ensure_batch_time_shape(mask: Tensor) -> tuple[Tensor, tuple[int, ...]]:
    """Normalize mask to (batch, frames, height, width) and return original shape."""
    original_shape = mask.shape
    if mask.ndim == 2:
        mask = mask.unsqueeze(0).unsqueeze(0)
    elif mask.ndim == 3:
        mask = mask.unsqueeze(0)
    elif mask.ndim == 4:
        pass
    else:
        raise ValueError("mask_batch must have 2, 3, or 4 dimensions")
    return mask, original_shape


def _restore_shape(mask: Tensor, original_shape: tuple[int, ...]) -> Tensor:
    """Restore tensor to its original dimensionality."""
    if not original_shape:
        return mask
    return mask.reshape(original_shape)


def _prepare_mask(mask: Tensor) -> Tensor:
    """Convert mask to a boolean tensor for logical operations."""
    if mask.dtype == torch.bool:
        return mask
    if mask.dtype.is_floating_point:
        return mask > 0.0  # treat any positive value as active
    if mask.dtype in (torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64):
        return mask != 0
    raise TypeError("mask_batch must be bool or numeric tensor")


def _validate_mode(mode: str) -> str:
    norm = mode.lower()
    if norm not in {"or", "majority"}:
        raise ValueError("mode must be 'or' or 'majority'")
    return norm


def _window_majority(counts: Tensor, threshold: int, window_size: int) -> Tensor:
    effective_threshold = max(1, min(threshold, window_size))
    return counts >= effective_threshold


class TemporalMaskUnion(io.ComfyNode):
    """Combine nearby temporal mask frames using logical OR or majority voting."""

    RELATIVE_PYTHON_MODULE: Final[str] = "nodes"

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="TemporalMaskUnion",
            display_name="Temporal Mask Union",
            category=CATEGORY,
            description=(
                "Combine nearby temporal mask frames using logical OR or majority voting "
                "to stabilize transient detections."
            ),
            inputs=[
                io.Mask.Input("mask_batch", display_name="Mask Sequence"),
                io.Int.Input(
                    "radius",
                    default=2,
                    min=0,
                    max=32,
                    step=1,
                    display_name="Radius",
                    tooltip="Half width of the temporal window (frames).",
                ),
                io.Combo.Input(
                    "mode",
                    options=["or", "majority"],
                    default="or",
                    display_name="Mode",
                    tooltip="'or' unions any active frame; 'majority' requires the threshold count.",
                ),
                io.Int.Input(
                    "threshold",
                    default=3,
                    min=1,
                    max=64,
                    step=1,
                    display_name="Threshold",
                    tooltip="Frames within the window that must be active when using majority mode.",
                ),
            ],
            outputs=[
                io.Mask.Output("mask_batch_out", display_name="Mask Batch"),
            ],
        )

    @classmethod
    def validate_inputs(
        cls,
        radius: int,
        threshold: int,
        **_: dict,
    ) -> bool | str:
        if radius < 0:
            return "radius must be non-negative"
        if threshold < 1:
            return "threshold must be at least 1"
        return True

    @classmethod
    def execute(
        cls,
        mask_batch: Tensor,
        radius: int,
        mode: str,
        threshold: int,
    ) -> io.NodeOutput:
        normalized_mode = _validate_mode(mode)
        mask_normalized, original_shape = _ensure_batch_time_shape(mask_batch)
        mask_bool = _prepare_mask(mask_normalized)

        window_size = radius * 2 + 1
        batch, frames, height, width = mask_bool.shape

        mask_float = mask_bool.reshape(batch, frames, -1).transpose(1, 2).to(dtype=torch.float32)
        padded = torch.nn.functional.pad(mask_float, (radius, radius)) if radius > 0 else mask_float
        windows = padded.unfold(dimension=2, size=window_size, step=1)

        if normalized_mode == "or":
            merged_flat = windows.amax(dim=3) > 0.0
        else:
            counts = windows.sum(dim=3)
            merged_flat = _window_majority(counts, threshold, window_size)

        merged_bool = merged_flat.transpose(1, 2).contiguous().reshape(batch, frames, height, width)
        merged = merged_bool.to(mask_normalized.dtype)
        merged = _restore_shape(merged, original_shape)
        return io.NodeOutput(merged)


