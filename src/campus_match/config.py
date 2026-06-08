from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io_utils import ensure_dir, read_json


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data_dir: Path
    images_dir: Path
    indexes_dir: Path
    outputs_dir: Path

    @classmethod
    def from_config(cls, root: str | Path, config: dict[str, Any]) -> "ProjectPaths":
        root_path = Path(root).resolve()
        paths = config.get("paths", {})
        obj = cls(
            root=root_path,
            data_dir=root_path / paths.get("data_dir", "data"),
            images_dir=root_path / paths.get("images_dir", "images"),
            indexes_dir=root_path / paths.get("indexes_dir", "indexes"),
            outputs_dir=root_path / paths.get("outputs_dir", "outputs"),
        )
        for path in [obj.data_dir, obj.images_dir, obj.indexes_dir, obj.outputs_dir]:
            ensure_dir(path)
        return obj


def load_config(config_path: str | Path) -> dict[str, Any]:
    return read_json(config_path)
