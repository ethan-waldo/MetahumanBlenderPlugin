from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from .scene_model import sanitize_name


class ExportManifestError(RuntimeError):
    pass


@dataclass(slots=True)
class ExportManifest:
    path: Path
    meta_human_name: str
    body_dna_path: Path
    head_dna_path: Path | None = None
    thumbnail_path: Path | None = None
    maps_folder: Path | None = None
    masks_folder: Path | None = None
    map_files: list[Path] = field(default_factory=list)
    mask_files: list[Path] = field(default_factory=list)
    export_plugin_version: str = ""
    export_engine_version: str = ""
    exported_at: str = ""

    @property
    def character_name(self) -> str:
        return sanitize_name(self.meta_human_name)

    @property
    def export_root(self) -> Path:
        return self.path.parent


def load_export_manifest(path: str | Path) -> ExportManifest:
    manifest_path = Path(path).expanduser().resolve()
    if not manifest_path.exists():
        raise ExportManifestError(f"Export manifest does not exist: {manifest_path}")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportManifestError(f"Invalid export manifest JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ExportManifestError("Export manifest root must be a JSON object.")

    root = manifest_path.parent
    dna = payload.get("dna") or {}
    if not isinstance(dna, dict):
        raise ExportManifestError("Export manifest 'dna' section must be an object.")

    body_relative = dna.get("body")
    if not body_relative:
        raise ExportManifestError("Export manifest is missing dna.body.")

    body_dna_path = _resolve_path(root, body_relative)
    if not body_dna_path.exists():
        raise ExportManifestError(f"Body DNA not found: {body_dna_path}")

    head_dna_path = None
    head_relative = dna.get("head")
    if head_relative:
        candidate = _resolve_path(root, head_relative)
        if candidate.exists():
            head_dna_path = candidate

    folders = payload.get("folders") or {}
    files = payload.get("files") or {}
    maps_folder = _resolve_optional_folder(root, folders, "maps")
    masks_folder = _resolve_optional_folder(root, folders, "masks")
    map_files = _resolve_file_list(maps_folder, files.get("maps"))
    mask_files = _resolve_file_list(masks_folder, files.get("masks"))

    thumbnail_path = None
    thumbnail_relative = payload.get("thumbnail")
    if thumbnail_relative:
        candidate = _resolve_path(root, thumbnail_relative)
        if candidate.exists():
            thumbnail_path = candidate

    return ExportManifest(
        path=manifest_path,
        meta_human_name=str(payload.get("metaHumanName") or root.name),
        body_dna_path=body_dna_path,
        head_dna_path=head_dna_path,
        thumbnail_path=thumbnail_path,
        maps_folder=maps_folder,
        masks_folder=masks_folder,
        map_files=map_files,
        mask_files=mask_files,
        export_plugin_version=str(payload.get("exportPluginVersion") or ""),
        export_engine_version=str(payload.get("exportEngineVersion") or ""),
        exported_at=str(payload.get("exportedAt") or ""),
    )


def find_export_manifest(path: str | Path) -> Path | None:
    candidate = Path(path).expanduser()
    if candidate.is_file() and candidate.suffix.lower() == ".json":
        lowered = candidate.name.lower()
        if lowered in {"exportmanifest.json", "manifest.json"}:
            return candidate.resolve()

    if candidate.is_dir():
        for name in ("ExportManifest.json", "exportmanifest.json", "Manifest.json"):
            manifest = candidate / name
            if manifest.exists():
                return manifest.resolve()
    return None


def _resolve_path(root: Path, relative: str) -> Path:
    return (root / relative).resolve()


def _resolve_optional_folder(root: Path, folders: dict, key: str) -> Path | None:
    relative = folders.get(key)
    if not relative:
        return None
    folder = _resolve_path(root, relative)
    return folder if folder.exists() else None


def _resolve_file_list(folder: Path | None, names) -> list[Path]:
    if folder is None or not isinstance(names, list):
        return []
    files: list[Path] = []
    for name in names:
        candidate = folder / str(name)
        if candidate.exists():
            files.append(candidate)
    return files
