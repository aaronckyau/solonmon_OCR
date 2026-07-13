from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import mimetypes
from pathlib import Path
import re
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError


SUPPORTED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
OUTPUT_MIME_TYPE = "image/jpeg"
MIN_LONG_EDGE = 2200
MAX_LONG_EDGE = 2800
MAX_UPSCALE_FACTOR = 2.0
DUAL_CARD_MIN_ASPECT_RATIO = 0.82
PDF_MIME_TYPE = "application/pdf"
PDF_LABEL_FONT_MIN = 13.0
PDF_LABEL_FONT_MAX = 19.0


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
    staff_names: list[str] | None = None,
) -> list[PreparedOcrSource]:
    normalized_mime = _normalize_mime_type(filename, mime_type)
    if normalized_mime == PDF_MIME_TYPE:
        pdf_sources = _prepare_oil_street_pdf_timecard_sources(
            file_bytes,
            filename,
            enabled=enabled,
            staff_names=staff_names or [],
        )
        if pdf_sources:
            return pdf_sources
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
                    "source_type": "pdf" if normalized_mime == PDF_MIME_TYPE else "single",
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


def _prepare_oil_street_pdf_timecard_sources(
    file_bytes: bytes,
    filename: str,
    *,
    enabled: bool,
    staff_names: list[str],
) -> list[PreparedOcrSource]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(file_bytes))
    except Exception:
        return []

    sources: list[PreparedOcrSource] = []
    for page_number, page in enumerate(reader.pages, start=1):
        labels = _pdf_page_staff_labels(page, staff_names)
        if len(labels) < 2:
            continue
        row_images = _pdf_page_timecard_row_images(page)
        if not row_images:
            continue

        for staff_index, staff_name_hint in enumerate(labels, start=1):
            cards: list[tuple[int, Image.Image]] = []
            crop_boxes: list[dict[str, Any]] = []
            for card_no, row_image in sorted(row_images.items()):
                card, crop_box = _crop_timecard_from_row(
                    row_image,
                    staff_index - 1,
                    len(labels),
                    card_no,
                )
                cards.append((card_no, card))
                crop_boxes.append({"card_no": card_no, **crop_box})
            if not cards:
                continue

            paired_image = _combine_timecard_cards(cards)
            part_filename = _pdf_staff_part_filename(filename, page_number, staff_index)
            paired_bytes = _image_to_jpeg_bytes(paired_image)
            processed, output_mime, preprocessing = prepare_ocr_image(
                paired_bytes,
                part_filename,
                mime_type=OUTPUT_MIME_TYPE,
                enabled=enabled,
            )
            preprocessing.update(
                {
                    "split_applied": True,
                    "source_filename": filename,
                    "source_part_filename": part_filename,
                    "source_page": page_number,
                    "source_staff_index": staff_index,
                    "source_staff_name_hint": staff_name_hint,
                    "source_card_nos": [card_no for card_no, _card in cards],
                    "source_crop_boxes": crop_boxes,
                }
            )
            sources.append(
                PreparedOcrSource(
                    file_bytes=processed,
                    filename=part_filename,
                    mime_type=output_mime,
                    source_filename=filename,
                    preprocessing=preprocessing,
                    metadata={
                        "source_type": "pdf_timecard_pair",
                        "source_page": page_number,
                        "source_staff_index": staff_index,
                        "source_staff_name_hint": staff_name_hint,
                        "source_card_nos": [card_no for card_no, _card in cards],
                        "source_part_filename": part_filename,
                        "source_part_label": f"page {page_number}, staff {staff_index}, cards 1-2",
                        "source_crop_boxes": crop_boxes,
                    },
                )
            )

    if len(sources) < 2:
        return []
    for source in sources:
        source.metadata["source_part_count"] = len(sources)
        source.preprocessing["source_part_count"] = len(sources)
    return sources


def _pdf_page_staff_labels(page: Any, staff_names: list[str]) -> list[str]:
    fragments: list[dict[str, Any]] = []

    def collect(text, current_matrix, text_matrix, _font, font_size) -> None:
        value = " ".join(str(text or "").split())
        if not value or not (PDF_LABEL_FONT_MIN <= float(font_size or 0) <= PDF_LABEL_FONT_MAX):
            return
        scale_x = abs(float(current_matrix[0])) or 1.0
        scale_y = abs(float(current_matrix[3])) or 1.0
        fragments.append(
            {
                "text": value,
                "x": float(current_matrix[4]) / scale_x,
                "y": float(current_matrix[5]) / scale_y,
                "line_y": float(text_matrix[5]),
            }
        )

    try:
        page.extract_text(visitor_text=collect)
    except Exception:
        return []
    if not fragments:
        return []

    bands: list[dict[str, Any]] = []
    for fragment in sorted(fragments, key=lambda item: item["y"]):
        band = next((item for item in bands if abs(item["y"] - fragment["y"]) <= 45), None)
        if band is None:
            band = {"y": fragment["y"], "fragments": []}
            bands.append(band)
        band["fragments"].append(fragment)

    candidates: list[list[str]] = []
    for band in bands:
        groups: list[dict[str, Any]] = []
        for fragment in sorted(band["fragments"], key=lambda item: (item["x"], item["line_y"])):
            group = next((item for item in groups if abs(item["x"] - fragment["x"]) <= 18), None)
            if group is None:
                group = {"x": fragment["x"], "fragments": []}
                groups.append(group)
            group["fragments"].append(fragment)
        labels = [
            " ".join(item["text"] for item in sorted(group["fragments"], key=lambda item: item["line_y"]))
            for group in sorted(groups, key=lambda item: item["x"])
        ]
        candidates.append([_match_staff_label(label, staff_names) for label in labels])
    return max(candidates, key=len, default=[])


def _match_staff_label(label: str, staff_names: list[str]) -> str:
    normalized_label = _normalized_name(label)
    for staff_name in staff_names:
        if _normalized_name(staff_name) == normalized_label:
            return staff_name
    return label


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _pdf_page_timecard_row_images(page: Any) -> dict[int, Image.Image]:
    candidates: list[tuple[Image.Image, int, int]] = []
    try:
        page_images = list(page.images)
    except Exception:
        return {}
    for item in page_images:
        try:
            image = Image.open(BytesIO(item.data))
            image = _to_rgb_on_white(image)
        except (OSError, UnidentifiedImageError, ValueError):
            continue
        if image.width < image.height:
            image = image.rotate(90, expand=True)
        if image.width < 500 or image.height < 400:
            continue
        blue_score, orange_score = _timecard_color_scores(image)
        candidates.append((image, blue_score, orange_score))
    if not candidates:
        return {}
    if len(candidates) == 1:
        image, blue_score, orange_score = candidates[0]
        return {1 if blue_score >= orange_score else 2: image}

    blue_index = max(range(len(candidates)), key=lambda index: candidates[index][1] - candidates[index][2])
    orange_index = min(range(len(candidates)), key=lambda index: candidates[index][1] - candidates[index][2])
    if blue_index == orange_index:
        return {}
    return {1: candidates[blue_index][0], 2: candidates[orange_index][0]}


def _timecard_color_scores(image: Image.Image) -> tuple[int, int]:
    sample, _scale = _resize_for_detection(image)
    pixels = sample.load()
    cutoff = max(1, round(sample.height * 0.55))
    blue_score = 0
    orange_score = 0
    for y in range(cutoff):
        blue_count = 0
        orange_count = 0
        for x in range(sample.width):
            red, green, blue = pixels[x, y]
            blue_count += int(_is_blue_header_pixel(red, green, blue))
            orange_count += int(_is_orange_header_pixel(red, green, blue))
        blue_score = max(blue_score, blue_count)
        orange_score = max(orange_score, orange_count)
    return blue_score, orange_score


def _crop_timecard_from_row(
    image: Image.Image,
    index: int,
    count: int,
    card_no: int,
) -> tuple[Image.Image, dict[str, int]]:
    left, right = _timecard_row_horizontal_bounds(image, count, card_no)
    pitch = (right - left) / max(count, 1)
    overlap = max(6, round(pitch * 0.045))
    crop_left = max(0, round(left + index * pitch) - overlap)
    crop_right = min(image.width, round(left + (index + 1) * pitch) + overlap)
    header_top = _timecard_header_top(image, card_no)
    crop_top = max(0, header_top - max(8, round(pitch * 0.08)))
    crop_bottom = min(image.height, crop_top + round((crop_right - crop_left) * 2.55))
    if crop_bottom - crop_top < image.height * 0.45:
        crop_bottom = image.height
    crop_box = (crop_left, crop_top, crop_right, crop_bottom)
    return image.crop(crop_box), {
        "left": crop_left,
        "top": crop_top,
        "right": crop_right,
        "bottom": crop_bottom,
    }


def _timecard_row_horizontal_bounds(image: Image.Image, count: int, card_no: int) -> tuple[int, int]:
    if count > 3:
        return 0, image.width
    sample, scale = _resize_for_detection(image)
    pixels = sample.load()
    cutoff = max(1, round(sample.height * 0.55))
    min_length = max(5, round(sample.width / max(count * 6, 1)))
    candidates: list[list[tuple[int, int]]] = []
    for center_y in range(4, max(4, cutoff - 4)):
        band_top = center_y - 4
        band_bottom = center_y + 5
        required = max(1, round((band_bottom - band_top) * 0.2))
        active = [
            sum(
                1
                for y in range(band_top, band_bottom)
                if _is_card_header_pixel(pixels[x, y], card_no)
            ) >= required
            for x in range(sample.width)
        ]
        intervals = _true_intervals(active, min_length=min_length)
        if len(intervals) == count:
            candidates.append(intervals)
    if not candidates:
        return 0, image.width
    selected = max(candidates, key=lambda items: sum(right - left for left, right in items))
    left = min(item[0] for item in selected)
    right = max(item[1] for item in selected)
    margin = max(3, round((right - left) / max(count, 1) * 0.05))
    return max(0, round((left - margin) / scale)), min(image.width, round((right + margin) / scale))


def _timecard_header_top(image: Image.Image, card_no: int) -> int:
    sample, scale = _resize_for_detection(image)
    pixels = sample.load()
    cutoff = max(1, round(sample.height * 0.55))
    counts = [
        sum(1 for x in range(sample.width) if _is_card_header_pixel(pixels[x, y], card_no))
        for y in range(cutoff)
    ]
    peak = max(counts, default=0)
    threshold = max(round(sample.width * 0.18), round(peak * 0.52))
    candidates = [y for y, value in enumerate(counts) if value >= threshold]
    if not candidates:
        return 0
    return max(0, round(candidates[0] / scale))


def _resize_for_detection(image: Image.Image) -> tuple[Image.Image, float]:
    if image.width <= 760:
        return image, 1.0
    scale = 760 / image.width
    size = (760, max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.BILINEAR), scale


def _is_card_header_pixel(pixel: tuple[int, int, int], card_no: int) -> bool:
    red, green, blue = pixel
    if card_no == 1:
        return _is_blue_header_pixel(red, green, blue)
    return _is_orange_header_pixel(red, green, blue)


def _is_blue_header_pixel(red: int, green: int, blue: int) -> bool:
    return blue - red > 18 and blue - green > 3 and blue > 70


def _is_orange_header_pixel(red: int, green: int, blue: int) -> bool:
    return red - blue > 30 and red - green > 5 and red > 120 and green > 50


def _true_intervals(values: list[bool], *, min_length: int) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate([*values, False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            if index - start >= min_length:
                intervals.append((start, index))
            start = None
    return intervals


def _combine_timecard_cards(cards: list[tuple[int, Image.Image]]) -> Image.Image:
    gap = 18
    height = max(card.height for _card_no, card in cards)
    width = sum(card.width for _card_no, card in cards) + gap * max(0, len(cards) - 1)
    output = Image.new("RGB", (width, height), "white")
    offset = 0
    for _card_no, card in cards:
        output.paste(card, (offset, 0))
        offset += card.width + gap
    return output


def _pdf_staff_part_filename(filename: str, page_number: int, staff_index: int) -> str:
    stem = Path(filename).stem or "timecard"
    return f"{stem}__page_{page_number:02d}__staff_{staff_index:02d}.jpg"


def _normalize_mime_type(filename: str, mime_type: str | None) -> str | None:
    guessed = mimetypes.guess_type(Path(filename).name)[0]
    normalized = (mime_type or guessed or "").split(";")[0].strip().lower()
    return normalized or guessed
