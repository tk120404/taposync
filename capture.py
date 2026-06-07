import cv2
import numpy as np
from color_utils import dominant_color

NUM_ZONES = 50
BAND_NAMES = ["top", "middle", "bottom"]


def open_camera(index: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise SystemExit(f"Error: Camera at index {index} not found. Check CAMERA_INDEX setting.")
    return cap


def extract_zone_colors_columns(
    frame: np.ndarray,
    crop: tuple[float, float, float, float] = (0.0, 0.30, 1.0, 0.70),
) -> list[tuple[int, int, int]]:
    h, w, _ = frame.shape
    x1, y1 = int(w * crop[0]), int(h * crop[1])
    x2, y2 = int(w * crop[2]), int(h * crop[3])
    region = frame[y1:y2, x1:x2, :]
    rw = region.shape[1]

    slice_width = rw / NUM_ZONES
    colors = []
    for i in range(NUM_ZONES):
        sx = int(i * slice_width)
        ex = int((i + 1) * slice_width)
        slice_pixels = region[:, sx:ex, :]
        rgb_slice = slice_pixels[:, :, ::-1]
        colors.append(dominant_color(rgb_slice))
    return colors


def extract_zone_colors_bands(
    frame: np.ndarray,
    crop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
) -> list[tuple[int, int, int]]:
    h, w, _ = frame.shape
    x1, y1 = int(w * crop[0]), int(h * crop[1])
    x2, y2 = int(w * crop[2]), int(h * crop[3])
    region = frame[y1:y2, x1:x2, :]
    rh = region.shape[0]

    boundaries = [(0, rh // 3), (rh // 3, 2 * rh // 3), (2 * rh // 3, rh)]
    band_colors = []
    for rs, re in boundaries:
        band = region[rs:re, :, :]
        rgb_band = band[:, :, ::-1]
        band_colors.append(dominant_color(rgb_band))

    colors = []
    sizes = [17, 17, 16]
    for color, size in zip(band_colors, sizes):
        colors.extend([color] * size)
    return colors


def extract_zone_colors(
    frame: np.ndarray,
    zone_mode: str,
    crop: tuple[float, float, float, float] = (0.0, 0.30, 1.0, 0.70),
) -> list[tuple[int, int, int]]:
    if zone_mode == "bands":
        return extract_zone_colors_bands(frame, crop)
    return extract_zone_colors_columns(frame, crop)


def draw_calibration_overlay(
    frame: np.ndarray,
    zone_colors: list[tuple[int, int, int]],
    crop: tuple[float, float, float, float],
    drag_rect: tuple[int, int, int, int] | None = None,
) -> np.ndarray:
    overlay = frame.copy()
    h, w, _ = frame.shape
    x1, y1 = int(w * crop[0]), int(h * crop[1])
    x2, y2 = int(w * crop[2]), int(h * crop[3])
    crop_w = x2 - x1

    slice_width = crop_w / NUM_ZONES
    for i in range(1, NUM_ZONES):
        lx = x1 + int(i * slice_width)
        cv2.line(overlay, (lx, y1), (lx, y2), (255, 255, 255), 1)

    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)

    if drag_rect:
        dx1, dy1, dx2, dy2 = drag_rect
        cv2.rectangle(overlay, (dx1, dy1), (dx2, dy2), (0, 165, 255), 2)

    cv2.putText(overlay, "Drag to fit TV  |  q = quit", (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    bar_height = 30
    bar = np.zeros((bar_height, w, 3), dtype=np.uint8)
    for i, (r, g, b) in enumerate(zone_colors):
        bx1 = x1 + int(i * slice_width)
        bx2 = x1 + int((i + 1) * slice_width)
        bar[:, bx1:bx2] = [b, g, r]

    return np.vstack([overlay, bar])
