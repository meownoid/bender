import numpy as np
from PIL import Image, ImageFilter

from bender.editor import OneToOneEditor
from bender.editors.utils import (
    float_rgb_to_image,
    float_rgb_to_uint8,
    image_to_float_rgb,
    rgb_to_luminance,
)
from bender.entity import entity
from bender.parameter import FloatParameter, IntParameter


def _build_highlight_mask(luminance: np.ndarray, threshold: float) -> np.ndarray:
    if threshold >= 1.0:
        return (luminance >= 1.0).astype(np.float32)

    scale = 1.0 / max(1.0 - threshold, 1e-6)
    return np.clip((luminance - threshold) * scale, 0.0, 1.0).astype(np.float32)


def _build_bucket_masks(luminance: np.ndarray, threshold: float, buckets: int) -> list[np.ndarray]:
    highlight = _build_highlight_mask(luminance, threshold)

    if buckets <= 1:
        return [highlight]

    if threshold >= 1.0:
        only_bright_masks = [np.zeros_like(highlight) for _ in range(buckets)]
        only_bright_masks[-1] = highlight
        return only_bright_masks

    normalized = np.clip((luminance - threshold) / max(1.0 - threshold, 1e-6), 0.0, 1.0)
    position = normalized * float(buckets - 1)
    lower = np.floor(position).astype(np.intp)
    upper = np.minimum(lower + 1, buckets - 1)

    upper_weight = (position - lower).astype(np.float32)
    lower_weight = (1.0 - upper_weight).astype(np.float32)

    bucket_masks: list[np.ndarray] = []
    for bucket_idx in range(buckets):
        bucket_weight = (lower == bucket_idx).astype(np.float32) * lower_weight + (
            upper == bucket_idx
        ).astype(np.float32) * upper_weight
        bucket_masks.append(bucket_weight * highlight)

    return bucket_masks


def _bucket_radius(bucket_idx: int, buckets: int, max_radius: float) -> float:
    if buckets <= 1:
        return max_radius

    return max_radius * float(bucket_idx + 1) / float(buckets)


@entity(
    name="bloom",
    description="Glow highlights with luminance-adaptive blur",
    parameters={
        "radius": FloatParameter(
            description="Maximum bloom blur radius in pixels",
            default=8.0,
            min_value=0.0,
            clamp=True,
        ),
        "buckets": IntParameter(
            description="Luminance bucket count (higher = better quality, lower = faster)",
            default=16,
            min_value=1,
            max_value=256,
            clamp=True,
        ),
        "threshold": FloatParameter(
            description="Highlight threshold in normalized range [0, 1]",
            default=0.7,
            min_value=0.0,
            max_value=1.0,
            clamp=True,
        ),
        "intensity": FloatParameter(
            description="Bloom intensity multiplier",
            default=0.6,
            min_value=0.0,
            max_value=5.0,
            clamp=True,
        ),
    },
)
class BloomEditor(OneToOneEditor):
    def __init__(self, radius: float, threshold: float, intensity: float, buckets: int = 4) -> None:
        self.radius = radius
        self.threshold = threshold
        self.intensity = intensity
        self.buckets = max(1, buckets)

    def _edit(self, image: Image.Image) -> Image.Image:
        if self.intensity <= 0.0 or self.radius <= 0.0:
            return image.copy()

        base = image_to_float_rgb(image)
        luminance = rgb_to_luminance(base)
        bucket_masks = _build_bucket_masks(luminance, self.threshold, self.buckets)

        glow = np.zeros_like(base, dtype=np.float32)
        bucket_count = len(bucket_masks)
        for bucket_idx, bucket_mask in enumerate(bucket_masks):
            if not np.any(bucket_mask > 0.0):
                continue

            highlights = base * bucket_mask[:, :, None]
            bucket_radius = _bucket_radius(bucket_idx, bucket_count, self.radius)

            blurred = Image.fromarray(float_rgb_to_uint8(highlights), mode="RGB").filter(
                ImageFilter.GaussianBlur(radius=bucket_radius)
            )
            glow += image_to_float_rgb(blurred)

        bloomed = np.clip(base + glow * self.intensity, 0.0, 1.0)
        return float_rgb_to_image(bloomed)
