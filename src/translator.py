"""Translation module — OCR + machine translation pipeline."""

from typing import Optional

import easyocr
import translators as ts

# Lazy-initialised reader — models download to this directory on first use.
_reader: Optional[easyocr.Reader] = None


def _get_reader() -> easyocr.Reader:
    """Return a cached EasyOCR reader (Chinese simplified + English)."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(
            ["ch_sim", "en"],
            model_storage_directory="data/easyocr_models",
            download_enabled=True,
        )
    return _reader


def translate_image(image_path: str, target_lang: str = "zh-CN") -> str:
    """OCR the image at *image_path*, then translate the recognised text.

    Returns the translated string, or an error / empty-result message.
    """
    try:
        reader = _get_reader()
        results = reader.readtext(image_path)
    except Exception as exc:
        return f"OCR 识别失败：{exc}"

    if not results:
        return "未识别到文字"

    # Preserve line breaks — each detected block becomes one line
    lines = [item[1] for item in results]
    source_text = "\n".join(lines)

    # Map to Bing language codes ("zh-CN" → "zh-Hans", etc.)
    to_lang = "zh-Hans" if target_lang == "zh-CN" else target_lang

    try:
        translated = ts.translate_text(
            source_text,
            translator="bing",
            from_language="auto",
            to_language=to_lang,
        )
    except Exception as exc:
        return f"翻译请求失败：{exc}"

    return translated
