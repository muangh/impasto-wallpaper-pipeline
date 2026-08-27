"""Prompt assembly.

Every prompt is two parts. Part A is one variable sentence naming the actual
scene, written per image. Part B is a fixed style block appended verbatim.
Splitting them is what stops the style drifting across a pack — only the scene
sentence changes.
"""
from .config import ROOT

WARM = ROOT / "style_block.txt"
COOL = ROOT / "style_block_cool.txt"

WITH_SCENE = ("Repaint this exact photograph of {scene} as a masterful traditional "
              "oil painting on canvas, keeping every element identical.")

# Used when no vision model described the scene. Drops the naming clause
# entirely rather than substituting a vague placeholder, which reads as
# self-contradictory once the opening is filled in.
WITHOUT_SCENE = ("Repaint this exact photograph as a masterful traditional oil "
                 "painting on canvas, keeping every element identical.")


def style_block(lighting="warm"):
    """Part B. 'cool' drops the warm-light clause for scenes that must stay blue."""
    path = COOL if lighting == "cool" else WARM
    if not path.exists():
        raise FileNotFoundError(f"missing style block: {path}")
    return path.read_text().strip()


def build_prompt(scene=None, lighting="warm"):
    """Join Part A and Part B into the final prompt."""
    scene = (scene or "").strip().rstrip(".")
    opening = WITH_SCENE.format(scene=scene) if scene else WITHOUT_SCENE
    return f"{opening} {style_block(lighting)}"
