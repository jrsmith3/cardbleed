# -*- coding: UTF-8 -*-
import argparse
import itertools
import logging
import math
import pathlib

from pdf2image import convert_from_bytes
from PIL import Image, UnidentifiedImageError

HANDLER = logging.StreamHandler()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(HANDLER)


def _mirror_right(im: Image.Image) -> Image.Image:
    """
    Return image plus its mirror across original image right edge

    Args:
        im: Image to mirror.
    """
    base_w, base_h = im.size

    mirrored_im = im.transpose(Image.FLIP_LEFT_RIGHT)

    result_im = Image.new(mode=im.mode, size=(2 * base_w, base_h))

    result_im.paste(im)
    result_im.paste(mirrored_im, box=(base_w, 0))

    return result_im


def mirror_across_edge(im: Image.Image, edge: str) -> Image.Image:
    """
    Return image plus its mirror attached across specified edge

    Args:
        im: Image to mirror.
        edge: Edge across which to mirror. Can be "top",
            "bottom", "left", or "right" (case insensitive).
    """
    edj = edge.lower()

    transforms = {
        "top": [Image.ROTATE_270, Image.ROTATE_90],
        "bottom": [Image.ROTATE_90, Image.ROTATE_270],
        "left": [Image.ROTATE_180, Image.ROTATE_180],
    }

    if edj in transforms:
        rot_im = im.transpose(transforms[edj][0])
        mirrored_im = _mirror_right(rot_im)
        result_im = mirrored_im.transpose(transforms[edj][1])
    elif edj == "right":
        result_im = _mirror_right(im)
    else:
        raise ValueError("Invalid value for 'edge'.")  # noqa: TRY003, EM101

    return result_im


def frill(im: Image.Image) -> Image.Image:
    """
    Return frill image of card image

    A "frill" image is created by mirroring and translating a given
    image around the perimiter of the image.

    Args:
        im: From which to create frill.
    """
    # This function ends up creating an image that is a set of 3x3
    # transposes of the original. I will start by creating the middle
    # set of three images, then mirror across the top and bottom of
    # that image.

    base_w, base_h = im.size

    res_im = mirror_across_edge(im, edge="left")
    res_im = mirror_across_edge(res_im, edge="right")
    res_im = res_im.crop((0, 0, 3 * base_w, base_h))

    res_im = mirror_across_edge(res_im, edge="top")
    res_im = mirror_across_edge(res_im, edge="bottom")
    res_im = res_im.crop((0, 0, 3 * base_w, 3 * base_h))

    return res_im  # noqa: RET504


def add_bleed(im: Image.Image, width: int | None = None, height: int | None = None) -> Image.Image:
    """
    Return image with bleed border around image using a frill

    Args:
        im: Image to which bleed will be added.
        width: Width, in pixels, of the resulting image. Must be
            between one and three times the value of the pixel-width
            of `im`. If `None`, the resulting image will be the same
            width as the `im`.

        height: Height, in pixels, of the resulting image. Must be
            between one and three times the value of the pixel-height
            of `im`. If `None`, the resulting image will be the same
            height as `im`.

    Raises:
        ValueError: If the width and height values aren't within the
            proper range.
    """
    base_w, base_h = im.size

    w = base_w if width is None else int(width)
    h = base_h if height is None else int(height)

    def check_out_of_bounds(val, target, name):
        err_dict = {"val": val, "target": target, "name": name}

        if val < target:
            err_msg = "{name} ({val}) must be greater than image pixel-{name} ({target})"
            raise ValueError(err_msg.format(**err_dict))

        if val > 3 * target:
            err_msg = "{name} ({val}) must be less than 3 times image pixel-{name} ({target})"
            raise ValueError(err_msg.format(**err_dict))

    check_out_of_bounds(w, base_w, "width")
    check_out_of_bounds(h, base_h, "height")

    frill_im = frill(im)

    border_w = int((w - base_w) / 2)
    border_h = int((h - base_h) / 2)

    box = (base_w - border_w, base_h - border_h, 2 * base_w + border_w, 2 * base_h + border_h)

    res_im = frill_im.crop(box=box)

    return res_im  # noqa: RET504


def add_dimensioned_bleed(
    im: Image.Image,
    width: float,
    height: float,
    bleed_width: float | None = None,
    bleed_height: float | None = None,
    crop_strategy: str = "smaller",
    **_: dict,
) -> Image.Image:
    """
    Add bleed border using frill given image linear spatial dimensions

    This function adds a bleed around an image specified in a linear
    spatial unit (e.g. inch, mm, etc.). The actual unit does not
    matter since this function translates them into pixels. The caller
    must specify the width and height of the image as well as the
    width and height of the full bleed.

    Args:
        im: Image to which bleed will be added.
        width: Width of image in a linear spatial unit.
        height: Height of image in a linear spatial unit.
        bleed_width: Width of full bleed in linear spatial unit. Must
            be between 1 and 3 times the specified `width`. If `None`,
            resulting image will be the same width as `im`.
        bleed_height: height of full bleed in linear spatial unit.
            Must be between 1 and 3 times the specified `height`. If
            `None`, resulting image will be the same height as `im`.
        crop_strategy: Either "smaller" or "larger"
            (case-insensitive). If "smaller", some of the image may be
            cropped out of the resulting image. If "larger", some of
            the frill may be cropped in.
        **_: Ignore everything else that's passed to the function.

    Returns:
        Image with bleed border.

    Raises:
        ValueError: If the bleed_width and bleed_height values aren't
            within the proper range.
    """
    base_w, base_h = im.size

    bleed_w = width if bleed_width is None else bleed_width
    bleed_h = height if bleed_height is None else bleed_height

    def check_out_of_bounds(val, target, val_name, target_name):
        err_dict = {"val": val, "target": target, "val_name": val_name, "target_name": target_name}

        if val < target:
            err_msg = "{val_name} ({val}) must be greater than image {target_name} ({target})"
            raise ValueError(err_msg.format(**err_dict))

        if val > 3 * target:
            err_msg = "{val_name} ({val}) must be less than 3 times image {target_name} ({target})"
            raise ValueError(err_msg.format(**err_dict))

    check_out_of_bounds(bleed_w, width, "bleed_width", "width")
    check_out_of_bounds(bleed_h, height, "bleed_height", "height")

    cs = crop_strategy.lower()
    if cs not in {"larger", "smaller"}:
        raise ValueError("crop_strategy must either be 'larger' or 'smaller'")  # noqa TRY003, EM101

    ppi_w = base_w / width
    ppi_h = base_h / height

    if ppi_w > ppi_h:
        ppi_larger = ppi_w
        ppi_smaller = ppi_h
    else:
        ppi_larger = ppi_h
        ppi_smaller = ppi_w

    ppi = ppi_smaller if cs == "smaller" else ppi_larger

    bleed_width_pixels = int(bleed_w * ppi)
    bleed_height_pixels = int(bleed_h * ppi)

    res_im = add_bleed(im, width=bleed_width_pixels, height=bleed_height_pixels)

    return res_im  # noqa: RET504


def strip_pixels(im: Image.Image, *args) -> Image.Image:
    """
    Return image with line of pixels from specified edge removed

    Args:
        im: Image from which to strip pixels.
        args: Edge from which to remove pixels. Can be "top",
            "bottom", "left", or "right" (case insensitive).
    """
    edjs = {e.lower() for e in args}
    legal_values = {"top", "bottom", "left", "right"}

    if not edjs <= legal_values:
        raise ValueError("Edge must be 'top', 'bottom', 'left', or 'right'.")  # noqa TRY003, EM101

    base_w, base_h = im.size

    left = 0
    top = 0
    right = base_w
    bottom = base_h

    if "left" in edjs:
        left += 1

    if "top" in edjs:
        top += 1

    if "right" in edjs:
        right -= 1

    if "bottom" in edjs:
        bottom -= 1

    box = (left, top, right, bottom)
    result = im.crop(box)

    return result  # noqa: RET504


def create_parser() -> argparse.ArgumentParser:
    """
    Factory to create ArgumentParser object defining interface
    """
    parser = argparse.ArgumentParser("cardbleed", description="Create card images with bleed from PDF.")

    parser.add_argument("--width", type=float, required=True, help="Width of original card.")

    parser.add_argument("--height", type=float, required=True, help="Height of original card.")

    parser.add_argument("--bleed_width", type=float, required=True, help="Width of card including the added bleed.")

    parser.add_argument("--bleed_height", type=float, required=True, help="Height of card including the added bleed.")

    parser.add_argument("--crop_strategy", default="smaller", choices={"smaller", "larger"})

    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress all output.")

    parser.add_argument("--dpi", default=300, type=int, help="DPI value of resulting images.")

    parser.add_argument(
        "--strip",
        action="append",
        default=[],
        choices={"top", "bottom", "left", "right"},
        help="Remove single strip of pixels from specified side of image before adding the bleed.",
    )

    parser.add_argument("input_file", type=argparse.FileType("rb"), help="Location of file containing card image(s).")

    parser.add_argument(
        "output_directory",
        type=lambda p: pathlib.Path(p).absolute(),
        help="Directory to which images with bleeds should be written. Directory must exist prior to running this program.",
    )

    return parser


def output_filenames(parent_dir: str = ".", suffix: str = "", pad_width: int = 0) -> pathlib.Path:
    """
    Infinite generator of output filenames

    Filenames are of the form

        <FILE_NUMBER>_card<CARD_NUMBER>_<SIDE>

    FILE_NUMBER increments from 0 for each iteration of this function.
    The purpose of this filename component is to order the filenames
    according to their appearance in the input PDF file. CARD_NUMBER
    and SIDE should be self-explanatory. The FILE_NUMBER can be
    left-padded with zeros in order to produce an asciibetical
    sequence of filenames.

    Args:
        parent_dir: Prepended to the filename. Can also be a
            pathlib.Path type.
        suffix: File extension appended to the filename. The string
            can include a preceding dot or not.
        pad_width: Determines the number of zeros padding the left of
            the file number.

    Yields:
        Output filename.
    """
    sides = itertools.cycle(("front", "back"))
    slug = "{:0{pad_width}d}_card{card_no}_{side}"

    for file_no, side in zip(itertools.count(), sides):
        card_no = int(file_no / 2)
        filename = slug.format(file_no, card_no=card_no, pad_width=pad_width, side=side)

        ext = "." + suffix.lstrip(".")
        path = pathlib.Path(parent_dir, filename).with_suffix(ext)
        yield path


def main():
    parser = create_parser()
    args = parser.parse_args()

    logger = logging.getLogger("main")
    if args.quiet:
        logger.propagate = False

    try:
        img = Image.open(args.input_file)
        imgs = [
            img,
        ]
    except UnidentifiedImageError:
        args.input_file.seek(0)
        imgs = convert_from_bytes(args.input_file.read(), dpi=args.dpi)

    pad_width = int(math.log10(len(imgs))) + 1

    filenames = output_filenames(parent_dir=args.output_directory, suffix=".png", pad_width=pad_width)

    for im, output_file in zip(imgs, filenames, strict=False):
        logger.info(output_file)
        stripped = strip_pixels(im, *args.strip)
        result = add_dimensioned_bleed(stripped, **vars(args))
        result.save(output_file)


if __name__ == "__main__":
    main()
