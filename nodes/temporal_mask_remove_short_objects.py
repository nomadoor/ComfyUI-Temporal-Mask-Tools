"""Temporal Mask Remove Short Objects node for ComfyUI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import torch
from torch import Tensor
import cv2

from comfy_api.latest import io

CATEGORY: Final[str] = "TemporalMask/Operations"


def _ensure_batch_time_shape(mask: Tensor) -> tuple[Tensor, tuple[int, ...]]:
    original_shape = mask.shape
    if mask.ndim == 2:
        mask = mask.unsqueeze(0).unsqueeze(0)
    elif mask.ndim == 3:
        mask = mask.unsqueeze(0)
    elif mask.ndim != 4:
        raise ValueError("mask_batch must have 2, 3, or 4 dimensions")
    return mask, original_shape


def _restore_shape(mask: Tensor, original_shape: tuple[int, ...]) -> Tensor:
    return mask.reshape(original_shape)


def _prepare_mask(mask: Tensor) -> Tensor:
    if mask.dtype == torch.bool:
        return mask
    if mask.dtype.is_floating_point:
        return mask > 0.0
    return mask != 0


def _finalize_dtype(out_mask: Tensor, reference: Tensor) -> Tensor:
    if reference.dtype == torch.bool:
        return out_mask > 0.0
    return out_mask.to(dtype=reference.dtype)


def _filter_small_components(frame_bool: np.ndarray, min_area_pixels: int) -> np.ndarray:
    if not frame_bool.any():
        return frame_bool
    if min_area_pixels <= 0:
        return frame_bool

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(frame_bool.astype(np.uint8), connectivity=8)
    output = np.zeros_like(frame_bool, dtype=bool)
    for label in range(1, int(num_labels)):
        if stats[label, cv2.CC_STAT_AREA] >= min_area_pixels:
            output[labels == label] = True
    return output


def _prune_area(mask_bool: Tensor, min_area_pixels: int) -> Tensor:
    if min_area_pixels <= 0:
        return mask_bool
    batch, frames, height, width = mask_bool.shape
    mask_np = mask_bool.cpu().numpy()
    result = np.zeros_like(mask_np, dtype=bool)
    for b in range(batch):
        for t in range(frames):
            result[b, t] = _filter_small_components(mask_np[b, t], min_area_pixels)
    return torch.from_numpy(result).to(mask_bool.device)


def _prune_duration(mask_bool: Tensor, min_duration: int) -> Tensor:
    if min_duration <= 1:
        return mask_bool
    batch, frames, height, width = mask_bool.shape
    flat = mask_bool.view(batch, frames, -1)
    lengths = torch.zeros_like(flat, dtype=torch.int32)
    running = torch.zeros((batch, flat.shape[2]), dtype=torch.int32, device=mask_bool.device)
    for t in range(frames):
        active = flat[:, t, :]
        running = torch.where(active, running + 1, torch.zeros_like(running))
        lengths[:, t, :] = running
    running.zero_()
    for t in range(frames - 1, -1, -1):
        active = flat[:, t, :]
        running = torch.where(active, running + 1, torch.zeros_like(running))
        lengths[:, t, :] += running - 1
    keep = lengths >= min_duration
    return (flat & keep).view(batch, frames, height, width)


class TemporalMaskRemoveShortObjects(io.ComfyNode):
    """Remove temporal mask activations that are too short or too small."""

    RELATIVE_PYTHON_MODULE: Final[str] = "nodes"

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="TemporalMaskRemoveShortObjects",
            display_name="Temporal Mask Remove Short Objects",
            category=CATEGORY,
            description="Remove transient or tiny activations from temporal masks based on duration/area thresholds.",
            inputs=[
                io.Mask.Input("mask_batch", display_name="Mask Sequence"),
                io.Int.Input(
                    "min_duration",
                    default=2,
                    min=1,
                    max=64,
                    step=1,
                    display_name="Min Duration",
                    tooltip="Minimum consecutive frames required to keep a pixel active.",
                ),
                io.Int.Input(
                    "min_area_pixels",
                    default=10,
                    min=0,
                    max=1_000_000,
                    step=1,
                    display_name="Min Area (pixels)",
                    tooltip="Connected components with fewer active pixels than this are removed.",
                ),
            ],
            outputs=[io.Mask.Output("mask_batch_out", display_name="Mask Batch")],
        )

    @classmethod
    def validate_inputs(
        cls,
        min_duration: int,
        min_area_pixels: int,
        **_: dict,
    ) -> bool | str:
        if min_duration < 1:
            return "min_duration must be at least 1"
        if min_area_pixels < 0:
            return "min_area_pixels must be non-negative"
        return True

    @classmethod
    def execute(
        cls,
        mask_batch: Tensor,
        min_duration: int,
        min_area_pixels: int,
    ) -> io.NodeOutput:
        mask_norm, orig_shape = _ensure_batch_time_shape(mask_batch)
        mask_bool = _prepare_mask(mask_norm)

        area_filtered = _prune_area(mask_bool, min_area_pixels)
        duration_filtered = _prune_duration(area_filtered, min_duration)

        result = duration_filtered.to(dtype=mask_norm.dtype)
        result = _restore_shape(result, orig_shape)

        return io.NodeOutput(result)


