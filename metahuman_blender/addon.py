from __future__ import annotations

import logging

from .ops import bake_to_metahuman, build_body_rig, evaluate_body, evaluate_face, groom_io, import_dna, import_faceboard, import_head_dna, import_manifest, setup_materials
from .ui import face_sliders, panels, properties

LOGGER = logging.getLogger(__name__)

MODULES = (
    face_sliders,
    properties,
    import_manifest,
    setup_materials,
    import_dna,
    import_head_dna,
    import_faceboard,
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
    from .riglogic.body_evaluator import register_handlers as register_body_handlers
    from .riglogic.evaluator import register_handlers as register_face_handlers

    register_body_handlers()
    register_face_handlers()
    LOGGER.info("MetaHuman Blender add-on registered")


def unregister():
    from .riglogic.body_evaluator import unregister_handlers as unregister_body_handlers, clear_cache as clear_body_cache
    from .riglogic.evaluator import unregister_handlers as unregister_face_handlers, clear_cache as clear_face_cache

    unregister_body_handlers()
    unregister_face_handlers()
    clear_body_cache()
    clear_face_cache()
    for module in reversed(MODULES):
        module.unregister()
    LOGGER.info("MetaHuman Blender add-on unregistered")
