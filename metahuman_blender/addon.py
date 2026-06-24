from __future__ import annotations

import logging

from .ops import bake_to_metahuman, build_body_rig, evaluate_body, evaluate_face, groom_io, import_dna
from .ui import panels, properties

LOGGER = logging.getLogger(__name__)

MODULES = (
    properties,
    import_dna,
    build_body_rig,
    evaluate_body,
    bake_to_metahuman,
    evaluate_face,
    groom_io,
    panels,
)


def register():
    logging.basicConfig(level=logging.INFO)
    for module in MODULES:
        module.register()
    from .riglogic.body_evaluator import register_handlers

    register_handlers()
    LOGGER.info("MetaHuman Blender add-on registered")


def unregister():
    for module in reversed(MODULES):
        module.unregister()
    LOGGER.info("MetaHuman Blender add-on unregistered")
