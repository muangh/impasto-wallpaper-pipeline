"""Pre-crop sources to the target aspect ratio before upload.

Image-to-image non-uniformly scales the source to fill the requested aspect
ratio, which squishes the geometry. Feeding a source already at the target
ratio leaves the model no reshaping to do.
"""
from pathlib import Path

from PIL import Image

RATIOS = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1), "4:3": (4, 3), "3:4": (3, 4)}
SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}


def find_images(folder):
    """Every readable image in a folder, sorted, ignoring dotfiles."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in SUFFIXES and not p.name.startswith(".")
    )


def crop_to_ratio(src, dest, ratio="16:9", anchor="center"):
    """Centre-crop the largest region of `ratio` that fits, and save as PNG."""
    tw, th = RATIOS.get(ratio, (16, 9))
    try:
        im = Image.open(src)
    except Exception as exc:
        raise ValueError(f"{Path(src).name}: cannot read image ({exc})") from exc
    im = im.convert("RGB")
    w, h = im.size

    cw, ch = min(w, round(h * tw / th)), min(h, round(w * th / tw))
    if anchor == "left":
        left = 0
    elif anchor == "right":
        left = w - cw
    else:
        left = (w - cw) // 2
    if anchor == "top":
        top = 0
    elif anchor == "bottom":
        top = h - ch
    else:
        top = (h - ch) // 2

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.crop((left, top, left + cw, top + ch)).save(dest)
    dropped = round((1 - (cw * ch) / (w * h)) * 100)
    return dest, (w, h), (cw, ch), dropped
