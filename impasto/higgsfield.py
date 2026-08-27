"""Stage 2 — the Higgsfield repaint.

Thin wrapper over the official `higgsfield-client` SDK: upload the prepared
source, submit an image-to-image request with the assembled prompt, wait for
the asynchronous job, and download the result.
"""
import urllib.request
from pathlib import Path


class HiggsfieldError(RuntimeError):
    pass


def _client():
    try:
        import higgsfield_client
    except ImportError as exc:  # pragma: no cover - depends on install
        raise HiggsfieldError(
            "higgsfield-client is not installed. Run: pip install -r requirements.txt"
        ) from exc
    return higgsfield_client


def upload(image_path):
    """Upload a local image and return the URL the model will read it from."""
    return _client().upload_file(str(image_path))


def _extract_url(result):
    """Pull the output image URL out of the SDK result.

    The SDK returns a dict whose exact shape varies by model, so probe the
    documented key first and fall back to a shallow search rather than crashing
    on an unfamiliar response.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        images = result.get("images") or result.get("image") or []
        if isinstance(images, dict):
            images = [images]
        for entry in images:
            if isinstance(entry, dict) and entry.get("url"):
                return entry["url"]
            if isinstance(entry, str):
                return entry
        for key in ("url", "output_url", "public_url"):
            if isinstance(result.get(key), str):
                return result[key]
    raise HiggsfieldError(f"could not find an image URL in the response: {result!r}")


def repaint(image_path, prompt, model, resolution="2K", aspect_ratio=None):
    """Run one image-to-image repaint. Returns the output image URL."""
    hf = _client()
    source_url = upload(image_path)

    arguments = {"image_url": source_url, "prompt": prompt, "resolution": resolution}
    if aspect_ratio:
        arguments["aspect_ratio"] = aspect_ratio

    try:
        result = hf.subscribe(model, arguments=arguments)
    except Exception as exc:
        raise HiggsfieldError(f"generation failed: {exc}") from exc

    return _extract_url(result)


def download(url, dest):
    """Fetch a generated image to disk."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, open(dest, "wb") as fh:
        fh.write(response.read())
    return dest
