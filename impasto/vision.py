"""Stage 1 — look at a photograph and write the scene sentence for it.

Uses Claude vision. If no Anthropic key is configured the caller falls back to
a generic scene description, which still produces a repaint but loses the
per-image tailoring that keeps composition faithful.
"""
import base64
import mimetypes

SYSTEM = """You write one-sentence scene descriptions that will be inserted into an oil-painting repaint prompt.

Describe only what is actually visible: subjects, setting, key elements, time of day, and the direction of the light. Be concrete and specific.

Rules:
- Reply with the scene description ONLY. No preamble, no quotes, no trailing period.
- Do not mention painting, style, brushwork, canvas, or art — that is handled elsewhere.
- Do not begin with "a photograph of" or "an image of". Begin with the subject itself.
- Aim for 15-40 words.

Example: an overhead aerial view of a golf green at golden hour, two pale sand bunkers curving around the putting surface, scattered trees throwing long raking shadows"""


def describe(image_path, api_key=None, model="claude-opus-5"):
    """Return a one-sentence scene description for the image."""
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depends on install
        raise RuntimeError(
            "the anthropic SDK is not installed; run: pip install -r requirements.txt"
        ) from exc

    media_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
    if media_type not in ("image/png", "image/jpeg", "image/gif", "image/webp"):
        media_type = "image/png"

    with open(image_path, "rb") as fh:
        data = base64.standard_b64encode(fh.read()).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": media_type, "data": data}},
                {"type": "text", "text": "Describe this scene."},
            ],
        }],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()
