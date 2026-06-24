from __future__ import annotations

from dataclasses import dataclass

from .bindings import validate_bindings


@dataclass(slots=True)
class EvaluationResult:
    ok: bool
    message: str


class FaceRigLogicEvaluator:
    """Thin placeholder for phase 3 RigLogic evaluation.

    The body milestone ships with dependency validation and a non-mutating
    current-frame command. Actual control decoding and output application live
    behind this class so phase 3 does not need to touch operator/UI plumbing.
    """

    def __init__(self, binding_paths: list[str] | None = None):
        self.binding_paths = binding_paths or []

    @classmethod
    def from_context(cls, context) -> "FaceRigLogicEvaluator":
        from ..ui.properties import _binding_paths_from_preferences

        return cls(_binding_paths_from_preferences(context))

    def evaluate_current_frame(self) -> EvaluationResult:
        status = validate_bindings(self.binding_paths)
        if not status.available:
            return EvaluationResult(False, status.message)
        if status.riglogic_module is None:
            return EvaluationResult(False, "RigLogic bindings are not available. Body rigging can still be used.")
        return EvaluationResult(
            True,
            "RigLogic bindings are available. Facial output application is reserved for the phase 3 evaluator.",
        )
