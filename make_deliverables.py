#!/usr/bin/env python3
"""Pack finishing: 16:9 desktop (optional watermark) + 9:16 iPhone (clean, pan-and-scan).

    /usr/bin/python3 make_deliverables.py \
        --src Processed_Images/Prod01_IMG/Sports_02 \
        --out Deliverables/Photos/Prod01_Sports \
        --pan packs/prod01_sports.pan.json

Add --watermark to composite the Impasto mark into the bottom-right of the 16:9.
Names absent from the pan file are centre-cropped.
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageFilter

LOGO_W = 560      # ~10% of the 5504px pack width: small but visible
MARGIN = 130      # inset from the bottom-right corner, in source pixels
PHONE_RATIO = (9, 16)


def build_watermark(logo_path):
    """Key the logo off its white background and return (text, shadow) RGBA layers.

    The source file is light grey text on solid white with no alpha, so
    compositing it directly would paste a white box onto the painting.
    """
    logo = Image.open(logo_path).convert("L")
    bbox = logo.point(lambda p: 255 if p < 235 else 0).getbbox()
    if bbox is None:
        sys.exit(f"{logo_path}: no dark pixels found, cannot key out the background")
    logo = logo.crop(bbox)

    # Text sits only ~38 levels below white, so the inverse-luminance alpha needs a boost.
    alpha = logo.point(lambda p: min(255, int((255 - p) * 6.0)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.4))

    logo_h = round(LOGO_W * (bbox[3] - bbox[1]) / (bbox[2] - bbox[0]))
    alpha = alpha.resize((LOGO_W, logo_h), Image.LANCZOS)

    text = Image.new("RGBA", (LOGO_W, logo_h), (255, 255, 255, 0))
    text.putalpha(alpha)

    # Blurred black copy, so the mark stays legible on pale images too.
    shadow = Image.new("RGBA", (LOGO_W, logo_h), (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda p: int(p * 0.7)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))

    return text, shadow


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="folder of <name>_oil.png renders")
    ap.add_argument("--out", required=True, help="destination pack folder")
    ap.add_argument("--pan", help="JSON map of {name: left_x} for the 9:16 crop")
    ap.add_argument("--logo", default="Impasto_Logo.png")
    ap.add_argument("--watermark", action="store_true",
                    help="composite the logo into the 16:9 output")
    args = ap.parse_args()

    desk_dir = os.path.join(args.out, "Desktop_16x9")
    phone_dir = os.path.join(args.out, "iPhone_9x16")
    os.makedirs(desk_dir, exist_ok=True)
    os.makedirs(phone_dir, exist_ok=True)

    pan = {}
    if args.pan:
        with open(args.pan) as fh:
            # Entries are either a bare left-edge x, or {"x": ..., "why": ...}.
            pan = {k: v["x"] if isinstance(v, dict) else v
                   for k, v in json.load(fh).items() if not k.startswith("_")}

    text = shadow = None
    if args.watermark:
        text, shadow = build_watermark(args.logo)

    names = sorted(n[:-8] for n in os.listdir(args.src) if n.endswith("_oil.png"))
    if not names:
        sys.exit(f"{args.src}: no *_oil.png files found")

    for name in names:
        im = Image.open(os.path.join(args.src, f"{name}_oil.png")).convert("RGB")
        w, h = im.size

        desk = im
        if args.watermark:
            desk = im.copy().convert("RGBA")
            x = w - MARGIN - text.width
            y = h - MARGIN - text.height
            desk.alpha_composite(shadow, (x + 3, y + 3))
            desk.alpha_composite(text, (x, y))
            desk = desk.convert("RGB")
        desk.save(os.path.join(desk_dir, f"{name}_oil.png"))

        crop_w = round(h * PHONE_RATIO[0] / PHONE_RATIO[1])
        default_left = (w - crop_w) // 2
        left = max(0, min(pan.get(name, default_left), w - crop_w))
        phone = im.crop((left, 0, left + crop_w, h))
        phone.save(os.path.join(phone_dir, f"{name}_oil_phone.png"))

        tag = "watermarked" if args.watermark else "clean"
        note = "" if name in pan else "  (centred: no pan entry)"
        print(f"{name}: desktop {tag}  |  phone {phone.size} @ x={left}{note}")

    print(f"\n{len(names)} images -> {args.out}")


if __name__ == "__main__":
    main()
