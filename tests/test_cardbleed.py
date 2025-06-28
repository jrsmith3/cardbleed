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


def test_mirror_right_size(sample_image):
    mirrored = _mirror_right(sample_image)
    assert mirrored.size == (20, 10)


# TODO: `sample_image` should include data so the test is nontrivial.
def test_mirror_right_mirrored(sample_image):
    mirrored = _mirror_right(sample_image)
    left = mirrored.crop((0, 0, 10, 10))
    right = mirrored.crop((10, 0, 20, 10))
    assert list(left.getdata()) == list(right.transpose(Image.FLIP_LEFT_RIGHT).getdata())


@pytest.mark.parametrize("edge", ["left", "right", "top", "bottom"])
def test_mirror_across_edge_size(sample_image, edge):
    mirrored = mirror_across_edge(sample_image, edge)
    if edge in ("left", "right"):
        assert mirrored.size == (20, 10)
    else:
        assert mirrored.size == (10, 20)


# TODO: write test for `mirror_across_edge` similar to
# `test_mirror_right_mirrored`.


def test_frill_size(sample_image):
    frilled = frill(sample_image)
    assert frilled.size == (30, 30)


# TODO: write test for `frill` similar to`test_mirror_right_mirrored`.


def test_add_bleed_size(sample_image):
    result = add_bleed(sample_image, width=20, height=20)
    assert result.size == (20, 20)


# TODO: write the following tests for `add_bleed`.
#
# * Tests when `width` or `height` args are `None`.
# * Tests the conditions when `ValueError` is raised.
# * Tests the frill is as expected.


def test_add_dimensioned_bleed_size(sample_image):
    result = add_dimensioned_bleed(sample_image, width=1.0, height=1.0, bleed_width=2.0, bleed_height=2.0)
    assert result.size == (20, 20)


# TODO: write the following tests for `add_dimensioned_bleed`.
#
# * Tests when `bleed_width` or `bleed_height` are `None`.
# * Tests the conditions when `ValueError` is raised according to docstring.
# * Test both values of `crop_strategy`.
# * Test condition when `crop_strategy` raises `ValueError`.
# * Tests the bleed is as expected (proper mirroring, etc.).


@pytest.mark.parametrize("edges", [["left",], ["right",], ["top",], ["bottom",]])
def test_strip_pixels_size(sample_image, edges):
    result = strip_pixels(sample_image, *edges)

    if edges in ["left", "right"]:
        assert result.size == (9, 10)
    elif edges in ["top", "bottom"]:
        assert result.size == (10, 9)


# TODO: write test to ensure output of `strip_pixels` is as expected.


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


# TODO: write test to ensure output of CLI command is as expected.


# TODO: refactor the following test to only test the `--strip` flag.
# The test should be parameterized to test each case.
def test_cli_strip_and_quiet(tmp_path, monkeypatch):
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
        "--strip", "left",
        "--quiet",
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
