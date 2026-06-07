import colorsys
import numpy as np
from typing import Optional

NUM_ZONES = 50


def dominant_color(pixels: np.ndarray) -> tuple[int, int, int]:
    """Return the mean RGB of a pixel array as the dominant color (fast, good enough per-zone)."""
    mean = pixels.reshape(-1, 3).mean(axis=0)
    return int(mean[0]), int(mean[1]), int(mean[2])


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Convert RGB (0-255) to HSV where H=0-360, S=0-100, V=0-100."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return int(h * 360), int(s * 100), int(v * 100)


def is_near_black(r: int, g: int, b: int, threshold: int = 15) -> bool:
    _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return (v * 255) < threshold


def apply_brightness_cap(v: int, cap: int) -> int:
    """Cap brightness (V in HSV, 0-100 scale) to avoid blinding brightness."""
    return min(v, cap)


def colors_changed(
    prev: list[tuple[int, int, int]],
    curr: list[tuple[int, int, int]],
    threshold: int = 5,
) -> bool:
    """Return True if any zone shifted by more than threshold in any RGB channel."""
    for (pr, pg, pb), (cr, cg, cb) in zip(prev, curr):
        if abs(pr - cr) > threshold or abs(pg - cg) > threshold or abs(pb - cb) > threshold:
            return True
    return False


def smooth_colors(
    previous: list[tuple[int, int, int]],
    current: list[tuple[int, int, int]],
    factor: float,
) -> list[tuple[int, int, int]]:
    """Blend previous and current RGB colors: result = factor*current + (1-factor)*previous."""
    result = []
    for (pr, pg, pb), (cr, cg, cb) in zip(previous, current):
        r = int(factor * cr + (1 - factor) * pr)
        g = int(factor * cg + (1 - factor) * pg)
        b = int(factor * cb + (1 - factor) * pb)
        result.append((r, g, b))
    return result
