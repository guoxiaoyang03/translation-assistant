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


def _normalize_lang(code: str) -> str:
    """Normalize a language code for the translators (Bing) backend.

    ``zh-CN`` is mapped to ``zh-Hans``, which Bing expects for simplified
    Chinese.  All other codes pass through unchanged.
    """
    if code == "zh-CN":
        return "zh-Hans"
    return code


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate *text* from *source_lang* to *target_lang*.

    Returns the translated string, or an error message.
    """
    if not text.strip():
        return "源文本为空，无法翻译"

    try:
        result = ts.translate_text(
            text,
            translator="bing",
            from_language=_normalize_lang(source_lang),
            to_language=_normalize_lang(target_lang),
        )
    except Exception as exc:
        return f"翻译请求失败：{exc}"

    return result


def translate_image(image_path: str, source_lang: str, target_lang: str) -> tuple[str, str]:
    """OCR the image at *image_path*, then translate the recognised text
    from *source_lang* to *target_lang*.

    Returns a ``(translated_text, ocr_text)`` tuple.  On OCR failure both
    elements contain the error message; on empty result both contain
    ``"未识别到文字"``.
    """
    try:
        reader = _get_reader()
        results = reader.readtext(image_path)
    except Exception as exc:
        msg = f"OCR 识别失败：{exc}"
        return (msg, msg)

    if not results:
        msg = "未识别到文字"
        return (msg, msg)

    # Preserve line breaks — each detected block becomes one line
    lines = [item[1] for item in results]
    source_text = "\n".join(lines)

    translated = translate_text(source_text, source_lang, target_lang)
    return (translated, source_text)
