from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import mimetypes
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError


SUPPORTED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
OUTPUT_MIME_TYPE = "image/jpeg"
MIN_LONG_EDGE = 2200
MAX_LONG_EDGE = 2800
MAX_UPSCALE_FACTOR = 2.0
DUAL_CARD_MIN_ASPECT_RATIO = 0.82


@dataclass(slots=True)
class PreparedOcrSource:
    file_bytes: bytes
    filename: str
    mime_type: str | None
    source_filename: str
    preprocessing: dict[str, Any]
    metadata: dict[str, Any]


def prepare_ocr_image(
    file_bytes: bytes,
    filename: str,
    *,
    mime_type: str | None = None,
    enabled: bool = True,
) -> tuple[bytes, str | None, dict[str, Any]]:
    """Return bytes/mime for OCR plus preprocessing metadata.

    Enhancement is intentionally conservative: it improves orientation, scale,
    contrast, and sharpness, but does not crop the card because losing labels or
    dates is worse than keeping some background.
    """
    normalized_mime = _normalize_mime_type(filename, mime_type)
    metadata: dict[str, Any] = {
        "enabled": bool(enabled),
        "applied": False,
        "input_mime_type": normalized_mime,
        "output_mime_type": normalized_mime,
        "method": "none",
    }
    if not enabled:
        metadata["reason"] = "disabled"
        return file_bytes, normalized_mime, metadata
    if normalized_mime not in SUPPORTED_IMAGE_MIME_TYPES:
        metadata["reason"] = "unsupported_file_type"
        return file_bytes, normalized_mime, metadata

    try:
        enhanced_bytes, details = enhance_logsheet_image(file_bytes)
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        metadata["reason"] = "enhancement_failed"
        metadata["error"] = str(exc)
        return file_bytes, normalized_mime, metadata

    metadata.update(details)
    metadata["applied"] = True
    metadata["output_mime_type"] = OUTPUT_MIME_TYPE
    metadata["method"] = "exif_transpose_resize_autocontrast_sharpen"
    return enhanced_bytes, OUTPUT_MIME_TYPE, metadata


def prepare_oil_street_timecard_sources(
    file_bytes: bytes,
    filename: str,
    *,
    mime_type: str | None = None,
    enabled: bool = True,
) -> list[PreparedOcrSource]:
    normalized_mime = _normalize_mime_type(filename, mime_type)
    if normalized_mime not in SUPPORTED_IMAGE_MIME_TYPES:
        processed, output_mime, preprocessing = prepare_ocr_image(
            file_bytes,
            filename,
            mime_type=mime_type,
            enabled=enabled,
        )
        return [
            PreparedOcrSource(
                file_bytes=processed,
                filename=filename,
                mime_type=output_mime,
                source_filename=filename,
                preprocessing=preprocessing,
                metadata={
                    "source_type": "pdf" if normalized_mime == "application/pdf" else "single",
                    "source_part_count": 1,
                },
            )
        ]

    try:
        image = Image.open(BytesIO(file_bytes))
        image = ImageOps.exif_transpose(image)
        image = _to_rgb_on_white(image)
    except (OSError, UnidentifiedImageError, ValueError):
        processed, output_mime, preprocessing = prepare_ocr_image(
            file_bytes,
            filename,
            mime_type=mime_type,
            enabled=enabled,
        )
        return [
            PreparedOcrSource(
                file_bytes=processed,
                filename=filename,
                mime_type=output_mime,
                source_filename=filename,
                preprocessing=preprocessing,
                metadata={"source_type": "single", "source_part_count": 1},
            )
        ]

    if not _looks_like_dual_timecard_image(image):
        processed, output_mime, preprocessing = prepare_ocr_image(
            file_bytes,
            filename,
            mime_type=mime_type,
            enabled=enabled,
        )
        return [
            PreparedOcrSource(
                file_bytes=processed,
                filename=filename,
                mime_type=output_mime,
                source_filename=filename,
                preprocessing=preprocessing,
                metadata={"source_type": "single", "source_part_count": 1},
            )
        ]

    sources: list[PreparedOcrSource] = []
    for part_index, card_no, crop_box in _dual_timecard_crop_boxes(image):
        crop = image.crop(crop_box)
        crop_bytes = _image_to_jpeg_bytes(crop)
        part_filename = _source_part_filename(filename, card_no)
        processed, output_mime, preprocessing = prepare_ocr_image(
            crop_bytes,
            part_filename,
            mime_type=OUTPUT_MIME_TYPE,
            enabled=enabled,
        )
        preprocessing["split_applied"] = True
        preprocessing["source_filename"] = filename
        preprocessing["source_part_filename"] = part_filename
        preprocessing["source_part_count"] = 2
        preprocessing["source_card_no"] = card_no
        preprocessing["crop_box"] = {
            "left": crop_box[0],
            "top": crop_box[1],
            "right": crop_box[2],
            "bottom": crop_box[3],
        }
        sources.append(
            PreparedOcrSource(
                file_bytes=processed,
                filename=part_filename,
                mime_type=output_mime,
                source_filename=filename,
                preprocessing=preprocessing,
                metadata={
                    "source_type": "dual_card_image",
                    "source_part_index": part_index,
                    "source_part_count": 2,
                    "source_part_label": f"card {card_no}",
                    "source_card_no": card_no,
                    "source_part_filename": part_filename,
                    "source_crop_box": preprocessing["crop_box"],
                },
            )
        )
    return sources


def enhance_logsheet_image(file_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    image = Image.open(BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)
    image = _to_rgb_on_white(image)
    original_size = image.size

    image, scale_factor = _resize_for_ocr(image)
    image = ImageOps.autocontrast(image, cutoff=0.5)
    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = ImageEnhance.Sharpness(image).enhance(1.35)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=3))

    output = BytesIO()
    image.save(output, format="JPEG", quality=92, optimize=True)
    enhanced = output.getvalue()
    return enhanced, {
        "original_size": {"width": original_size[0], "height": original_size[1]},
        "processed_size": {"width": image.width, "height": image.height},
        "scale_factor": round(scale_factor, 3),
        "original_bytes": len(file_bytes),
        "processed_bytes": len(enhanced),
    }


def _resize_for_ocr(image: Image.Image) -> tuple[Image.Image, float]:
    long_edge = max(image.size)
    if long_edge <= 0:
        raise ValueError("image has invalid dimensions")
    if long_edge < MIN_LONG_EDGE:
        scale = min(MIN_LONG_EDGE / long_edge, MAX_UPSCALE_FACTOR)
    elif long_edge > MAX_LONG_EDGE:
        scale = MAX_LONG_EDGE / long_edge
    else:
        scale = 1.0
    if abs(scale - 1.0) < 0.001:
        return image, 1.0
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS), scale


def _to_rgb_on_white(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        return background.convert("RGB")
    return image.convert("RGB")


def _looks_like_dual_timecard_image(image: Image.Image) -> bool:
    width, height = image.size
    if width < 900 or height < 700:
        return False
    aspect_ratio = width / max(height, 1)
    return aspect_ratio >= DUAL_CARD_MIN_ASPECT_RATIO


def _dual_timecard_crop_boxes(image: Image.Image) -> list[tuple[int, int, tuple[int, int, int, int]]]:
    width, height = image.size
    midpoint = width // 2
    overlap = max(8, round(width * 0.015))
    return [
        (1, 1, (0, 0, min(width, midpoint + overlap), height)),
        (2, 2, (max(0, midpoint - overlap), 0, width, height)),
    ]


def _image_to_jpeg_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="JPEG", quality=94, optimize=True)
    return output.getvalue()


def _source_part_filename(filename: str, card_no: int) -> str:
    path = Path(filename)
    return f"{path.stem}__card_{card_no}.jpg"


def _normalize_mime_type(filename: str, mime_type: str | None) -> str | None:
    guessed = mimetypes.guess_type(Path(filename).name)[0]
    normalized = (mime_type or guessed or "").split(";")[0].strip().lower()
    return normalized or guessed
