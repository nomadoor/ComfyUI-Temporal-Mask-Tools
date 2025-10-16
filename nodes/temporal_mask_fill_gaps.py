"""Temporal Mask Fill Gaps node implementation for ComfyUI."""
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
    elif mask.ndim != 4:
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


def _compute_segment_bounds(mask_bool: Tensor) -> tuple[Tensor, Tensor, Tensor]:
    """Return lengths, starts, and ends of active segments per frame."""
    if mask_bool.ndim != 3:
        raise ValueError("mask_bool must have shape (batch, frames, features)")

    batch, frames, features = mask_bool.shape
    device = mask_bool.device
    time_indices = torch.arange(frames, dtype=torch.int64, device=device)

    starts = torch.full((batch, frames, features), -1, dtype=torch.int64, device=device)
    ends = torch.full((batch, frames, features), -1, dtype=torch.int64, device=device)

    current_start = torch.full((batch, features), -1, dtype=torch.int64, device=device)
    neg_one = torch.full((batch, features), -1, dtype=torch.int64, device=device)
    for idx in range(frames):
        active = mask_bool[:, idx, :]
        current_start = torch.where(
            active & (current_start < 0),
            time_indices[idx],
            current_start,
        )
        starts[:, idx, :] = torch.where(active, current_start, neg_one)
        current_start = torch.where(~active, neg_one, current_start)

    current_end = torch.full((batch, features), -1, dtype=torch.int64, device=device)
    neg_one_end = neg_one  # reuse allocation
    for idx in range(frames - 1, -1, -1):
        active = mask_bool[:, idx, :]
        current_end = torch.where(
            active & (current_end < 0),
            time_indices[idx],
            current_end,
        )
        ends[:, idx, :] = torch.where(active, current_end, neg_one_end)
        current_end = torch.where(~active, neg_one_end, current_end)

    lengths = torch.where(
        mask_bool,
        ends - starts + 1,
        torch.zeros(1, dtype=torch.int64, device=device),
    )
    return lengths, starts, ends


def _compute_last_next_indices(mask_bool: Tensor) -> tuple[Tensor, Tensor]:
    """Return per-frame indices of the previous and next active frames."""
    if mask_bool.ndim != 3:
        raise ValueError("mask_bool must have shape (batch, frames, features)")

    batch, frames, features = mask_bool.shape
    device = mask_bool.device
    time_indices = torch.arange(frames, dtype=torch.int64, device=device)

    last_indices = torch.full((batch, frames, features), -1, dtype=torch.int64, device=device)
    current_last = torch.full((batch, features), -1, dtype=torch.int64, device=device)
    for idx in range(frames):
        active = mask_bool[:, idx, :]
        current_last = torch.where(active, time_indices[idx], current_last)
        last_indices[:, idx, :] = current_last

    next_indices = torch.full((batch, frames, features), frames, dtype=torch.int64, device=device)
    current_next = torch.full((batch, features), frames, dtype=torch.int64, device=device)
    for idx in range(frames - 1, -1, -1):
        active = mask_bool[:, idx, :]
        current_next = torch.where(active, time_indices[idx], current_next)
        next_indices[:, idx, :] = current_next

    return last_indices, next_indices


class TemporalMaskFillGaps(io.ComfyNode):
    """Fill short inactive spans between active mask segments using hold interpolation."""

    RELATIVE_PYTHON_MODULE: Final[str] = "nodes"

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="TemporalMaskFillGaps",
            display_name="Temporal Mask Fill Gaps",
            category=CATEGORY,
            description="Fill short gaps between active mask segments using hold interpolation.",
            inputs=[
                io.Mask.Input("mask_batch", display_name="Mask Sequence"),
                io.Int.Input(
                    "max_gap_frames",
                    default=3,
                    min=0,
                    max=64,
                    step=1,
                    display_name="Max Gap Frames",
                    tooltip="Inactive span (frames) eligible for filling.",
                ),
                io.Int.Input(
                    "min_duration",
                    default=2,
                    min=1,
                    max=64,
                    step=1,
                    display_name="Min Duration",
                    tooltip="Active segments shorter than this are removed before filling gaps.",
                ),
                io.Boolean.Input(
                    "debug_output",
                    default=False,
                    display_name="Debug Output",
                    tooltip="Print the node configuration for troubleshooting.",
                ),
            ],
            outputs=[io.Mask.Output("mask_batch_out", display_name="Mask Sequence")],
        )

    @classmethod
    def validate_inputs(
        cls,
        max_gap_frames: int,
        min_duration: int,
        **_: dict,
    ) -> bool | str:
        if max_gap_frames < 0:
            return "max_gap_frames must be non-negative"
        if min_duration < 1:
            return "min_duration must be at least 1"
        return True

    @classmethod
    def execute(
        cls,
        mask_batch: Tensor,
        max_gap_frames: int,
        min_duration: int,
        debug_output: bool,
    ) -> io.NodeOutput:
        mask_normalized, original_shape = _ensure_batch_time_shape(mask_batch)
        mask_bool = _prepare_mask(mask_normalized)

        batch, frames, height, width = mask_bool.shape
        features = height * width

        mask_bool_flat = mask_bool.reshape(batch, frames, features)

        if min_duration > 1:
            segment_lengths, segment_starts, segment_ends = _compute_segment_bounds(mask_bool_flat)
            mask_bool_flat = mask_bool_flat & (
                (segment_ends - segment_starts + 1) >= min_duration
            )

        mask_bool_filtered = mask_bool_flat

        mask_values = mask_normalized.to(dtype=torch.float32).reshape(batch, frames, features)
        result_values = torch.where(
            mask_bool_filtered,
            mask_values,
            torch.zeros_like(mask_values),
        )

        if max_gap_frames > 0:
            last_idx, next_idx = _compute_last_next_indices(mask_bool_filtered)
            gap_sizes = next_idx - last_idx - 1

            fill_positions = (
                ~mask_bool_filtered
                & (last_idx >= 0)
                & (next_idx < frames)
                & (gap_sizes > 0)
                & (gap_sizes <= max_gap_frames)
            )

            if fill_positions.any().item():
                gather_last = torch.gather(
                    mask_values,
                    dim=1,
                    index=last_idx.clamp(min=0),
                )
                fill_values = gather_last
                result_values = torch.where(fill_positions, fill_values, result_values)
                mask_bool_filtered = mask_bool_filtered | fill_positions

        result = result_values.reshape(batch, frames, height, width)

        if mask_normalized.dtype == torch.bool:
            result = result > 0.0
        else:
            result = result.to(mask_normalized.dtype)

        result = _restore_shape(result, original_shape)

        if debug_output:
            print(
                "[TemporalMaskFillGaps] debug:",
                f"shape={tuple(original_shape)}",
                f"max_gap={max_gap_frames}",
                f"min_duration={min_duration}",
            )

        return io.NodeOutput(result)
