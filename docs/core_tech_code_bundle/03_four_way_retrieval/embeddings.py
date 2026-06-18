from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .io_utils import ensure_dir, write_json


TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norm, eps)


def hash_embedding(text: str, dim: int = 384) -> np.ndarray:
    """Deterministic offline text embedding.

    This is a fallback for demos without model downloads. Replace with
    sentence-transformers for better semantic quality.
    """
    vec = np.zeros(dim, dtype=np.float32)
    tokens = TOKEN_RE.findall(text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 else -1.0
        vec[idx] += sign
    return l2_normalize(vec.reshape(1, -1))[0]


class TextEmbedder:
    def __init__(self, provider: str = "hash", model_name: str = "", dim: int = 384) -> None:
        self.provider = provider
        self.requested_provider = provider
        self.model_name = model_name
        self.dim = dim
        self.model = None
        self.error = ""
        if provider in {"sentence_transformer", "auto"}:
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(model_name)
                self.provider = "sentence_transformer"
            except Exception as exc:  # noqa: BLE001
                self.provider = "hash"
                self.error = str(exc)

    def encode(self, texts: list[str]) -> np.ndarray:
        if self.provider == "sentence_transformer" and self.model is not None:
            vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(vectors, dtype=np.float32)
        return np.vstack([hash_embedding(text, self.dim) for text in texts]).astype(np.float32)


def profile_to_text(profile: dict[str, Any]) -> str:
    parts = [
        profile.get("self_intro", ""),
        profile.get("ideal_partner", ""),
        "兴趣：" + "、".join(profile.get("interests", [])),
        "价值观：" + "、".join(profile.get("values", [])),
        "关系目标：" + str(profile.get("relationship_goal", "")),
        "沟通风格：" + str(profile.get("communication_style", "")),
        "理想约会：" + "、".join(profile.get("preferred_date", [])),
        "雷点：" + "、".join(profile.get("deal_breakers", [])),
    ]
    return "\n".join(parts)


def color_histogram_embedding(image_path: str | Path, bins: int = 16) -> np.ndarray:
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    hist_parts = []
    for channel in range(3):
        hist, _ = np.histogram(arr[:, :, channel], bins=bins, range=(0.0, 1.0), density=True)
        hist_parts.append(hist.astype(np.float32))
    vec = np.concatenate(hist_parts)
    return l2_normalize(vec.reshape(1, -1))[0]


class ImageEmbedder:
    def __init__(self, provider: str = "color_histogram", clip_model_name: str = "openai/clip-vit-base-patch32") -> None:
        self.provider = provider
        self.clip_model_name = clip_model_name
        self.model = None
        self.processor = None
        self.device = "cpu"
        if provider == "clip":
            import torch
            from transformers import CLIPModel, CLIPProcessor

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = CLIPModel.from_pretrained(clip_model_name).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(clip_model_name)

    def encode(self, image_paths: list[str | Path]) -> np.ndarray:
        if self.provider == "clip" and self.model is not None and self.processor is not None:
            import torch

            vectors = []
            for path in image_paths:
                image = Image.open(path).convert("RGB")
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    feat = self.model.get_image_features(**inputs)
                feat = feat / feat.norm(dim=-1, keepdim=True)
                vectors.append(feat.detach().cpu().numpy()[0])
            return np.asarray(vectors, dtype=np.float32)
        vectors = [color_histogram_embedding(path) for path in image_paths]
        return np.vstack(vectors).astype(np.float32)


def build_embeddings(
    profiles: list[dict[str, Any]],
    image_rows: list[dict[str, str]],
    indexes_dir: str | Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    indexes_dir = ensure_dir(indexes_dir)
    emb_cfg = config.get("embedding", {})
    dim = int(config.get("embedding_dim", 384))
    text_embedder = TextEmbedder(
        provider=emb_cfg.get("text_provider", "hash"),
        model_name=emb_cfg.get("text_model_name", ""),
        dim=dim,
    )
    profile_texts = [profile_to_text(profile) for profile in profiles]
    text_vectors = text_embedder.encode(profile_texts)

    image_map = {row["user_id"]: row["image_path"] for row in image_rows}
    image_paths = [image_map[profile["user_id"]] for profile in profiles]
    image_embedder = ImageEmbedder(
        provider=emb_cfg.get("image_provider", "color_histogram"),
        clip_model_name=emb_cfg.get("clip_model_name", "openai/clip-vit-base-patch32"),
    )
    image_vectors = image_embedder.encode(image_paths)

    np.save(indexes_dir / "text_embeddings.npy", text_vectors)
    np.save(indexes_dir / "image_embeddings.npy", image_vectors)
    metadata = {
        "user_ids": [p["user_id"] for p in profiles],
        "profile_texts": profile_texts,
        "image_paths": image_paths,
        "text_shape": list(text_vectors.shape),
        "image_shape": list(image_vectors.shape),
        "text_provider_requested": text_embedder.requested_provider,
        "text_provider_actual": text_embedder.provider,
        "text_model_name": text_embedder.model_name,
        "text_provider_error": text_embedder.error,
        "image_provider": image_embedder.provider,
        "clip_model_name": image_embedder.clip_model_name,
    }
    write_json(indexes_dir / "embedding_metadata.json", metadata)

    try:
        import faiss

        text_index = faiss.IndexFlatIP(text_vectors.shape[1])
        text_index.add(text_vectors.astype(np.float32))
        faiss.write_index(text_index, str(indexes_dir / "text_flat.index"))
        image_index = faiss.IndexFlatIP(image_vectors.shape[1])
        image_index.add(image_vectors.astype(np.float32))
        faiss.write_index(image_index, str(indexes_dir / "image_flat.index"))
        metadata["faiss"] = True
        metadata["faiss_index_files"] = ["indexes/text_flat.index", "indexes/image_flat.index"]
        write_json(indexes_dir / "embedding_metadata.json", metadata)
    except Exception as exc:  # noqa: BLE001
        metadata["faiss"] = False
        metadata["faiss_error"] = str(exc)
        write_json(indexes_dir / "embedding_metadata.json", metadata)

    return {"text": text_vectors, "image": image_vectors, "metadata": metadata, "text_embedder": text_embedder}
