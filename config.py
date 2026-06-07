import argparse
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

CROP_FILE = os.path.join(os.path.dirname(__file__), ".tapo_crop")


def load_crop() -> tuple[float, float, float, float]:
    try:
        with open(CROP_FILE) as f:
            x1, y1, x2, y2 = map(float, f.read().split())
            return (x1, y1, x2, y2)
    except (FileNotFoundError, ValueError):
        return (0.0, 0.30, 1.0, 0.70)


def save_crop(crop: tuple[float, float, float, float]) -> None:
    with open(CROP_FILE, "w") as f:
        f.write(f"{crop[0]:.4f} {crop[1]:.4f} {crop[2]:.4f} {crop[3]:.4f}\n")


@dataclass
class Config:
    email: str
    password: str
    tapo_ip: str = "192.168.0.41"
    camera_index: int = 0
    fps: int = 10
    brightness_cap: int = 80
    smoothing_factor: float = 0.7
    zone_mode: str = "columns"
    calibrate: bool = False
    crop_region: tuple[float, float, float, float] = (0.0, 0.30, 1.0, 0.70)


def load_config() -> Config:
    parser = argparse.ArgumentParser(description="TapoSync — Ambient TV light sync via webcam")
    parser.add_argument("--tapo-ip", default=os.getenv("TAPO_IP", "192.168.0.28"))
    parser.add_argument("--camera-index", type=int, default=int(os.getenv("CAMERA_INDEX", "0")))
    parser.add_argument("--fps", type=int, default=int(os.getenv("FPS", "10")))
    parser.add_argument("--brightness-cap", type=int, default=int(os.getenv("BRIGHTNESS_CAP", "80")))
    parser.add_argument("--smoothing-factor", type=float, default=float(os.getenv("SMOOTHING_FACTOR", "0.7")))
    parser.add_argument("--zone-mode", choices=["columns", "bands"], default=os.getenv("ZONE_MODE", "columns"))
    parser.add_argument("--calibrate", action="store_true", help="Show calibration overlay window")
    parser.add_argument("--list-cameras", action="store_true", help="List available camera indices and exit")
    args = parser.parse_args()

    email = os.getenv("TAPO_EMAIL")
    password = os.getenv("TAPO_PASSWORD")
    if not email or not password:
        raise SystemExit("Error: TAPO_EMAIL and TAPO_PASSWORD must be set as environment variables or in .env")

    return Config(
        email=email,
        password=password,
        tapo_ip=args.tapo_ip,
        camera_index=args.camera_index,
        fps=args.fps,
        brightness_cap=args.brightness_cap,
        smoothing_factor=args.smoothing_factor,
        zone_mode=args.zone_mode,
        calibrate=args.calibrate,
        crop_region=load_crop(),
    )
