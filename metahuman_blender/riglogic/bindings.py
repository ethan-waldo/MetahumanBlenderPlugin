from __future__ import annotations

from dataclasses import dataclass, field
import importlib
from pathlib import Path
import sys
from types import ModuleType


@dataclass(slots=True)
class BindingStatus:
    available: bool
    message: str
    dna_module: ModuleType | None = None
    riglogic_module: ModuleType | None = None
    search_paths: list[str] = field(default_factory=list)


def add_binding_paths(paths: list[str] | tuple[str, ...] | None) -> list[str]:
    added: list[str] = []
    for raw_path in paths or []:
        if not raw_path:
            continue
        for path in _expand_binding_path(Path(raw_path).expanduser()):
            path_text = str(path)
            if path_text not in sys.path:
                sys.path.insert(0, path_text)
                added.append(path_text)
    return added


def _expand_binding_path(path: Path) -> list[Path]:
    candidates = [path]
    common_children = [
        path / "dna",
        path / "riglogic",
        path / "python" / "dna",
        path / "python" / "riglogic",
    ]
    for child in common_children:
        if child.exists():
            candidates.append(child)
    return candidates


def validate_bindings(extra_paths: list[str] | tuple[str, ...] | None = None) -> BindingStatus:
    added = add_binding_paths(extra_paths)
    try:
        dna_module = importlib.import_module("dna")
    except Exception as exc:
        return BindingStatus(
            available=False,
            message=f"Could not import OpenRigLogic DNA bindings: {exc}",
            search_paths=added,
        )

    riglogic_module = None
    riglogic_errors: list[str] = []
    for module_name in ("riglogic", "rl4"):
        try:
            riglogic_module = importlib.import_module(module_name)
            break
        except Exception as exc:
            riglogic_errors.append(f"{module_name}: {exc}")

    if riglogic_module is None:
        return BindingStatus(
            available=True,
            message="DNA bindings are available. RigLogic bindings were not found yet; body import can continue.",
            dna_module=dna_module,
            riglogic_module=None,
            search_paths=added,
        )

    return BindingStatus(
        available=True,
        message="OpenRigLogic DNA and RigLogic bindings are available.",
        dna_module=dna_module,
        riglogic_module=riglogic_module,
        search_paths=added,
    )
