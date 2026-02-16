from typing import Final

import numpy as np
from PIL import Image

from bender.editor import OneToOneEditor
from bender.editors.utils import LUMA_WEIGHTS, float_rgb_to_uint8, image_to_float_rgb
from bender.entity import entity
from bender.parameter import ChoiceParameter

BAYER16: Final[np.ndarray] = np.array(
    [
        [0, 128, 32, 160, 8, 136, 40, 168, 2, 130, 34, 162, 10, 138, 42, 170],
        [192, 64, 224, 96, 200, 72, 232, 104, 194, 66, 226, 98, 202, 74, 234, 106],
        [48, 176, 16, 144, 56, 184, 24, 152, 50, 178, 18, 146, 58, 186, 26, 154],
        [240, 112, 208, 80, 248, 120, 216, 88, 242, 114, 210, 82, 250, 122, 218, 90],
        [12, 140, 44, 172, 4, 132, 36, 164, 14, 142, 46, 174, 6, 134, 38, 166],
        [204, 76, 236, 108, 196, 68, 228, 100, 206, 78, 238, 110, 198, 70, 230, 102],
        [60, 188, 28, 156, 52, 180, 20, 148, 62, 190, 30, 158, 54, 182, 22, 150],
        [252, 124, 220, 92, 244, 116, 212, 84, 254, 126, 222, 94, 246, 118, 214, 86],
        [3, 131, 35, 163, 11, 139, 43, 171, 1, 129, 33, 161, 9, 137, 41, 169],
        [195, 67, 227, 99, 203, 75, 235, 107, 193, 65, 225, 97, 201, 73, 233, 105],
        [51, 179, 19, 147, 59, 187, 27, 155, 49, 177, 17, 145, 57, 185, 25, 153],
        [243, 115, 211, 83, 251, 123, 219, 91, 241, 113, 209, 81, 249, 121, 217, 89],
        [15, 143, 47, 175, 7, 135, 39, 167, 13, 141, 45, 173, 5, 133, 37, 165],
        [207, 79, 239, 111, 199, 71, 231, 103, 205, 77, 237, 109, 197, 69, 229, 101],
        [63, 191, 31, 159, 55, 183, 23, 151, 61, 189, 29, 157, 53, 181, 21, 149],
        [255, 127, 223, 95, 247, 119, 215, 87, 253, 125, 221, 93, 245, 117, 213, 85],
    ],
    dtype=np.uint8,
)

EGA16: Final[np.ndarray] = np.array(
    [
        (0.000, 0.000, 0.000),  # 0 Black
        (0.502, 0.000, 0.000),  # 1 Dark Red
        (0.000, 0.502, 0.000),  # 2 Dark Green
        (0.502, 0.502, 0.000),  # 3 Dark Yellow/Brown
        (0.000, 0.000, 0.502),  # 4 Dark Blue
        (0.502, 0.000, 0.502),  # 5 Dark Magenta
        (0.000, 0.502, 0.502),  # 6 Dark Cyan
        (0.753, 0.753, 0.753),  # 7 Light Gray
        (0.502, 0.502, 0.502),  # 8 Dark Gray
        (1.000, 0.000, 0.000),  # 9 Red
        (0.000, 1.000, 0.000),  # 10 Green
        (1.000, 1.000, 0.000),  # 11 Yellow
        (0.000, 0.000, 1.000),  # 12 Blue
        (1.000, 0.000, 1.000),  # 13 Magenta
        (0.000, 1.000, 1.000),  # 14 Cyan
        (1.000, 1.000, 1.000),  # 15 White
    ],
    dtype=np.float32,
)

_gray = np.linspace(0.0, 1.0, 16, dtype=np.float32)
GRAY16: Final[np.ndarray] = np.stack([_gray, _gray, _gray], axis=1)

PALETTES: Final[dict[str, np.ndarray]] = {
    "ega16": EGA16,
    "gray16": GRAY16,
}


def _apply_palette_dither(image: Image.Image, palette: np.ndarray) -> Image.Image:
    arr = image_to_float_rgb(image)
    height, width = arr.shape[:2]

    block = arr[::2, ::2]
    block = np.repeat(np.repeat(block, 2, axis=0), 2, axis=1)
    block = block[:height, :width]

    y_idx = (np.arange(height) & 15).astype(np.intp)[:, None]
    x_idx = (np.arange(width) & 15).astype(np.intp)[None, :]
    bayer = BAYER16[y_idx, x_idx].astype(np.float32) * (1.0 / 256.0)

    adjusted = np.clip(block + (bayer[..., None] - 0.5) * 0.2, 0.0, 1.0)

    diff = adjusted[:, :, None, :] - palette[None, None, :, :]
    distances = (diff * diff) * LUMA_WEIGHTS[None, None, None, :]
    distances = distances.sum(axis=3)
    best_idx = np.argmin(distances, axis=2)

    mapped = float_rgb_to_uint8(palette[best_idx])
    return Image.fromarray(mapped, mode="RGB")


@entity(
    name="dither",
    description="Bayer dither with selectable palette quantization",
    parameters={
        "palette": ChoiceParameter(
            description="Palette to quantize against",
            default="ega16",
            choices=list(PALETTES.keys()),
        )
    },
)
class PaletteDitherEditor(OneToOneEditor):
    def __init__(self, palette: str) -> None:
        self.palette = palette

    def _edit(self, image: Image.Image) -> Image.Image:
        palette = PALETTES[self.palette]
        return _apply_palette_dither(image, palette)
