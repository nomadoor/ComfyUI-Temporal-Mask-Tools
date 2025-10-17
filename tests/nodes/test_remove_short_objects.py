import pytest
import torch

from comfy_api.latest import io  # required for node registration

pytest.importorskip("numpy")
pytest.importorskip("cv2")

from nodes.temporal_mask_remove_short_objects import TemporalMaskRemoveShortObjects


def _stack(*frames):
    tensors = [torch.tensor(frame, dtype=torch.float32) for frame in frames]
    return torch.stack(tensors, dim=0)


def test_single_frame_flicker_is_removed():
    mask = _stack(
        [[0, 0, 0, 0]],
        [[1, 0, 0, 0]],
        [[0, 0, 0, 0]],
    )

    output = TemporalMaskRemoveShortObjects.execute(
        mask_batch=mask,
        min_duration=2,
        min_area_pixels=0,
    ).mask_batch_out

    assert output.sum() == 0


def test_large_object_survives_filters():
    mask = _stack(
        [[0, 0, 0, 0]],
        [[1, 1, 1, 1]],
        [[1, 1, 1, 1]],
        [[0, 0, 0, 0]],
    )

    output = TemporalMaskRemoveShortObjects.execute(
        mask_batch=mask,
        min_duration=2,
        min_area_pixels=1,
    ).mask_batch_out

    assert torch.allclose(output[1], mask[1])
    assert torch.allclose(output[2], mask[2])


def test_small_connected_component_removed():
    mask = _stack(
        [[0, 0, 0, 0]],
        [[0, 0, 1, 0]],
        [[0, 0, 0, 0]],
        [[0, 0, 0, 0]],
    )

    output = TemporalMaskRemoveShortObjects.execute(
        mask_batch=mask,
        min_duration=1,
        min_area_pixels=5,
    ).mask_batch_out

    assert output.sum() == 0


