from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
import pytest

from schedule_parser.image_enhancement import (
    OUTPUT_MIME_TYPE,
    PdfStaffLabel,
    _match_staff_label,
    _timecard_column_crop_bounds,
    _timecard_row_with_roster_labels,
    prepare_ocr_image,
    prepare_oil_street_timecard_sources,
)


OIL_JUNE_STAFF_NAMES = [
    "Au Kin Wai Johnny",
    "Chui Chung Yan Nicole",
    "Ching Yeuk Ling Alice",
    "Ko Wai Yin",
    "Kwong Wai Thomas",
    "Lam Wai Ching Jade",
    "Lau Ka Yiu Yo Yo",
    "Law Suet Shan",
    "Leung Ah Woon Alvina",
    "Ma Pak Yin Momo",
    "Lo Siu Ho Heaven",
    "Poon Wai Ching Crystal",
    "Ma Pui Ying Joy",
    "Pan Hoi Yin William",
    "Tse Bing Ying Samantha",
    "Woo Hiu Ki Yuki",
    "Kan Lok Chi Gigi",
    "Wong Ching Yuk Selene",
    "Wong Pak Him Samuel",
    "Lam Lok Yi Sum",
    "Mok Ka Man Idy",
    "Leung Yuen Yi Alyria",
    "Wong Pui Yin Olivia",
    "Lau Yuet To Alice",
]


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


def test_timecard_row_roster_band_uses_canonical_names():
    row = Image.new("RGB", (600, 800), "white")
    labels = [
        PdfStaffLabel(raw_label="Johnny", roster_name="Au Kin Wai Johnny", x=0),
        PdfStaffLabel(raw_label="Nicole", roster_name="Chui Chung Yan Nicole", x=300),
    ]

    labeled, band_height = _timecard_row_with_roster_labels(
        row,
        labels,
        [(0, 300), (300, 600)],
    )

    assert labeled.size == (600, 800 + band_height)
    assert 56 <= band_height <= 96
    label_band = labeled.crop((0, 0, labeled.width, band_height))
    assert label_band.convert("L").getextrema()[0] < 100


def test_prepare_oil_street_all_staff_pdf_splits_one_source_per_card():
    sample = (
        Path(__file__).parents[1]
        / "doc"
        / "Testing"
        / "Testing"
        / "Oil Street"
        / "June 2026"
        / "Oi! timecard_June 2026 (All Staff).pdf"
    )
    if not sample.exists():
        pytest.skip("Oil Street all-staff PDF fixture is not available")

    sources = prepare_oil_street_timecard_sources(
        sample.read_bytes(),
        sample.name,
        mime_type="application/pdf",
        enabled=False,
        staff_names=OIL_JUNE_STAFF_NAMES,
    )

    assert len(sources) == 50
    assert {source.metadata["source_type"] for source in sources} == {"pdf_timecard_card"}
    assert all(source.editor_file_bytes for source in sources)
    assert all(source.editor_filename for source in sources)
    assert all(source.metadata["source_editor_size"]["width"] > 0 for source in sources)
    assert all(source.metadata["source_roster_label_band"] is True for source in sources)
    assert all(source.metadata["source_roster_label_band_height"] > 0 for source in sources)
    assert all(source.metadata["source_crop_box"]["top"] == 0 for source in sources)
    assert sources[0].metadata["source_editor_vertical_crop"]["top"] > 0
    assert all(source.metadata["source_split_status"] in {"ready", "review"} for source in sources)
    assert all(0 <= source.metadata["source_split_score"] <= 100 for source in sources)
    assert [source.metadata["source_page"] for source in sources] == [
        *([1] * 12),
        *([2] * 12),
        *([3] * 12),
        *([4] * 10),
        *([5] * 4),
    ]
    assert sources[0].metadata["source_staff_name_hint"].replace(" ", "") == "AuKinWaiJohnny"
    assert sources[-1].metadata["source_staff_name_hint"].replace(" ", "") == "LauYuetToAlice"
    assert all(source.metadata["source_staff_name_hint"] in OIL_JUNE_STAFF_NAMES for source in sources)
    assert all(source.metadata["source_staff_label"] for source in sources)
    assert [source.metadata["source_card_no"] for source in sources[:4]] == [1, 2, 1, 2]
    assert sources[0].filename.endswith("__card_1.jpg")
    assert sources[1].filename.endswith("__card_2.jpg")
    jade_card_1 = next(
        source
        for source in sources
        if source.metadata["source_staff_name_hint"].replace(" ", "") == "LamWaiChingJade"
        and source.metadata["source_card_no"] == 1
    )
    jade_crop = jade_card_1.metadata["source_crop_box"]
    assert 230 <= jade_crop["right"] - jade_crop["left"] <= 320


def test_prepare_oil_street_pdf_problem_cards_keep_complete_width_and_height():
    sample = (
        Path(__file__).parents[1]
        / "doc"
        / "Testing"
        / "Testing"
        / "Oil Street"
        / "June 2026"
        / "Oi! timecard_June 2026 (All Staff).pdf"
    )
    if not sample.exists():
        pytest.skip("Oil Street all-staff PDF fixture is not available")

    sources = prepare_oil_street_timecard_sources(
        sample.read_bytes(),
        sample.name,
        mime_type="application/pdf",
        enabled=False,
        staff_names=OIL_JUNE_STAFF_NAMES,
    )

    targets = [
        source
        for source in sources
        if source.metadata["source_staff_name_hint"] in {"Law Suet Shan", "Ma Pui Ying Joy"}
    ]
    assert len(targets) == 4
    assert all(source.preprocessing["source_crop_size"]["width"] >= 230 for source in targets)
    assert all(source.preprocessing["source_crop_size"]["height"] >= 700 for source in targets)
    assert all(source.metadata["source_split_method"] == "color_extent_grid" for source in targets)


def test_prepare_oil_street_pdf_card_crops_do_not_overlap_adjacent_staff():
    sample = (
        Path(__file__).parents[1]
        / "doc"
        / "Testing"
        / "Testing"
        / "Oil Street"
        / "June 2026"
        / "Oi! timecard_June 2026 (All Staff).pdf"
    )
    if not sample.exists():
        pytest.skip("Oil Street all-staff PDF fixture is not available")

    sources = prepare_oil_street_timecard_sources(
        sample.read_bytes(),
        sample.name,
        mime_type="application/pdf",
        enabled=False,
        staff_names=OIL_JUNE_STAFF_NAMES,
    )

    for page_number in range(1, 6):
        for card_no in (1, 2):
            row = sorted(
                (
                    source
                    for source in sources
                    if source.metadata["source_page"] == page_number
                    and source.metadata["source_card_no"] == card_no
                ),
                key=lambda source: source.metadata["source_staff_index"],
            )
            for current, following in zip(row, row[1:]):
                assert current.metadata["source_crop_box"]["right"] <= following.metadata["source_crop_box"]["left"]


def test_prepare_oil_street_pdf_cards_are_large_enough_for_stamp_ocr():
    sample = (
        Path(__file__).parents[1]
        / "doc"
        / "Testing"
        / "Testing"
        / "Oil Street"
        / "June 2026"
        / "Oi! timecard_June 2026 (All Staff).pdf"
    )
    if not sample.exists():
        pytest.skip("Oil Street all-staff PDF fixture is not available")

    sources = prepare_oil_street_timecard_sources(
        sample.read_bytes(),
        sample.name,
        mime_type="application/pdf",
        enabled=True,
        staff_names=OIL_JUNE_STAFF_NAMES,
    )
    source = next(
        item
        for item in sources
        if item.metadata["source_staff_name_hint"].replace(" ", "") == "LauKaYiuYoYo"
        and item.metadata["source_card_no"] == 1
    )

    with Image.open(BytesIO(source.file_bytes)) as image:
        assert image.width >= 780
        assert image.height >= 2000


def test_match_staff_label_only_returns_canonical_roster_name():
    assert _match_staff_label("Lau Ka Y iu Y o Y o", OIL_JUNE_STAFF_NAMES) == "Lau Ka Yiu Yo Yo"
    assert _match_staff_label("Brand New OCR Name", OIL_JUNE_STAFF_NAMES) is None


def test_timecard_column_crop_bounds_follow_irregular_card_positions():
    image = Image.new("RGB", (760, 300), "white")
    pixels = image.load()
    starts = [20, 120, 225, 335, 450, 565]
    ends = [100, 205, 315, 430, 545, 690]
    for left, right in zip(starts, ends):
        for y in range(25, 46):
            for x in range(left, right):
                pixels[x, y] = (35, 90, 190)

    bounds = _timecard_column_crop_bounds(image, 6, 1)

    assert len(bounds) == 6
    assert bounds[-1][0] == starts[-1]
    assert bounds[-1][1] >= ends[-1]
    assert all(current[1] <= following[0] for current, following in zip(bounds, bounds[1:]))


def test_timecard_column_crop_bounds_reject_implausibly_narrow_columns():
    image = Image.new("RGB", (1512, 1134), "white")
    pixels = image.load()
    intervals = [(360, 472), (846, 895), (899, 945), (1092, 1142), (1158, 1202), (1343, 1387)]
    for left, right in intervals:
        for y in range(25, 46):
            for x in range(left, right):
                pixels[x, y] = (35, 90, 190)

    bounds = _timecard_column_crop_bounds(image, 6, 1)

    assert bounds == []
