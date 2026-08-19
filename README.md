# Impasto — oil-paint wallpaper pipeline

Turns a folder of photographs into gallery-grade oil-paint wallpapers at 4K, then cuts
them into desktop (16:9) and iPhone (9:16) deliverables.

The repaint is **image-to-image**, never text-to-image. The photograph supplies
composition, proportion and light; the model only rewrites the *surface* into thick
hand-applied paint. That single constraint is what separates this from the smooth
digital slop a blank prompt produces.

## Sample

| Source photograph | Repainted at 4K |
|---|---|
| ![source](samples/Golf02_source.jpg) | ![oil](samples/Golf02_oil.jpg) |

Detail at 100%, straight from the 5504×3072 render — palette-knife ridges catching the
light, canvas weave showing through the thinner passages:

![detail](samples/Golf02_oil_detail.jpg)

The exact prompt that produced it is in [`samples/Golf02_prompt.txt`](samples/Golf02_prompt.txt).

## How it works

```
Input_Images/<pack>/            your photographs (jpg / png / heic)
        │
        │  prepare_sources.sh — pre-crop to the target aspect ratio
        ▼
Input_Prepared/<pack>/          sources already at 16:9
        │
        │  Stage 1  an agent views each photo and writes a tailored prompt
        │  Stage 2  Higgsfield `generate_image` (Nano Banana Pro), image-to-image
        ▼
Processed_Images/<pack>/        <name>_oil.png at 4K  +  <name>_prompt.txt sidecar
        │
        │  make_deliverables.py — watermark + pan-and-scan
        ▼
Deliverables/Photos/<pack>/     Desktop_16x9/  and  iPhone_9x16/
```

Two stages do the real work:

**Stage 1 — vision to prompt.** An agent (Claude Code, via native vision) opens each
photograph and writes a prompt in two parts. Part A is one variable sentence naming the
actual scene. Part B is a fixed style block appended verbatim from
[`style_block.txt`](style_block.txt). Splitting them is what keeps the style from
drifting across a pack — only the scene sentence flexes.
[`style_block_cool.txt`](style_block_cool.txt) is the same block minus the warm-light
clause, for images that must keep a cool or blue mood.

**Stage 2 — repaint.** The prepared source is uploaded to Higgsfield
(`media_upload` → PUT bytes → `media_confirm`), then passed to `generate_image` with
model `nano_banana_pro` as the image-to-image input. The upload path is fully
scriptable, so a pack runs unattended.

### Why sources are pre-cropped

Image-to-image non-uniformly scales the source to fill the requested `aspect_ratio`,
which squishes the geometry. Feeding a source already at the target ratio leaves the
model no reshaping to do. That is the whole job of `prepare_sources.sh`.

## Usage

```bash
./prepare_sources.sh Prod01_IMG/Sports 16 9 center
```

Then run the repaint (Stage 1 + 2 are driven by the agent against the Higgsfield MCP),
and finish the pack:

```bash
/usr/bin/python3 make_deliverables.py \
    --src Processed_Images/Prod01_IMG/Sports_02 \
    --out Deliverables/Photos/Prod01_Sports \
    --pan packs/prod01_sports.pan.json
```

Add `--watermark` to composite the Impasto mark into the bottom-right of the 16:9
output. The phone crops are always left clean.

Pan offsets live in `packs/*.pan.json` as the left-edge x of the 9:16 crop in source
pixels, chosen by eye per image so the subject survives the crop. Any name missing from
the file is centre-cropped.

> **macOS note:** use `/usr/bin/python3`. The system interpreter ships with Pillow 11.3
> already installed; the Homebrew and python.org interpreters on this machine do not
> have it. Otherwise `pip install -r requirements.txt`.

## Costs

Measured against Higgsfield Plus credits.

| Job | Config | Credits |
|---|---|---|
| Repaint, 2K | `nano_banana_pro` | 2 / image |
| Repaint, 4K | `nano_banana_pro` | 4 / image |
| Video, 1080p | Seedance 2.0, 7s, silent, high bitrate | 63 |
| Video, 4K | Seedance 2.0, 7s, silent, high bitrate | 154 |
| Video, cheap | Kling 3.0 pro, 5s, silent | 8.75 |

A 12-image pack costs 48 credits at 4K. Kling is ~7× cheaper than Seedance for video
but destroys the impasto texture — see [field notes](docs/field-notes.md#video).

## Repo layout

```
prepare_sources.sh          pre-crop sources to the target aspect ratio
make_deliverables.py        16:9 + 9:16 finishing, optional watermark
style_block.txt             fixed Part B of the prompt (warm)
style_block_cool.txt        same, minus the warm-light clause
packs/*.pan.json            per-image 9:16 pan offsets
samples/                    one before/after pair + its prompt
docs/field-notes.md         what works, what fails, and why
docs/phase-1-brief.md       the original build spec
```

The image working folders (`Input_Images/`, `Input_Prepared/`, `Processed_Images/`,
`Deliverables/`) are **not tracked** — they run to ~1.7 GB and the renders are
reproducible from the sidecar prompts. Only `samples/` is committed.

## Status

Phase 1 is complete: folder in, 4K oil-paint stills out, cut to two delivery formats.

- **Prod01 Sports** — 12/12 shipped at 5504×3072.
- **Video** — under evaluation. Seedance 2.0 holds the paint texture; Kling does not.
- **Next packs** — Villa (expected to run clean: sunlit, broad surfaces) and Larp
  (needs generated bases for the watches and cars).

## Licensing

Use own photographs, licensed stock, or AI-generated bases only. Note that arena and
event photography is frequently licensed *editorial use only*, which is a contract term
excluding resale merchandise — separate from any trademark question. Verify current
Higgsfield / Nano Banana commercial terms before selling output.
