from typing import Final

import numpy as np
from PIL import Image

UINT8_MAX: Final[float] = 255.0
UINT8_INV: Final[float] = 1.0 / UINT8_MAX
LUMA_WEIGHTS: Final[np.ndarray] = np.array([0.299, 0.587, 0.114], dtype=np.float32)


def image_to_float_rgb(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"), dtype=np.float32) * UINT8_INV


def float_rgb_to_uint8(rgb: np.ndarray) -> np.ndarray:
    return np.clip(rgb * UINT8_MAX + 0.5, 0.0, UINT8_MAX).astype(np.uint8)


def float_rgb_to_image(rgb: np.ndarray) -> Image.Image:
    return Image.fromarray(float_rgb_to_uint8(rgb), mode="RGB")


def rgb_to_luminance(rgb: np.ndarray) -> np.ndarray:
    return (
        rgb[:, :, 0] * LUMA_WEIGHTS[0]
        + rgb[:, :, 1] * LUMA_WEIGHTS[1]
        + rgb[:, :, 2] * LUMA_WEIGHTS[2]
    ).astype(np.float32)
