import asyncio
import logging
from tapo import ApiClient
from tapo.requests import LightingEffect, LightingEffectType

logger = logging.getLogger(__name__)

NUM_ZONES = 50
# Segments are 1-indexed on the L920
_SEGMENTS = list(range(1, NUM_ZONES + 1))


class TapoClient:
    def __init__(self, email: str, password: str, ip: str):
        self._email = email
        self._password = password
        self._ip = ip
        self._device = None

    async def connect(self):
        try:
            client = ApiClient(self._email, self._password)
            self._device = await client.l920(self._ip)
            info = await self._device.get_device_info()
            logger.info(f"Connected to {info.nickname} at {self._ip}")
        except Exception as e:
            raise SystemExit(
                f"Tapo auth failed: {e}\n\n"
                "Tip: Use a Third-Party/Local Account password from the Tapo app,\n"
                "not your TP-Link cloud password. Generate one under:\n"
                "  Tapo app → Me → Manage Account → Third-Party Compatibility"
            )

    async def set_segments(
        self,
        zone_hsv: list[tuple[int, int, int]],
        brightness_cap: int,
        transition_ms: int = 100,
    ):
        """
        Push per-zone HSV colors to the L920 as a static lighting effect.
        Silently skips on rate-limit / transient errors.

        zone_hsv: list of 50 (hue 0-360, sat 0-100, val 0-100) tuples.
        """
        sequence = []
        for h, s, v in zone_hsv:
            v_capped = min(v, brightness_cap)
            sequence.append((h, max(s, 1) if v_capped > 0 else 0, v_capped))

        # display_colors shown in the Tapo app — just pick the first unique colors
        display_colors = list({(h, s, v) for h, s, v in sequence[:5]})[:3] or [(0, 0, 0)]

        effect = (
            LightingEffect(
                "ambilight",
                LightingEffectType.Static,
                True,
                True,
                brightness_cap,
                display_colors,
            )
            .with_sequence(sequence)
            .with_segments(_SEGMENTS)
            .with_transition(transition_ms)
        )

        try:
            await self._device.set_lighting_effect(effect)
        except Exception as e:
            logger.warning(f"Strip update skipped: {e}")

    async def turn_on(self):
        try:
            await self._device.on()
        except Exception as e:
            logger.warning(f"Could not turn on strip: {e}")

    async def turn_off(self):
        try:
            await self._device.off()
        except Exception as e:
            logger.warning(f"Could not turn off strip: {e}")
