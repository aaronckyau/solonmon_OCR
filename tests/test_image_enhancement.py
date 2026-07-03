from __future__ import annotations

from io import BytesIO

from PIL import Image

from schedule_parser.image_enhancement import OUTPUT_MIME_TYPE, prepare_ocr_image


def _sample_png_bytes(size=(320, 520)) -> bytes:
    image = Image.new("RGB", size, "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_prepare_ocr_image_enhances_supported_image():
    original = _sample_png_bytes()

    processed, mime_type, metadata = prepare_ocr_image(
        original,
        "logsheet.png",
        mime_type="image/png",
        enabled=True,
    )

    assert processed != original
    assert mime_type == OUTPUT_MIME_TYPE
    assert metadata["applied"] is True
    assert metadata["output_mime_type"] == OUTPUT_MIME_TYPE
    assert metadata["processed_size"]["height"] >= 1000


def test_prepare_ocr_image_can_be_disabled():
    original = _sample_png_bytes()

    processed, mime_type, metadata = prepare_ocr_image(
        original,
        "logsheet.png",
        mime_type="image/png",
        enabled=False,
    )

    assert processed == original
    assert mime_type == "image/png"
    assert metadata["applied"] is False
    assert metadata["reason"] == "disabled"


def test_prepare_ocr_image_skips_pdf():
    processed, mime_type, metadata = prepare_ocr_image(
        b"%PDF fake",
        "logsheet.pdf",
        mime_type="application/pdf",
        enabled=True,
    )

    assert processed == b"%PDF fake"
    assert mime_type == "application/pdf"
    assert metadata["applied"] is False
    assert metadata["reason"] == "unsupported_file_type"
