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
