from typing import Final

import numpy as np
from PIL import Image

from bender.editor import OneToOneEditor
from bender.editors.utils import (
    BlendMode,
    apply_noise_dither,
    blend,
    image_to_linear_rgb,
    linear_rgb_to_image,
)
from bender.entity import entity
from bender.parameter import ChoiceParameter, FloatParameter

_PYRAMID_LEVEL_COUNT: Final[int] = 6
_EXTRA_BLUR_START_LEVEL: Final[int] = 3
_BLUR_OFFSET_DIVISOR: Final[float] = 3.0
_BLUR_SAMPLE_WEIGHT: Final[float] = 0.25

_BLUR_OFFSETS: Final[tuple[tuple[float, float], ...]] = (
    (-1.0, -1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
    (1.0, 1.0),
)


def _resize_linear(image_data: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
    if image_data.shape[0] == target_h and image_data.shape[1] == target_w:
        return image_data.copy()

    channels = []
    for channel in range(image_data.shape[2]):
        channel_image = Image.fromarray(image_data[:, :, channel], mode="F")
        resized_channel = channel_image.resize((target_w, target_h), Image.Resampling.BILINEAR)
        channels.append(np.asarray(resized_channel, dtype=np.float32))
    return np.stack(channels, axis=2)


def _build_pyramid_levels(
    base: np.ndarray, level_count: int = _PYRAMID_LEVEL_COUNT
) -> list[np.ndarray]:
    pyramid_levels = [base]
    current = base
    for _ in range(1, level_count):
        next_h = max(1, current.shape[0] // 2)
        next_w = max(1, current.shape[1] // 2)
        pyramid_levels.append(_resize_linear(current, next_h, next_w))
        current = pyramid_levels[-1]
    return pyramid_levels


def _sample_level(
    level_image: np.ndarray, x_positions: np.ndarray, y_positions: np.ndarray
) -> np.ndarray:
    height, width = level_image.shape[:2]
    max_x = max(width - 1.0, 0.0)
    max_y = max(height - 1.0, 0.0)
    x_positions = np.clip(x_positions * width - 0.5, 0.0, max_x)
    y_positions = np.clip(y_positions * height - 0.5, 0.0, max_y)

    x0 = np.floor(x_positions).astype(np.int64)
    y0 = np.floor(y_positions).astype(np.int64)
    x1 = np.clip(x0 + 1, 0, width - 1)
    y1 = np.clip(y0 + 1, 0, height - 1)

    x_weight = (x_positions - x0).astype(np.float32)[None, :, None]
    y_weight = (y_positions - y0).astype(np.float32)[:, None, None]

    top_left = level_image[y0[:, None], x0[None, :], :]
    top_right = level_image[y0[:, None], x1[None, :], :]
    bottom_left = level_image[y1[:, None], x0[None, :], :]
    bottom_right = level_image[y1[:, None], x1[None, :], :]

    top = top_left + (top_right - top_left) * x_weight
    bottom = bottom_left + (bottom_right - bottom_left) * x_weight
    return top + (bottom - top) * y_weight


def _sum_pyramid_levels(
    pyramid_levels: list[np.ndarray],
    sample_x_positions: np.ndarray,
    sample_y_positions: np.ndarray,
) -> np.ndarray:
    height, width = pyramid_levels[0].shape[:2]
    bloom = np.zeros((height, width, 3), dtype=np.float32)

    for level_index, level_image in enumerate(pyramid_levels):
        if level_index < _EXTRA_BLUR_START_LEVEL:
            bloom += _sample_level(level_image, sample_x_positions, sample_y_positions)
            continue

        level_h, level_w = level_image.shape[:2]
        x_offset = 1.0 / (_BLUR_OFFSET_DIVISOR * level_w)
        y_offset = 1.0 / (_BLUR_OFFSET_DIVISOR * level_h)
        blur_acc = np.zeros((height, width, 3), dtype=np.float32)

        for sign_x, sign_y in _BLUR_OFFSETS:
            blur_acc += _sample_level(
                level_image,
                sample_x_positions + sign_x * x_offset,
                sample_y_positions + sign_y * y_offset,
            )
        bloom += _BLUR_SAMPLE_WEIGHT * blur_acc

    return bloom


@entity(
    name="bloom",
    description="Bloom with configurable blend mode",
    parameters={
        "factor": FloatParameter(
            description="Bloom strength",
            default=0.6,
            min_value=0.0,
            max_value=1.0,
            clamp=True,
        ),
        "blend_mode": ChoiceParameter(
            description="Blend mode",
            default=BlendMode.SCREEN.value,
            choices=[mode.value for mode in BlendMode],
        ),
    },
)
class BloomEditor(OneToOneEditor):
    def __init__(self, factor: float, blend_mode: str) -> None:
        self.factor = factor
        self.blend_mode = BlendMode(blend_mode.lower())

    def _edit(self, image: Image.Image) -> Image.Image:
        if self.factor <= 0.0:
            return image.copy()

        base = image_to_linear_rgb(image)
        sample_x_positions = (np.arange(base.shape[1], dtype=np.float32) + 0.5) / base.shape[1]
        sample_y_positions = (np.arange(base.shape[0], dtype=np.float32) + 0.5) / base.shape[0]

        pyramid_levels = _build_pyramid_levels(base)
        bloom_sum = _sum_pyramid_levels(pyramid_levels, sample_x_positions, sample_y_positions)
        bloom = bloom_sum / float(_PYRAMID_LEVEL_COUNT)

        combined = blend(
            base,
            bloom * self.factor,
            self.blend_mode,
        )
        combined = apply_noise_dither(combined)
        return linear_rgb_to_image(np.asarray(combined, dtype=np.float32))
