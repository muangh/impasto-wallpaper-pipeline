# Oil-Paint Wallpaper Pipeline — PHASE 1 Build Spec (Higgsfield MCP version)

Paste this into a fresh Claude Code session. Scope is deliberately narrow: **folder of photos → per-image prompt → repainted oil-paint stills in an output folder.** No video, no upscaling, no ratio variants. Build ONLY this.

This version uses the **Higgsfield MCP** for the repaint — NOT a separate image API. Reuses the exact model already validated (Nano Banana Pro) and existing Higgsfield Plus credits. No Gemini/Flux key, no new billing.

---

## Goal

```
/input      ← my own photos (jpg/png/heic)
     │
     ▼  Stage 1: Claude Code agent reads each photo (native vision), writes a tailored repaint prompt
     ▼  Stage 2: Higgsfield MCP repaints photo (image-to-image, Nano Banana Pro) using that prompt
     ▼
/processed  ← <originalname>_oil.png
```

Folder in, folder out. As unattended as the MCP upload path allows (see linchpin note).

## Why this method (do not skip)

Text-to-image from a blank prompt = smooth digital slop. Validated method is **image-to-image on a real photo**: the photo supplies composition/proportions/light; the model only repaints the surface into oil. Confirmed working on a landscape photo with Nano Banana Pro via Higgsfield. Always pass the source photo as the content input.

## Architecture — no external APIs

- **Stage 1 vision → prompt:** the Claude Code agent does this ITSELF. It can open each image from disk and write the prompt. No Anthropic API key, no separate vision call.
- **Stage 2 repaint:** call the **Higgsfield MCP** `generate_image` tool, model `nano_banana_pro`, with the source image as the image-to-image input. Same model that produced the approved result. Spends Higgsfield Plus credits.

## ⚠️ LINCHPIN — confirm the headless upload path first

Higgsfield MCP tools cannot read arbitrary local paths directly; media must be uploaded to Higgsfield first. There are two upload paths:
- **Widget (`media_upload_widget`)** — a UI file picker, human-in-the-loop. NOT suitable for an unattended folder loop.
- **Scriptable (`media_upload` → PUT bytes → `media_confirm`)** — programmatic. `media_upload` returns a presigned upload URL; PUT the local file's bytes to it; `media_confirm` registers it and returns a `media_id`. Feed that `media_id` into `generate_image`.

**FIRST STEP in the session: confirm `media_upload` and `media_confirm` are exposed in this Code session's Higgsfield MCP.** If yes → fully headless per-image upload. If only the widget is available → semi-manual (upload each by hand; pipeline still works, just less automated).

## Per-image loop (what the agent does)

For each image in `/input`:
1. (if HEIC) convert to PNG/JPG.
2. Agent views the image, writes the tailored prompt: PART A (variable scene description) + PART B (fixed style block, verbatim).
3. Upload to Higgsfield: `media_upload` → PUT bytes → `media_confirm` → `media_id`.
4. `generate_image` (model `nano_banana_pro`, `medias: [{role:"image", value: media_id}]`, `aspect_ratio` matching the source, prompt = tailored prompt).
5. Download the result, save to `/processed/<name>_oil.png`.
6. Write a sidecar `<name>_prompt.txt` (the prompt used) for tuning.
Add: skip already-processed files, retry once on error, print progress.

## The prompt — two parts

**PART A — VARIABLE (agent writes, ~1 sentence naming the real scene):**
`"Repaint this exact photograph of [accurate scene: subjects, setting, key elements, time of day] as a masterful traditional oil painting on canvas, keeping every element identical..."`

**PART B — FIXED (appended verbatim, never changes):**

> ...Only transform the surface into thick hand-applied oil paint. Uniform small directional impasto dabs across every surface, comma-shaped palette-knife strokes, each stroke a slightly different value sitting side by side like overlapping scales. Chunky ridged paint with visible bristle marks, short dabbed strokes catching light on the raised ridges, softly blended alla prima passages in open areas like sky or water. Visible woven linen canvas texture showing through the thinner passages. Warm raking natural light, rich saturated complementary color, deep luminous shadows, glowing highlights on the paint ridges, high contrast, cinematic aspirational gallery-quality mood in the style of American impressionist plein-air oil painting. The scene stays photographically real in composition but every surface is unmistakably physical oil paint, tactile and dimensional. Ultra detailed, sharp, no text, no watermark, no signature. NOT a 3D render, NOT digital, NOT smooth, NOT glossy, NOT CGI, NOT airbrushed — authentic thick oil on canvas.

Split guarantees the style never drifts — only the scene sentence flexes. Store PART B in `style_block.txt`, load and append every time.

**Lighting lever:** PART B warms images toward golden hour (part of the premium look). If a photo must keep a cool/blue mood, the agent drops the "Warm raking natural light" clause for that image.

## Tradeoff to accept

An MCP agent loop calls tools one image at a time — slower and more token-heavy than a tight API script, but fine at pack scale (20–40). If you ever need 500+ unattended overnight, switch Stage 2 to a direct image API then. Not now.

## Test before batching

Run on **3 different scene types first** — open landscape, architecture, and something with a person — before a full pack. The validated image was an easy landscape; texture wobbles most on busy/architectural/people scenes. Confirm all 3, then batch.

## Explicitly OUT of scope for Phase 1

No video/motion, no upscaling, no 4K, no ratio/matched-set variants, no store integration. Later phases.

## Licensing

Own photos, licensed stock, or AI-generated bases only. (Higgsfield/Nano Banana commercial terms already in use via Plus — verify current terms.)

---

*Context: method validated end-to-end in a prior Claude chat (photo → oil-paint still via Higgsfield Nano Banana Pro = perfect). This phase converts the manual one-at-a-time chat workflow into an automated folder-in/folder-out stills pipeline, reusing the Higgsfield MCP instead of standing up a new image API.*
