# TapoSync

**Turn your Tapo L920 LED strip into a real-time ambient light that reacts to whatever is on your TV.**

No subscriptions. No cloud. No Philips Hue tax. Just your laptop webcam, a Python script, and lights that actually follow your screen.

![demo](https://github.com/user-attachments/assets/placeholder)

---

## How it works

TapoSync points your laptop camera at the TV, samples 50 horizontal color zones across the screen 10 times a second, and pushes those colors to the LED strip over your local network — all with hardware-smoothed transitions so the lights feel like a natural extension of the image.

---

## What you need

- Tapo L920-5 LED strip (already on your Wi-Fi)
- Any laptop with a webcam, positioned so it can see your TV
- Python 3.11+

---

## Setup

```bash
git clone https://github.com/yourname/taposync
cd taposync
pip install -r requirements.txt
```

Create a `.env` file:

```env
TAPO_EMAIL=your@email.com
TAPO_PASSWORD=your_third_party_password
TAPO_IP=192.168.1.x
```

> **Password note:** Use your **Third-Party Compatibility** password, not your TP-Link cloud password.
> Get one in the Tapo app: **Me → Manage Account → Third-Party Compatibility**

---

## Run

```bash
python main.py
```

That's it. The strip will start reacting to your TV within seconds.

---

## Calibration (important — do this first)

Out of the box, TapoSync samples the middle 40% of the camera frame. If the colors look wrong, it means the camera isn't seeing the right part of the screen.

Run calibration mode to fix it:

```bash
python main.py --calibrate
```

A preview window opens. **Click and drag a rectangle directly over the TV screen.** The green box snaps to your selection and the color bar at the bottom updates in real time. The crop is saved automatically to `.tapo_crop` and used on every future run.

| Overlay element | Meaning |
|---|---|
| Green rectangle | The region being sampled |
| White lines | 50 zone boundaries |
| Color bar | Live dominant color per zone |

---

## Options

```bash
python main.py --fps 15 --brightness-cap 60 --smoothing-factor 0.4
```

| Flag | Default | Description |
|---|---|---|
| `--tapo-ip` | `192.168.0.41` | IP address of the L920 |
| `--camera-index` | `0` | Webcam to use (try `1` or `2` if 0 fails) |
| `--fps` | `10` | Capture and update rate |
| `--brightness-cap` | `80` | Max brightness 0–100 (lower = easier on the eyes) |
| `--smoothing-factor` | `0.7` | Blend speed — lower is slower and silkier |
| `--zone-mode` | `columns` | `columns` (50 independent zones) or `bands` (3 broad bands) |
| `--calibrate` | off | Open the live calibration window |
| `--list-cameras` | — | Print available camera indices and exit |

All flags can also be set as environment variables (uppercase, underscores, e.g. `BRIGHTNESS_CAP=60`).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Wrong colors on the strip | Run `--calibrate` and drag the box tightly over the TV screen |
| Strip flickers on static scenes | Expected — if it persists, raise the change threshold in `color_utils.py` (`threshold=8`) |
| Colors lag noticeably | Lower `--smoothing-factor` to `0.4` or `0.3` |
| Too bright | Lower `--brightness-cap` to `50` |
| `Camera not found` | Try `--camera-index 1` or run `--list-cameras` |
| `Tapo auth failed` | Use Third-Party password, not your TP-Link cloud password |
| Strip doesn't turn on | Check the device IP with the Tapo app and update `TAPO_IP` |

---

## License

MIT
