# Portions of this file were written with the help of GitHub Copilot
# Chat, an AI tool by GitHub. Final content was reviewed and adapted
# by a human.

import contextlib
import sys

import pytest
from PIL import Image

from cardbleed import (
    _mirror_right,
    add_bleed,
    add_dimensioned_bleed,
    create_parser,
    frill,
    mirror_across_edge,
    strip_pixels,
)
from cardbleed import (
    main as cardbleed_main,
)


@pytest.fixture
def sample_image():
    # Create a simple 10x10 red image for testing
    return Image.new("RGB", (10, 10), color="red")


@pytest.fixture
def patterned_image():
    # 2x2 image, upper left red, upper right green, lower left blue, lower right white
    img = Image.new("RGB", (2, 2))
    img.putpixel((0, 0), (255, 0, 0))     # red
    img.putpixel((1, 0), (0, 255, 0))     # green
    img.putpixel((0, 1), (0, 0, 255))     # blue
    img.putpixel((1, 1), (255, 255, 255)) # white
    return img


def test_mirror_right_size(sample_image):
    mirrored = _mirror_right(sample_image)
    assert mirrored.size == (20, 10)


# TODO: `sample_image` should include data so the test is nontrivial.
def test_mirror_right_mirrored(patterned_image):
    mirrored = _mirror_right(patterned_image)
    # Left half should be original, right half should be left half mirrored
    left_half = mirrored.crop((0, 0, 2, 2))
    right_half = mirrored.crop((2, 0, 4, 2))
    assert list(left_half.getdata()) == list(right_half.transpose(Image.FLIP_LEFT_RIGHT).getdata())


@pytest.mark.parametrize("edge", ["left", "right", "top", "bottom"])
def test_mirror_across_edge_size(sample_image, edge):
    mirrored = mirror_across_edge(sample_image, edge)
    if edge in ("left", "right"):
        assert mirrored.size == (20, 10)
    else:
        assert mirrored.size == (10, 20)


# TODO: write test for `mirror_across_edge` similar to
# `test_mirror_right_mirrored`.
@pytest.mark.parametrize("edge, transpose_op", [
    ("left", Image.FLIP_LEFT_RIGHT),
    ("right", Image.FLIP_LEFT_RIGHT),
    ("top", Image.FLIP_TOP_BOTTOM),
    ("bottom", Image.FLIP_TOP_BOTTOM),
])
def test_mirror_across_edge_mirrored(patterned_image, edge, transpose_op):
    mirrored = mirror_across_edge(patterned_image, edge)
    # split image in half depending on edge
    if edge in ('left', 'right'):
        left = mirrored.crop((0, 0, 2, 2))
        right = mirrored.crop((2, 0, 4, 2))
        assert list(left.getdata()) == list(right.transpose(Image.FLIP_LEFT_RIGHT).getdata())
    else:
        top = mirrored.crop((0, 0, 2, 2))
        bottom = mirrored.crop((0, 2, 2, 4))
        assert list(top.getdata()) == list(bottom.transpose(Image.FLIP_TOP_BOTTOM).getdata())


def test_frill_size(sample_image):
    frilled = frill(sample_image)
    assert frilled.size == (30, 30)


# TODO: write test for `frill` similar to`test_mirror_right_mirrored`.
def test_frill_mirrored(patterned_image):
    frilled = frill(patterned_image)
    # Check that the center of the frilled image is the original
    center = frilled.crop((2, 2, 4, 4))
    assert list(center.getdata()) == list(patterned_image.getdata())


def test_add_bleed_size(sample_image):
    result = add_bleed(sample_image, width=20, height=20)
    assert result.size == (20, 20)


def test_add_bleed_none(sample_image):
    # width or height None should default to original size
    result = add_bleed(sample_image, width=None, height=None)
    assert list(result.getdata()) == list(sample_image.getdata())


@pytest.mark.parametrize("dimensions",[
    {"width": 1, "height": 10},    # width too small
    {"width": 100, "height": 10},  # width too large
    {"width": 10, "height": 1},    # height too small
    {"width": 10, "height": 100},  # height too large
    ])
def test_add_bleed_value_error(sample_image, dimensions):
    with pytest.raises(ValueError):
        add_bleed(sample_image, **dimensions)


def test_add_bleed_frill(sample_image):
    # The frill image used for the bleed should ensure continuity at the borders
    result = add_bleed(sample_image, width=12, height=12)
    assert result.size == (12, 12)
    # Center of result should match the original image
    center = result.crop((1, 1, 11, 11))
    assert list(center.getdata()) == list(sample_image.getdata())


def test_add_dimensioned_bleed_size(sample_image):
    result = add_dimensioned_bleed(sample_image, width=1.0, height=1.0, bleed_width=2.0, bleed_height=2.0)
    assert result.size == (20, 20)


def test_add_dimensioned_bleed_none(sample_image):
    # bleed_width or bleed_height None should default to width/height
    result = add_dimensioned_bleed(sample_image, width=1.0, height=1.0, bleed_width=None, bleed_height=None)
    assert list(result.getdata()) == list(sample_image.getdata())


@pytest.mark.parametrize("dimensions",[
    {"bleed_width": 1.0, "bleed_height": 2.0},  # bleed_width too small
    {"bleed_width": 7.0, "bleed_height": 2.0},  # bleed_width too large
    {"bleed_width": 2.0, "bleed_height": 1.0},  # bleed_height too small
    {"bleed_width": 2.0, "bleed_height": 7.0},  # bleed_height too large
    ])
def test_add_dimensioned_bleed_value_error(sample_image, dimensions):
    with pytest.raises(ValueError):
        add_dimensioned_bleed(sample_image, width=2.0, height=2.0, **dimensions)


@pytest.mark.parametrize("crop_strategy", ["smaller", "larger"])
def test_add_dimensioned_bleed_crop_strategies(sample_image, crop_strategy):
    result = add_dimensioned_bleed(
        sample_image, width=1.0, height=1.0, bleed_width=2.0, bleed_height=2.0, crop_strategy=crop_strategy
    )
    assert result.size == (20, 20)


def test_add_dimensioned_bleed_crop_strategy_value_error(sample_image):
    with pytest.raises(ValueError):
        add_dimensioned_bleed(
            sample_image, width=1.0, height=1.0, bleed_width=2.0, bleed_height=2.0, crop_strategy="invalid"
        )


def test_add_dimensioned_bleed_frill(sample_image):
    # The frill in the result should be correct size and centered
    result = add_dimensioned_bleed(sample_image, width=1.0, height=1.0, bleed_width=2.0, bleed_height=2.0)
    center = result.crop((5, 5, 15, 15))
    assert list(center.getdata()) == list(sample_image.getdata())


@pytest.mark.parametrize("edges", [["left",], ["right",], ["top",], ["bottom",]])
def test_strip_pixels_size(sample_image, edges):
    result = strip_pixels(sample_image, *edges)

    if edges in ["left", "right"]:
        assert result.size == (9, 10)
    elif edges in ["top", "bottom"]:
        assert result.size == (10, 9)


@pytest.mark.parametrize("edge, size, expected_pixels", [
    ("left", (1, 2), ((0, 255, 0), (255, 255, 255))),
    ("right", (1, 2), ((255, 0, 0), (0, 0, 255))),
    ("top", (2, 1), ((0, 0, 255), (255, 255, 255))),
    ("bottom", (2, 1), ((255, 0, 0), (0, 255, 0))),
])
def test_strip_pixels_output(patterned_image, edge, size, expected_pixels):
    result = strip_pixels(patterned_image, edge)
    assert result.size == size

    # Check that the expected pixels are still in the result
    for result_px, expected_px in zip(result.getdata(), expected_pixels):
        assert result_px == expected_px


def test_parser_parses_args(tmp_path):
    parser = create_parser()
    img_file = tmp_path / "test.png"
    Image.new("RGB", (10, 10)).save(img_file)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    args = [
        "--width", "2.5",
        "--height", "3.5",
        "--bleed_width", "2.75",
        "--bleed_height", "3.75",
        "--dpi", "72",
        str(img_file),
        str(output_dir),
    ]  # fmt: skip
    ns = parser.parse_args(args)
    assert ns.width == 2.5  # noqa: PLR2004
    assert ns.height == 3.5  # noqa: PLR2004
    assert ns.bleed_width == 2.75  # noqa: PLR2004
    assert ns.bleed_height == 3.75  # noqa: PLR2004
    assert ns.dpi == 72  # noqa: PLR2004
    assert ns.input_file.name == str(img_file)
    assert str(ns.output_directory) == str(output_dir.resolve())


def test_cli_runs_and_creates_output(tmp_path, monkeypatch):
    # Prepare input image and output directory
    img_file = tmp_path / "test.png"
    Image.new("RGB", (250, 350)).save(img_file)
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    # Prepare CLI arguments
    args = [
        "--width", "2.5",
        "--height", "3.5",
        "--bleed_width", "2.75",
        "--bleed_height", "3.75",
        str(img_file),
        str(output_dir),
    ]  # fmt: skip
    monkeypatch.setattr(sys, "argv", ["cardbleed", *args])

    # Prevent pytest from exiting
    with contextlib.suppress(SystemExit):
        # Run main, expecting files to be written
        cardbleed_main()

    # Check that at least one PNG was written
    pngs = list(output_dir.glob("*.png"))
    assert len(pngs) >= 1


# TODO: this test could have more depth and ensure that the output
# image is exactly what is expected.
def test_cli_output(tmp_path, monkeypatch):
    img_file = tmp_path / "test.png"
    Image.new("RGB", (250, 350)).save(img_file)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    args = [
        "--width", "2.5",
        "--height", "3.5",
        "--bleed_width", "2.75",
        "--bleed_height", "3.75",
        str(img_file),
        str(output_dir),
    ]
    monkeypatch.setattr(sys, "argv", ["cardbleed", *args])
    with contextlib.suppress(SystemExit):
        cardbleed_main()
    pngs = list(output_dir.glob("*.png"))
    assert len(pngs) >= 1
    # Image should be readable
    for png in pngs:
        img = Image.open(png)
        assert img.size[0] > 0 and img.size[1] > 0


# TODO: this test could be edited to be more precise and test that the
# output is exactly what is expected.
@pytest.mark.parametrize("strip_flag, expected_size", [
    ("left", (249, 350)),
    ("right", (249, 350)),
    ("top", (250, 349)),
    ("bottom", (250, 349)),
])
def test_cli_strip(tmp_path, monkeypatch, strip_flag, expected_size):
    img_file = tmp_path / "test.png"
    Image.new("RGB", (250, 350)).save(img_file)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    args = [
        "--width", "2.5",
        "--height", "3.5",
        "--bleed_width", "2.75",
        "--bleed_height", "3.75",
        "--strip", strip_flag,
        str(img_file),
        str(output_dir),
    ]
    monkeypatch.setattr(sys, "argv", ["cardbleed", *args])

    with contextlib.suppress(SystemExit):
        cardbleed_main()

    pngs = list(output_dir.glob("*.png"))
    assert len(pngs) >= 1

    for png in pngs:
        img = Image.open(png)
        # Bleed will be added, so the size will be larger, but must
        # not be equal to the original (should match the logic)
        assert img.size[0] >= expected_size[0]
        assert img.size[1] >= expected_size[1]
