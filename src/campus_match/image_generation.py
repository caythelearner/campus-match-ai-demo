from __future__ import annotations

import base64
import os
import textwrap
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont

from .io_utils import ensure_dir


def build_image_prompt(profile: dict[str, Any], kind: str = "lifestyle") -> str:
    interests = ", ".join(profile.get("interests", [])[:4])
    values = ", ".join(profile.get("values", [])[:3])
    style = ", ".join(profile.get("personality_tags", [])[:3])
    age = profile.get("age", 21)
    if kind == "avatar":
        return (
            f"A synthetic AI-generated campus dating app avatar of a {age}-year-old Chinese university student, "
            f"{style}, interests: {interests}, values: {values}, warm and natural portrait, soft daylight, "
            "realistic but clearly synthetic, no school logo, no ID card, no text, not a real person."
        )
    return (
        "A lifestyle image representing a Chinese university student, "
        f"interests: {interests}, personality style: {style}, values: {values}, "
        "warm campus atmosphere, soft daylight, no identifiable face, no school logo, no text, no real person."
    )


def _profile_color(profile: dict[str, Any]) -> tuple[int, int, int]:
    text = "|".join(profile.get("interests", [])) + profile.get("user_id", "")
    value = sum(ord(ch) for ch in text)
    return 80 + value % 120, 70 + (value // 3) % 120, 90 + (value // 7) % 120


def _blend(color_a: tuple[int, int, int], color_b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(int(a * (1 - ratio) + b * ratio) for a, b in zip(color_a, color_b))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    min_size: int = 18,
    bold: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        font = _load_font(size, bold=bold)
        width, _ = _text_size(draw, text, font)
        if width <= max_width:
            return font
    return _load_font(min_size, bold=bold)


def generate_placeholder_image(profile: dict[str, Any], output_path: str | Path, kind: str = "lifestyle") -> None:
    """Create a deterministic synthetic avatar card for offline demos."""
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    accent = _profile_color(profile)
    bg = _blend(accent, (255, 255, 255), 0.82)
    accent_dark = _blend(accent, (18, 33, 43), 0.35)
    accent_soft = _blend(accent, (255, 255, 255), 0.62)
    ink = (30, 41, 50)
    muted = (95, 105, 118)

    img = Image.new("RGB", (768, 768), (246, 248, 251))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((48, 48, 720, 720), radius=34, fill=(255, 255, 255), outline=(220, 226, 234), width=3)
    draw.rounded_rectangle((48, 48, 720, 320), radius=34, fill=bg)
    draw.rectangle((48, 284, 720, 330), fill=bg)

    # A clean symbolic portrait keeps the offline demo readable without pretending
    # to contain real student photos.
    face = _blend((255, 224, 198), accent_soft, 0.25)
    hair = _blend(accent_dark, (33, 39, 47), 0.35)
    shirt = accent_dark
    draw.ellipse((264, 112, 504, 352), fill=face, outline=(226, 197, 176), width=3)
    draw.pieslice((242, 86, 526, 286), start=190, end=355, fill=hair)
    draw.ellipse((318, 218, 334, 234), fill=ink)
    draw.ellipse((430, 218, 446, 234), fill=ink)
    draw.arc((344, 232, 424, 286), start=20, end=160, fill=(154, 95, 87), width=4)
    draw.rounded_rectangle((210, 358, 558, 528), radius=78, fill=shirt)
    draw.rounded_rectangle((318, 326, 450, 406), radius=34, fill=face)
    draw.rounded_rectangle((278, 404, 490, 468), radius=30, fill=_blend(shirt, (255, 255, 255), 0.16))

    badge_font = _load_font(26, bold=True)
    badge = f"{profile.get('user_id', 'USER')} · {profile.get('relationship_goal', '')}"
    badge_w, badge_h = _text_size(draw, badge, badge_font)
    draw.rounded_rectangle((60, 64, 84 + badge_w, 104 + badge_h), radius=18, fill=(255, 255, 255))
    draw.text((72, 74), badge, fill=accent_dark, font=badge_font)

    name = profile.get("display_name", profile.get("user_id", "Campus User"))
    title = f"{profile.get('major', '')} / {profile.get('campus', '')}"
    name_font = _fit_text(draw, name, 560, 44, bold=True)
    title_font = _fit_text(draw, title, 560, 28)
    name_w, _ = _text_size(draw, name, name_font)
    title_w, _ = _text_size(draw, title, title_font)
    draw.text(((768 - name_w) / 2, 548), name, fill=ink, font=name_font)
    draw.text(((768 - title_w) / 2, 604), title, fill=muted, font=title_font)

    chip_font = _load_font(22)
    chips = (profile.get("interests", [])[:2] + profile.get("values", [])[:1])[:3]
    x = 92
    y = 660
    for chip in chips:
        label = str(chip)
        chip_w, chip_h = _text_size(draw, label, chip_font)
        width = min(chip_w + 28, 210)
        draw.rounded_rectangle((x, y, x + width, y + chip_h + 18), radius=18, fill=accent_soft)
        draw.text((x + 14, y + 8), textwrap.shorten(label, width=8, placeholder=""), fill=accent_dark, font=chip_font)
        x += width + 14
    img.save(output_path)


def _save_base64_image(encoded: str, output_path: Path) -> None:
    if "," in encoded and encoded.split(",", 1)[0].startswith("data:"):
        encoded = encoded.split(",", 1)[1]
    data = base64.b64decode(encoded)
    Image.open(BytesIO(data)).save(output_path)


def generate_image_via_api(prompt: str, output_path: str | Path) -> bool:
    """Generic image API adapter.

    Environment variables:
    - IMAGE_API_URL
    - IMAGE_API_KEY
    - IMAGE_API_MODEL
    - IMAGE_API_RESPONSE_MODE: url or base64

    The payload/response format may need small provider-specific edits.
    """
    api_url = os.getenv("IMAGE_API_URL")
    api_key = os.getenv("IMAGE_API_KEY")
    model = os.getenv("IMAGE_API_MODEL")
    response_mode = os.getenv("IMAGE_API_RESPONSE_MODE", "url")
    if not api_url or not api_key:
        return False

    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    payload = {"prompt": prompt, "model": model, "size": "1024x1024", "response_format": response_mode}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    image_url = data.get("url")
    image_b64 = data.get("b64_json") or data.get("base64")
    if not image_url and isinstance(data.get("data"), list) and data["data"]:
        image_url = data["data"][0].get("url")
        image_b64 = data["data"][0].get("b64_json") or data["data"][0].get("base64")

    if image_url:
        img_resp = requests.get(image_url, timeout=120)
        img_resp.raise_for_status()
        output_path.write_bytes(img_resp.content)
        return True
    if image_b64:
        _save_base64_image(image_b64, output_path)
        return True
    return False


def generate_images_for_profiles(
    profiles: list[dict[str, Any]],
    images_dir: str | Path,
    provider: str = "placeholder",
    kind: str = "lifestyle",
    write_prompts: bool = True,
) -> list[dict[str, str]]:
    images_dir = ensure_dir(images_dir)
    rows: list[dict[str, str]] = []
    for profile in profiles:
        user_id = profile["user_id"]
        prompt = build_image_prompt(profile, kind=kind)
        image_path = images_dir / f"{user_id}.png"
        prompt_path = images_dir / f"{user_id}.prompt.txt"
        if write_prompts:
            prompt_path.write_text(prompt, encoding="utf-8")

        ok = False
        if provider == "api":
            ok = generate_image_via_api(prompt, image_path)
        if not ok:
            generate_placeholder_image(profile, image_path, kind=kind)
        rows.append({"user_id": user_id, "image_path": str(image_path), "prompt": prompt})
    return rows
