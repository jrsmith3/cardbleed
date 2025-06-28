# Portions of this file were written with the help of GitHub Copilot
# Chat, an AI tool by GitHub. Final content was reviewed and adapted
# by a human.

import argparse
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

def test_frill(sample_image):
    frilled = frill(sample_image)
    assert frilled.size == (30, 30)

def test_add_bleed(sample_image):
    result = add_bleed(sample_image, width=20, height=20)
    assert result.size == (20, 20)

def test_add_dimensioned_bleed(sample_image):
    result = add_dimensioned_bleed(
        sample_image, width=1.0, height=1.0, bleed_width=2.0, bleed_height=2.0
    )
    assert result.size == (20, 20)

def test_strip_pixels(sample_image):
    result = strip_pixels(sample_image, "left", "right")
    assert result.size == (8, 10)
    result2 = strip_pixels(sample_image, "top", "bottom")
    assert result2.size == (10, 8)

def test_create_parser_returns_argparse():
    parser = create_parser()
    assert isinstance(parser, argparse.ArgumentParser)

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
    ]
    ns = parser.parse_args(args)
    assert ns.width == 2.5
    assert ns.height == 3.5
    assert ns.bleed_width == 2.75
    assert ns.bleed_height == 3.75
    assert ns.dpi == 72
    assert ns.input_file.name == str(img_file)
    assert str(ns.output_directory) == str(output_dir.resolve())

@pytest.mark.parametrize("cli_args", [
    ["--width", "2.5", "--height", "3.5", "--bleed_width", "2.75", "--bleed_height", "3.75"],
])
def test_cli_runs_and_creates_output(tmp_path, cli_args, monkeypatch):
    # Prepare input image and output directory
    img_file = tmp_path / "test.png"
    Image.new("RGB", (10, 10)).save(img_file)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    # Prepare CLI arguments
    args = cli_args + [
        str(img_file),
        str(output_dir),
    ]
    monkeypatch.setattr(sys, "argv", ["cardbleed"] + args)
    # Patch sys.exit to prevent pytest from exiting
    monkeypatch.setattr(sys, 'exit', lambda x=0: (_ for _ in ()).throw(SystemExit(x)))
    # Run main, expecting files to be written
    try:
        cardbleed_main()
    except SystemExit:
        pass
    # Check that at least one PNG was written
    pngs = list(output_dir.glob("*.png"))
    assert len(pngs) >= 1

def test_cli_strip_and_quiet(tmp_path, monkeypatch):
    img_file = tmp_path / "test.png"
    Image.new("RGB", (10, 10)).save(img_file)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    args = [
        "--width", "2.5",
        "--height", "3.5",
        "--bleed_width", "2.75",
        "--bleed_height", "3.75",
        "--strip", "left",
        "--quiet",
        str(img_file),
        str(output_dir),
    ]
    monkeypatch.setattr(sys, "argv", ["cardbleed"] + args)
    monkeypatch.setattr(sys, 'exit', lambda x=0: (_ for _ in ()).throw(SystemExit(x)))
    try:
        cardbleed_main()
    except SystemExit:
        pass
    pngs = list(output_dir.glob("*.png"))
    assert len(pngs) >= 1
