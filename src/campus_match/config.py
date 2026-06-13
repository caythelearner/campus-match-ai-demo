from __future__ import annotations

from dataclasses import dataclass
import os
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
    load_env_file(Path(config_path).resolve().parents[1] / ".env")
    return read_json(config_path)


def load_env_file(path: str | Path) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ[key] = value
