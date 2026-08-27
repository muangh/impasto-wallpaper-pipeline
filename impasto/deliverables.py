"""Finishing: optional watermark on the wide render, plus a phone crop."""
from pathlib import Path

from PIL import Image, ImageFilter

LOGO_W = 560      # ~10% of a 5504px render: small but visible
MARGIN = 130      # inset from the corner, in source pixels


def build_watermark(logo_path, logo_w=LOGO_W):
    """Key the logo off its white background, returning (text, shadow) layers.

    The logo file is light grey text on solid white with no alpha, so
    compositing it directly would paste a white box onto the painting.
    """
    logo = Image.open(logo_path).convert("L")
    bbox = logo.point(lambda p: 255 if p < 235 else 0).getbbox()
    if bbox is None:
        raise ValueError(f"{logo_path}: no dark pixels found, cannot key out the background")
    logo = logo.crop(bbox)

    # Text sits only ~38 levels below white, so inverse luminance needs a boost.
    alpha = logo.point(lambda p: min(255, int((255 - p) * 6.0)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.4))
    logo_h = round(logo_w * (bbox[3] - bbox[1]) / (bbox[2] - bbox[0]))
    alpha = alpha.resize((logo_w, logo_h), Image.LANCZOS)

    text = Image.new("RGBA", (logo_w, logo_h), (255, 255, 255, 0))
    text.putalpha(alpha)

    # Blurred dark copy so the mark stays legible on pale images too.
    shadow = Image.new("RGBA", (logo_w, logo_h), (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda p: int(p * 0.7)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    return text, shadow


def watermark(image, text, shadow, margin=MARGIN):
    """Composite the mark into the bottom-right corner."""
    out = image.convert("RGBA")
    x = out.width - margin - text.width
    y = out.height - margin - text.height
    out.alpha_composite(shadow, (x + 3, y + 3))
    out.alpha_composite(text, (x, y))
    return out.convert("RGB")


def phone_crop(image, pan_x=None, ratio=(9, 16)):
    """Pan-and-scan to a portrait crop at native resolution."""
    w, h = image.size
    cw = round(h * ratio[0] / ratio[1])
    if cw > w:  # already portrait — crop vertically instead
        ch = round(w * ratio[1] / ratio[0])
        top = max(0, (h - ch) // 2)
        return image.crop((0, top, w, top + ch))
    left = (w - cw) // 2 if pan_x is None else pan_x
    left = max(0, min(left, w - cw))
    return image.crop((left, 0, left + cw, h))


def finish(render_path, out_dir, name, logo_path=None, pan_x=None, make_phone=True):
    """Write the finished deliverables for one render. Returns written paths."""
    out_dir = Path(out_dir)
    image = Image.open(render_path).convert("RGB")
    written = []

    wide_dir = out_dir / "Desktop_16x9"
    wide_dir.mkdir(parents=True, exist_ok=True)
    wide = image
    if logo_path and Path(logo_path).exists():
        text, shadow = build_watermark(logo_path)
        wide = watermark(image, text, shadow)
    wide_path = wide_dir / f"{name}_oil.png"
    wide.save(wide_path)
    written.append(wide_path)

    if make_phone:
        phone_dir = out_dir / "iPhone_9x16"
        phone_dir.mkdir(parents=True, exist_ok=True)
        phone_path = phone_dir / f"{name}_oil_phone.png"
        phone_crop(image, pan_x).save(phone_path)
        written.append(phone_path)

    return written
