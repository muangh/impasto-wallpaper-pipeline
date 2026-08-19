# Field notes

What actually determines whether a photograph repaints well. Everything here was
learned by running the pipeline and looking at the output, not by reasoning about it in
advance — several of these rules replaced an earlier guess that turned out to be wrong.

## The core constraint

Text-to-image from a blank prompt produces smooth digital slop. Image-to-image on a real
photograph produces paint. The photograph supplies composition, proportion and light;
the model only rewrites the surface. **Always pass the source photo as the content
input.** Nothing else in this document matters if this is violated.

## Spatial frequency decides everything

This is the single best predictor of a good repaint.

**Broad, simple surfaces abstract into brushwork.** Turf, clay, sand, painted walls, a
fairway — the model has nothing fine to protect, so it converts them into strokes. These
are the surfaces that produce visible impasto.

**Fine detail is preserved instead of abstracted.** If an area is packed with small
high-contrast structure, the model tries to keep it, and the result reads as a lightly
filtered photograph rather than a painting.

The clearest demonstration is water, which does both:

- **Distant water** reduced to simple horizontal bands repaints beautifully (Golf01).
- **Close-up overhead water** filling the frame with surface texture fails — it comes
  back looking like a photo with a filter (Boat01, Boat02 in the first run).

> **Sourcing rule:** shoot the horizon, not the surface. A pack full of overhead
> drone-over-water shots will have a low keep rate.

## Dark scenes: soft vs detailed

An early rule of thumb — "dark areas are dead areas" — was **wrong**, and cost two
images that were rejected before being tried. The real distinction:

- **Dark and soft** (out-of-focus shadow, bokeh) converts cleanly to brushwork. There is
  no detail to protect, so the darkness gives the model permission to abstract.
  Basketball02 is ~60% dark bokeh and became dense impressionist crowd dabs.
- **Dark and detailed** (night architecture, city lights, fine structure in shadow)
  fails. The Blade Runner cityscape failed for exactly this reason.

Similarly, a large flat wall with little tonal variety was expected to be too dull to
take paint. Instead the model read the wall panels as an excuse for broad palette-knife
slabs, and the wall carried the picture (Basketball01).

## Signage and trademarks

**Large high-contrast signage survives the repaint — often rendered more legibly than
in the source.** Stadium hoardings came back as clean painted billboards for brands that
never licensed the work: LIDL, UEFA EUROPA LEAGUE, Coca-Cola, Toyota, and an
advertiser's phone number.

**Small incidental marks get abstracted away.** A ball's wordmark and a glove's branding
both dissolved into illegible texture.

> **Sourcing rule:** professional arena sport is advertising-saturated; aerial and
> open-air sport is clean. Tight, subject-focused framing solves the trademark problem
> as a side effect of solving the composition problem.

## Aspect ratio must be fixed before upload

Image-to-image non-uniformly scales the source to fill the requested `aspect_ratio`,
which visibly squishes geometry. Pre-crop the source to the target ratio so the model
has no reshaping to do. This is what `prepare_sources.sh` exists for.

## 4K re-runs are new paintings, not upscales

Re-running an approved 2K image at 4K produces a **fresh generation** — the model
repaints from scratch, so composition and stroke pattern differ from the version that
was signed off. Always re-review after a resolution change. Do the resolution decision
once, at the end, over the whole pack.

## Testing order

Run 2K first to measure keep rate cheaply (2 credits/image), then commit to 4K
(4 credits/image) only for the images that survive. On the first Sports run this turned a
potential 48-credit batch into 24 credits plus a 48-credit final pass, and caught five
rejects before they were paid for at full resolution.

Test across scene types before batching. Texture wobbles most on busy, architectural and
people-heavy scenes; an easy landscape proves very little.

## Video

Animating a finished painting into a subtly moving "living painting" is the phase-2
question. The trade-off found so far:

| Model | Config | Credits | Verdict |
|---|---|---|---|
| Seedance 2.0 | 4K, 7s, silent, high bitrate | 154 | Quality is right, cost is not |
| Seedance 2.0 | 1080p, 7s, silent, high bitrate | 63 | In budget; texture holds |
| Seedance 2.0 | 1080p, 5s | 45 | Cheapest config that still holds paint |
| Kling 3.0 | pro, 5s, silent | 8.75 | **Unusable** |

**Kling does not just look cheaper — it un-paints the image.** Its frames revert the
water to photographic ocean: the impasto strokes disappear and the shadows crush. Since
the paint texture *is* the product, cost per video is the wrong axis to optimise on
alone.

Seedance holds the brushwork because it treats the painted surface as content rather
than as a style to reinterpret. The prompt reinforces this by stating explicitly that
the brushstrokes and canvas texture stay intact and that only the painted water and
figures drift.

If true 4K video is required, the economics favour a 1-day unlimited plan with all video
work batched into it, rather than paying 154 credits per clip. A 1080p render followed
by a video upscale is the untested middle path.

## Sourcing checklist

Before adding a photograph to a pack:

- [ ] Broad, simple surfaces dominate the frame
- [ ] No large signage, hoardings or legible branding
- [ ] Any water is distant, not close-up overhead
- [ ] Dark areas are soft, not detailed
- [ ] Raking or directional natural light
- [ ] Complementary colour pair if possible (orange kit on green turf, green turf on
      orange dirt)
- [ ] Crops to 16:9 without losing the subject
