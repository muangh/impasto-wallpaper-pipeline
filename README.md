# Impasto — oil-paint wallpaper pipeline

A command-line wrapper around Higgsfield that turns a folder of photographs into
oil-paint wallpapers. Drop images in `input/`, answer a few questions, collect
finished files from `output/`.

The repaint is **image-to-image**, never text-to-image. The photograph supplies
composition, proportion and light; the model only rewrites the *surface* into thick
hand-applied paint. That single constraint is what separates this from the smooth
digital slop a blank prompt produces.

A personal project, built to see how far a disciplined prompt structure and careful
source selection could push a generative model toward something that reads as a real
painted object rather than a filter.

## Gallery

### The full chain, end to end

One image carries every stage: a drone photograph, repainted at 4K, then animated into a
living painting.

| Source photograph | Repainted at 4K |
|---|---|
| ![source](samples/Boat01_source.jpg) | ![oil](samples/Boat01_oil.jpg) |

**▶ [Watch the 7-second animation](samples/Boat01_oil_video.mp4)** — GitHub plays it
inline when you open the file. The water shimmers and the surfers drift with the swell
while the camera holds completely still; the brushwork and canvas weave stay put.

This is deliberately the *hardest* case in the pack, and it's instructive. Close-up
overhead water fills the frame with fine detail, and the model preserves detail rather
than abstracting it — so the paint here is far subtler than elsewhere, closer to a
painterly treatment than to thick impasto. It earns its place as the hero because that
same dense surface makes it the best subject for motion, and because it is the one image
that runs the whole pipeline.

### Where the paint is most convincing

Broad, simple surfaces are what the style block was built for. This is the same render
at 100%, straight from 5504×3072 — palette-knife ridges catching the light, canvas weave
showing through the thinner passages:

| Source photograph | Repainted at 4K |
|---|---|
| ![source](samples/Golf02_source.jpg) | ![oil](samples/Golf02_oil.jpg) |

![detail](samples/Golf02_oil_detail.jpg)

### Range

Three more from the same pack, each testing a different kind of scene:

| Action and figures | Built structure | Aerial and raking light |
|---|---|---|
| ![football](samples/Football02_oil.jpg) | ![basketball](samples/Basketball01_oil.jpg) | ![tennis](samples/Tennis02_oil.jpg) |
| Orange kit on green turf — a true complementary pair, and turf takes impasto beautifully | The flat wall was expected to be too dull to paint; it became broad palette-knife slabs and carries the picture | Clay reduced to dabbed strokes, with the shadow diagonal preserved intact |

Every source photograph and the exact prompt that produced each render are in
[`samples/`](samples/).

## Quick start

```bash
pip install -r requirements.txt
```

Try it with no keys and no spending — this prepares the sources and writes the exact
prompts it *would* send, then stops:

```bash
python -m impasto --dry-run
```

For a real run, put your photographs in `input/` and go:

```bash
python -m impasto
```

It asks for resolution, aspect ratio, lighting, whether you want a phone crop and a
watermark, then confirms before spending anything. Missing credentials are prompted for
and can be saved to `.env` (gitignored, `chmod 600`).

### Keys

| Variable | Required | What it does |
|---|---|---|
| `HF_API_KEY` / `HF_API_SECRET` | Yes | The Higgsfield repaint. Create a pair at [cloud.higgsfield.ai](https://cloud.higgsfield.ai) — issued as `ID:SECRET`. |
| `ANTHROPIC_API_KEY` | Optional | Lets Claude describe each photograph so the repaint keeps that specific scene. Without it, a generic description is used. |

Copy `.env.example` to `.env`, or just let the CLI ask.

### Options

```
--input FOLDER    where the photographs are (default: input)
--output FOLDER   where the results go (default: output)
--dry-run         prepare and build prompts without calling any paid API
--model ID        override the image-to-image model
--pan FILE        JSON map of {name: left_x} for hand-tuned 9:16 crops
```

## How it works

```
input/                      your photographs (jpg / png / webp / heic)
     │
     │  pre-crop to the target aspect ratio
     ▼
output/_prepared/           sources already at the right ratio
     │
     │  Stage 1  Claude views the photo and writes the scene sentence
     │  Stage 2  Higgsfield repaints it, image-to-image
     ▼
output/renders/             <name>_oil.png  +  <name>_prompt.txt
     │
     │  watermark and pan-and-scan
     ▼
output/Desktop_16x9/  and  output/iPhone_9x16/
```

**Stage 1 — vision to prompt.** Every prompt is two parts. Part A is one variable
sentence naming the actual scene, written per image by Claude. Part B is a fixed style
block appended verbatim from [`style_block.txt`](style_block.txt). Splitting them is what
keeps the style from drifting across a pack — only the scene sentence flexes.
[`style_block_cool.txt`](style_block_cool.txt) is the same block minus the warm-light
clause, for images that must keep a cool or blue mood.

**Stage 2 — repaint.** The prepared source is uploaded, then passed to an
image-to-image model with the assembled prompt. Results are downloaded to
`output/renders/` alongside the prompt that produced them, so a render is always
reproducible.

### Why sources are pre-cropped

Image-to-image non-uniformly scales the source to fill the requested aspect ratio, which
squishes the geometry. Feeding a source already at the target ratio leaves the model no
reshaping to do.

### A note on the model

The default is `bytedance/seedream/v4/image-to-image`, overridable with `--model` or
`IMPASTO_MODEL`. The renders in the gallery above were produced with **Nano Banana Pro**
through the Higgsfield MCP rather than this CLI, so expect the character of the paint to
differ somewhat between models. The prompt structure is what carries the style, and it
transfers.

## Costs

Measured against Higgsfield Plus credits, for the models used to build the gallery.

| Job | Config | Credits |
|---|---|---|
| Repaint, 2K | Nano Banana Pro | 2 / image |
| Repaint, 4K | Nano Banana Pro | 4 / image |
| Video, 1080p | Seedance 2.0, 7s, silent, high bitrate | 63 |
| Video, 4K | Seedance 2.0, 7s, silent, high bitrate | 154 |
| Video, cheap | Kling 3.0 pro, 5s, silent | 8.75 |

Kling is ~7× cheaper than Seedance for video but destroys the impasto texture — see
[field notes](docs/field-notes.md#video). Video is not yet wired into the CLI.

## Repo layout

```
impasto/                    the pipeline package
  cli.py                    interactive command line
  config.py                 credential resolution
  prepare.py                aspect-ratio pre-crop
  vision.py                 Stage 1 — Claude writes the scene sentence
  style.py                  prompt assembly (Part A + Part B)
  higgsfield.py             Stage 2 — upload, repaint, download
  deliverables.py           watermark and phone crop
style_block.txt             fixed Part B of the prompt (warm)
style_block_cool.txt        same, minus the warm-light clause
packs/*.pan.json            hand-tuned 9:16 pan offsets
samples/                    before/after pairs, their prompts, and the video
docs/field-notes.md         what works, what fails, and why
docs/phase-1-brief.md       the original build spec
```

`input/` and `output/` are tracked as empty folders; their contents never are.

## Status

The stills pipeline is complete and runnable end to end. Video is validated but still
driven by hand — Seedance 2.0 holds the paint texture, Kling destroys it, and 1080p at 7s
is the config that stays affordable without losing the brushwork.

## License and source material

The code, prompts and documentation are MIT licensed — see [LICENSE](LICENSE).

The **photographs are not**. Sample sources are included only to show what the pipeline
receives as input, and the rights in them belong to their original photographers. This is
a non-commercial personal project; nothing here is produced for sale.

If you run this on your own images, use photographs you took or hold rights to. Worth
knowing if you ever point it at stock: a lot of arena and event photography is licensed
*editorial use only*, which restricts commercial reuse independently of any trademark
question.
