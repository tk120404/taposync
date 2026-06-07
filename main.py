import asyncio
import logging
import sys
import time
import cv2

from config import load_config, save_crop
from capture import open_camera, extract_zone_colors, draw_calibration_overlay
from tapo_client import TapoClient
from color_utils import rgb_to_hsv, is_near_black, smooth_colors, colors_changed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NUM_ZONES = 50


def list_cameras():
    print("Scanning camera indices 0–9...")
    found = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            backend = cap.getBackendName()
            cap.release()
            if ret:
                found.append((i, backend))
                print(f"  [{i}] {backend}")
    if not found:
        print("  No cameras found.")
    return found


async def run():
    config = load_config()

    logger.info("Opening camera...")
    cap = open_camera(config.camera_index)

    logger.info(f"Connecting to Tapo L920 at {config.tapo_ip}...")
    client = TapoClient(config.email, config.password, config.tapo_ip)
    await client.connect()
    await client.turn_on()

    previous_rgb = [(0, 0, 0)] * NUM_ZONES
    last_sent_rgb = [(0, 0, 0)] * NUM_ZONES
    frame_interval = 1.0 / config.fps

    logger.info(f"Starting sync loop at {config.fps} FPS (zone_mode={config.zone_mode})")

    mouse = {"drawing": False, "start": (0, 0), "rect": None}
    frame_h: int | None = None
    frame_w: int | None = None

    def mouse_callback(event, x, y, flags, param):
        nonlocal frame_h, frame_w
        if frame_h is None:
            return
        y = min(y, frame_h - 1)
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse["drawing"] = True
            mouse["start"] = (x, y)
            mouse["rect"] = None
        elif event == cv2.EVENT_MOUSEMOVE and mouse["drawing"]:
            sx, sy = mouse["start"]
            mouse["rect"] = (min(sx, x), min(sy, y), max(sx, x), max(sy, y))
        elif event == cv2.EVENT_LBUTTONUP and mouse["drawing"]:
            mouse["drawing"] = False
            sx, sy = mouse["start"]
            px1, py1 = min(sx, x), min(sy, y)
            px2, py2 = max(sx, x), max(sy, y)
            if px2 - px1 > 10 and py2 - py1 > 10:
                new_crop = (
                    max(0.0, px1 / frame_w),
                    max(0.0, py1 / frame_h),
                    min(1.0, px2 / frame_w),
                    min(1.0, py2 / frame_h),
                )
                config.crop_region = new_crop
                save_crop(new_crop)
                logger.info(f"Crop saved: {new_crop}")
            mouse["rect"] = None

    if config.calibrate:
        logger.info("Calibrate mode: drag to set TV region, press 'q' to quit")
        cv2.namedWindow("TapoSync Calibration")
        cv2.setMouseCallback("TapoSync Calibration", mouse_callback)

    try:
        while True:
            t0 = time.monotonic()

            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame — skipping")
                await asyncio.sleep(frame_interval)
                continue

            if frame_h is None:
                frame_h, frame_w = frame.shape[:2]

            zone_rgb = extract_zone_colors(frame, config.zone_mode, config.crop_region)

            # Smooth colors
            zone_rgb = smooth_colors(previous_rgb, zone_rgb, config.smoothing_factor)
            previous_rgb = zone_rgb

            if colors_changed(last_sent_rgb, zone_rgb):
                zone_hsv = []
                for r, g, b in zone_rgb:
                    if is_near_black(r, g, b):
                        zone_hsv.append((0, 0, 0))
                    else:
                        zone_hsv.append(rgb_to_hsv(r, g, b))

                await client.set_segments(zone_hsv, config.brightness_cap, int(1000 / config.fps))
                last_sent_rgb = zone_rgb

            if config.calibrate:
                display = draw_calibration_overlay(frame, zone_rgb, config.crop_region, mouse["rect"])
                cv2.imshow("TapoSync Calibration", display)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            elapsed = time.monotonic() - t0
            sleep = max(0.0, frame_interval - elapsed)
            if sleep:
                await asyncio.sleep(sleep)

    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down")
    finally:
        cap.release()
        if config.calibrate:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    if "--list-cameras" in sys.argv:
        list_cameras()
        sys.exit(0)
    asyncio.run(run())
