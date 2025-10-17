"""ComfyUI entrypoint registering temporal mask nodes."""
from __future__ import annotations

from comfy_api.latest import ComfyExtension, io

from .temporal_mask_union import TemporalMaskUnion
from .temporal_mask_remove_short_objects import TemporalMaskRemoveShortObjects


class TemporalMaskToolsExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [TemporalMaskUnion, TemporalMaskRemoveShortObjects]


async def comfy_entrypoint() -> ComfyExtension:
    return TemporalMaskToolsExtension()
