# -*- coding: UTF-8 -*-
from PIL import Image


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
        edge (str): Edge across which to mirror. Can be "top", "bottom",
            "left", or "right" (case insensitive).

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

    A "frill" image is created by mirroring and translating a given image
    around the perimiter of the image.

    Args:
        im (PIL.Image): From which to create frill.

    Returns:
        PIL.Image
    """
    # This function ends up creating an image that is a set of 3x3 transposes
    # of the original. I will start by creating the middle set of three
    # images, then mirror across the top and bottom of that image.
    
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
