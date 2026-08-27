"""Interactive command line for the Impasto pipeline.

    python -m impasto            # interactive
    python -m impasto --dry-run  # everything except the paid API calls
"""
import argparse
import getpass
import sys
import traceback
from pathlib import Path

from . import config, deliverables, higgsfield, prepare, style

BANNER = "Impasto — photographs into oil paintings"
RESOLUTIONS = ["1K", "2K", "4K"]
RATIOS = ["16:9", "9:16", "1:1", "4:3", "source"]


# --- small prompt helpers ---------------------------------------------------

def ask_choice(question, options, default=0):
    print(f"\n{question}")
    for i, opt in enumerate(options):
        marker = " (default)" if i == default else ""
        print(f"  {i + 1}. {opt}{marker}")
    while True:
        raw = input(f"Choose 1-{len(options)} [{default + 1}]: ").strip()
        if not raw:
            return options[default]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  Not a valid choice.")


def ask_yes_no(question, default=True):
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{question} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def ensure_keys(need_vision):
    """Resolve credentials, prompting for anything missing."""
    keys = config.Keys()
    captured = {}

    if not keys.has_higgsfield:
        print("\nHiggsfield credentials are required for the repaint.")
        print("Create a key pair at https://cloud.higgsfield.ai — it is shown as ID:SECRET.")
        keys.hf_key = input("  HF_API_KEY (key ID): ").strip()
        keys.hf_secret = getpass.getpass("  HF_API_SECRET (hidden): ").strip()
        captured["HF_API_KEY"] = keys.hf_key
        captured["HF_API_SECRET"] = keys.hf_secret

    if need_vision and not keys.has_anthropic:
        print("\nAn Anthropic key lets Claude describe each photograph so the")
        print("repaint keeps that scene's composition. Leave blank to skip.")
        entered = getpass.getpass("  ANTHROPIC_API_KEY (hidden, optional): ").strip()
        if entered:
            keys.anthropic = entered
            captured["ANTHROPIC_API_KEY"] = entered

    if captured and ask_yes_no("\nSave these to .env for next time?", True):
        config.save_env_file(captured)
        print(f"  Saved to {config.ENV_FILE} (gitignored, permissions 600).")

    keys.export()
    return keys


def load_pan(path):
    """Optional {name: left_x} map. Entries may be a bare int or {"x": int}."""
    if not path:
        return {}
    import json
    raw = json.loads(Path(path).read_text())
    return {k: (v["x"] if isinstance(v, dict) else v)
            for k, v in raw.items() if not k.startswith("_")}


# --- the run ----------------------------------------------------------------

def process(image, opts, keys, out_root, dry_run):
    """Run one photograph through both stages. Returns True on success."""
    name = image.stem
    work = out_root / "_prepared"
    renders = out_root / "renders"
    renders.mkdir(parents=True, exist_ok=True)

    final = renders / f"{name}_oil.png"
    if final.exists() and not opts["overwrite"]:
        print(f"  {name}: already rendered, skipping")
        return True

    # Pre-crop so the model has no reshaping to do.
    if opts["ratio"] == "source":
        source = image
        print(f"  {name}: using source at its own ratio")
    else:
        source, orig, cropped, dropped = prepare.crop_to_ratio(
            image, work / f"{name}.png", opts["ratio"])
        print(f"  {name}: {orig[0]}x{orig[1]} -> {cropped[0]}x{cropped[1]} "
              f"({opts['ratio']}, {dropped}% dropped)")

    # Stage 1 — scene description.
    scene = None
    if opts["vision"] and keys.has_anthropic:
        try:
            scene = vision_describe(source, keys)
            print(f"    scene: {scene[:88]}{'...' if len(scene) > 88 else ''}")
        except Exception as exc:
            print(f"    vision failed ({exc}); falling back to a generic description")
    prompt = style.build_prompt(scene, opts["lighting"])

    (renders / f"{name}_prompt.txt").write_text(prompt + "\n")

    # Stage 2 — repaint.
    if dry_run:
        print(f"    [dry run] would repaint at {opts['resolution']} via {opts['model']}")
        return True

    try:
        url = higgsfield.repaint(
            source, prompt, opts["model"],
            resolution=opts["resolution"],
            aspect_ratio=None if opts["ratio"] == "source" else opts["ratio"],
        )
        higgsfield.download(url, final)
        print(f"    rendered -> {final}")
    except higgsfield.HiggsfieldError as exc:
        print(f"    FAILED: {exc}")
        return False

    # Finishing.
    written = deliverables.finish(
        final, out_root, name,
        logo_path=config.ROOT / "Impasto_Logo.png" if opts["watermark"] else None,
        pan_x=opts["pan"].get(name),
        make_phone=opts["phone"],
    )
    for path in written:
        print(f"    finished -> {path}")
    return True


def vision_describe(image, keys):
    from . import vision
    return vision.describe(image, api_key=keys.anthropic)


def main(argv=None):
    parser = argparse.ArgumentParser(description=BANNER)
    parser.add_argument("--input", default="input", help="folder of photographs")
    parser.add_argument("--output", default="output", help="destination folder")
    parser.add_argument("--dry-run", action="store_true",
                        help="prepare sources and build prompts, but spend nothing")
    parser.add_argument("--model", default=None, help="override the repaint model id")
    parser.add_argument("--pan", default=None,
                        help="JSON map of {name: left_x} for hand-tuned 9:16 crops")
    args = parser.parse_args(argv)

    in_dir, out_dir = Path(args.input), Path(args.output)
    print(f"\n{BANNER}\n{'=' * len(BANNER)}")

    images = prepare.find_images(in_dir)
    if not images:
        print(f"\nNo images found in {in_dir}/")
        print("Drop your photographs in there and run this again.")
        return 1
    print(f"\nFound {len(images)} image(s) in {in_dir}/")

    opts = {
        "resolution": ask_choice("Output resolution?", RESOLUTIONS, default=1),
        "ratio": ask_choice("Aspect ratio?", RATIOS, default=0),
        "lighting": ask_choice(
            "Lighting treatment?",
            ["warm (golden hour, the default look)", "cool (keeps blue/overcast moods)"],
            default=0).split()[0],
        "phone": ask_yes_no("Also produce a 9:16 phone crop?", True),
        "watermark": ask_yes_no("Watermark the wide version?", False),
        "overwrite": False,
        "vision": True,
        "model": args.model or config.model_id(),
        "pan": load_pan(args.pan),
    }

    opts["vision"] = ask_yes_no(
        "Use Claude to describe each photo? (better fidelity, needs an Anthropic key)", True)

    if args.dry_run:
        keys = config.Keys()   # use whatever is already configured; never prompt
        keys.export()
    else:
        keys = ensure_keys(need_vision=opts["vision"])
    if not keys.has_higgsfield and not args.dry_run:
        print("\nNo Higgsfield credentials — cannot repaint. Re-run with --dry-run to test.")
        return 1
    if opts["vision"] and not keys.has_anthropic:
        print("\nNo Anthropic key: falling back to a generic scene description.")
        opts["vision"] = False

    print(f"\n{'-' * 60}")
    print(f"  {len(images)} image(s) at {opts['resolution']}, {opts['ratio']}, "
          f"{opts['lighting']} light")
    print(f"  model: {opts['model']}")
    if args.dry_run:
        print("  DRY RUN — no API calls, nothing spent")
    print(f"{'-' * 60}")

    if not args.dry_run and not ask_yes_no("\nProceed? This spends Higgsfield credits.", False):
        print("Cancelled.")
        return 0

    ok = 0
    for i, image in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] {image.name}")
        try:
            ok += bool(process(image, opts, keys, out_dir, args.dry_run))
        except KeyboardInterrupt:
            print("\nInterrupted.")
            return 130
        except Exception:
            print(f"  unexpected error on {image.name}:")
            traceback.print_exc(limit=2)

    print(f"\nDone: {ok}/{len(images)} succeeded. Output in {out_dir}/")
    return 0 if ok == len(images) else 1


if __name__ == "__main__":
    sys.exit(main())
