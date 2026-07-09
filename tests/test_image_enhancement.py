from __future__ import annotations

from io import BytesIO

from PIL import Image

from schedule_parser.image_enhancement import OUTPUT_MIME_TYPE, prepare_ocr_image, prepare_oil_street_timecard_sources


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


def test_prepare_oil_street_timecard_sources_splits_dual_card_image():
    original = _sample_png_bytes(size=(1300, 1000))

    sources = prepare_oil_street_timecard_sources(
        original,
        "Poon Wai Ching Crystal.png",
        mime_type="image/png",
        enabled=False,
    )

    assert len(sources) == 2
    assert [source.metadata["source_card_no"] for source in sources] == [1, 2]
    assert [source.filename for source in sources] == [
        "Poon Wai Ching Crystal__card_1.jpg",
        "Poon Wai Ching Crystal__card_2.jpg",
    ]
    assert all(source.source_filename == "Poon Wai Ching Crystal.png" for source in sources)
    assert all(source.preprocessing["split_applied"] is True for source in sources)


def test_prepare_oil_street_timecard_sources_keeps_single_vertical_card():
    original = _sample_png_bytes(size=(900, 1600))

    sources = prepare_oil_street_timecard_sources(
        original,
        "Wong Hau Sin Cynthia 2.png",
        mime_type="image/png",
        enabled=False,
    )

    assert len(sources) == 1
    assert sources[0].filename == "Wong Hau Sin Cynthia 2.png"
    assert sources[0].metadata["source_type"] == "single"
