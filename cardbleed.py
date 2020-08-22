# -*- coding: UTF-8 -*-
import argparse
import itertools
import os

from pdf2image import convert_from_bytes
from PIL import Image, UnidentifiedImageError


def _mirror_right(im):
    """
    Create image plus its mirror across original image right edge

    Args:
        im (PIL.Image): Image to mirror.

    Returns:
        PIL.Image
    """
    base_w, base_h = im.size

    mirrored_im = im.transpose(Image.FLIP_LEFT_RIGHT)

    result_im = Image.new(mode=im.mode, size=(2 * base_w, base_h))

    result_im.paste(im)
    result_im.paste(mirrored_im, box=(base_w, 0))

    return result_im


def mirror_across_edge(im, edge):
    """
    Create image plus its mirror attached across specified edge

    Args:
        im (PIL.Image): Image to mirror.
        edge (str): Edge across which to mirror. Can be "top",
            "bottom", "left", or "right" (case insensitive).

    Returns:
        PIL.Image
    """
    edj = edge.lower()

    transforms = {
            "top": [Image.ROTATE_270, Image.ROTATE_90],
            "bottom": [Image.ROTATE_90, Image.ROTATE_270],
            "left": [Image.ROTATE_180, Image.ROTATE_180]
        }

    if edj in transforms.keys():
        rot_im = im.transpose(transforms[edj][0])
        mirrored_im = _mirror_right(rot_im)
        result_im = mirrored_im.transpose(transforms[edj][1])
    elif edj == "right":
        result_im = _mirror_right(im)
    else:
        raise ValueError("Invalid value for 'edge'.")

    return result_im


def frill(im):
    """
    Create frill image of card image

    A "frill" image is created by mirroring and translating a given
    image around the perimiter of the image.

    Args:
        im (PIL.Image): From which to create frill.

    Returns:
        PIL.Image
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

    return res_im


def add_bleed(im, width=None, height=None):
    """
    Add bleed border around image using a frill

    Args:
        im (PIL.Image): Image to which bleed will be added.
        width (int): Width, in pixels, of the resulting image. Must be
            between one and three times the value of the pixel-width
            of `im`. If `None`, the resulting image will be the same
            width as the `im`.
        height (int): Height, in pixels, of the resulting image. Must
            be between one and three times the value of the
            pixel-height of `im`. If `None`, the resulting image will
            be the same height as `im`.

    Returns:
        PIL.Image

    Raises:
        ValueError: If the width and height values aren't within the
            proper range.
    """
    base_w, base_h = im.size

    if width is None:
        w = base_w
    else:
        w = int(width)

    if height is None:
        h = base_h
    else:
        h = int(height)

    def check_out_of_bounds(val, target, name):
        err_dict = {"val": val, "target": target, "name": name}

        if val < target:
            err_msg = "{name} ({val}) must be greater than image pixel-{name} ({target})"
            raise ValueError(err_msg.format(**err_dict))
    
        elif val > 3 * target:
            err_msg = "{name} ({val}) must be less than and 3 times image pixel-{name} ({target})"
            raise ValueError(err_msg.format(**err_dict))

    check_out_of_bounds(width, base_w, "width")
    check_out_of_bounds(height, base_h, "height")

    frill_im = frill(im)

    border_w = int((w - base_w)/2)
    border_h = int((h - base_h)/2)

    box = (base_w - border_w,
        base_h - border_h,
        2 * base_w + border_w,
        2 * base_h + border_h)

    res_im = frill_im.crop(box=box)

    return res_im


def add_dimensioned_bleed(im, width, height, bleed_width=None, bleed_height=None, crop_strategy="smaller", **_):
    """
    Add bleed border using frill given image linear spatial dimensions

    This function adds a bleed around an image specified in a linear
    spatial unit (e.g. inch, mm, etc.). The actual unit does not
    matter since this function translates them into pixels. The caller
    must specify the width and height of the image as well as the
    width and height of the full bleed.

    Args:
        im (PIL.Image): Image to which bleed will be added.
        width (float): Width of image in a linear spatial unit.
        height (float): Height of image in a linear spatial unit.
        bleed_width (float): Width of full bleed in linear spatial
            unit. Must be between 1 and 3 times the specified `width`.
            If `None`, resulting image will be the same width as `im`.
        bleed_height (float): height of full bleed in linear spatial
            unit. Must be between 1 and 3 times the specified
            `height`. If `None`, resulting image will be the same
            height as `im`.
        crop_strategy (str): Either "smaller" or "larger"
            (case-insensitive). If "smaller", some of the image may be
            cropped out of the resulting image. If "larger", some of
            the frill may be cropped in.
        **_ (dict): Ignore everything else that's passed to the
            function.

    Returns:
        PIL.Image

    Raises:
        ValueError: If the bleed_width and bleed_height values aren't
            within the proper range.
    """
    base_w, base_h = im.size

    if bleed_width is None:
        bleed_w = width
    else:
        bleed_w = bleed_width

    if bleed_height is None:
        bleed_h = height
    else:
        bleed_h = bleed_height

    def check_out_of_bounds(val, target, val_name, target_name):
        err_dict = {"val": val, "target": target, "val_name": val_name, "target_name": target_name}

        if val < target:
            err_msg = "{val_name} ({val}) must be greater than image {target_name} ({target})"
            raise ValueError(err_msg.format(**err_dict))
    
        elif val > 3 * target:
            err_msg = "{val_name} ({val}) must be less than 3 times image {target_name} ({target})"
            raise ValueError(err_msg.format(**err_dict))

    check_out_of_bounds(bleed_w, width, "bleed_width", "width")
    check_out_of_bounds(bleed_h, height, "bleed_height", "height")

    cs = crop_strategy.lower()
    if cs not in {"larger", "smaller"}:
        raise ValueError("crop_strategy must either be 'larger' or 'smaller'")

    ppi_w = base_w / width
    ppi_h = base_h / height

    if ppi_w > ppi_h:
        ppi_larger = ppi_w
        ppi_smaller = ppi_h
    else:
        ppi_larger = ppi_h
        ppi_smaller = ppi_w

    if cs == "smaller":
        ppi = ppi_smaller
    else:
        ppi = ppi_larger

    bleed_width_pixels = int(bleed_width * ppi)
    bleed_height_pixels = int(bleed_height * ppi)

    res_im = add_bleed(im, width=bleed_width_pixels, height=bleed_height_pixels)

    return res_im


def create_parser():
    """
    Factory to create ArgumentParser object defining interface

    Returns:
        argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser("cardbleed", description="Create card images with bleed from PDF.")

    parser.add_argument("--width", type=float, required=True, help="Width of original card.")
    parser.add_argument("--height", type=float, required=True, help="Height of original card.")
    parser.add_argument("--bleed_width", type=float, required=True, help="Width of card including the added bleed.")
    parser.add_argument("--bleed_height", type=float, required=True, help="Height of card including the added bleed.")
    parser.add_argument("--crop_strategy", default="smaller", choices={"smaller", "larger"})
    parser.add_argument("input_file", type=argparse.FileType("rb"), help="Location of file containing card image(s).")
    parser.add_argument("output_directory", help="Directory to which images with bleeds should be written. Directory must exist prior to running this program.")

    return parser


def output_filenames(pad_width=0):
    """
    Infinite generator of output filenames

    Yields:
        str: Output filename.
    """
    sides = itertools.cycle(("front", "back"))
    slug = "{:0{pad_width}d}_card{card_no}_{side}"

    for iteration, side in zip(itertools.count(), sides):
        card_no = int(iteration/2)
        filename = slug.format(iteration, card_no=card_no, pad_width=pad_width, side=side)
        yield filename


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    try:
        img = Image.open(args.input_file)
        imgs = [img,]
    except UnidentifiedImageError:
        args.input_file.seek(0)
        imgs = convert_from_bytes(args.input_file.read())

    for im in imgs:
        output_file = os.path.join(args.output_directory, "foo.png")

        result = add_dimensioned_bleed(im, **vars(args))
        result.save(output_file)
