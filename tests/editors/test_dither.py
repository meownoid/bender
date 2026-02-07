import numpy as np
from PIL import Image

from bender.editors.dither import EGA16, GRAY16, PaletteDitherEditor


def _make_gradient_image(size: int = 6) -> Image.Image:
    x = np.linspace(0, 255, size, dtype=np.uint8)
    gradient = np.tile(x, (size, 1))
    rgb = np.stack([gradient, np.flipud(gradient), gradient.T], axis=2)
    return Image.fromarray(rgb, mode="RGB")


def _palette_colors(palette: np.ndarray) -> set[tuple[int, int, int]]:
    colors = np.clip(palette * 255.0 + 0.5, 0.0, 255.0).astype(np.uint8)
    return {tuple(color) for color in colors}


def test_dither_ega16_palette_colors():
    image = _make_gradient_image()
    editor = PaletteDitherEditor(palette="ega16")

    result = editor.edit([image])
    result_arr = np.asarray(result)

    allowed = _palette_colors(EGA16)

    assert result.mode == "RGB"
    assert result.size == image.size
    for color in result_arr.reshape(-1, 3):
        assert tuple(color) in allowed


def test_dither_gray16_palette_is_grayscale():
    image = _make_gradient_image()
    editor = PaletteDitherEditor(palette="gray16")

    result = editor.edit([image])
    result_arr = np.asarray(result)

    allowed = _palette_colors(GRAY16)

    assert result.mode == "RGB"
    assert result.size == image.size
    assert np.all(result_arr[:, :, 0] == result_arr[:, :, 1])
    assert np.all(result_arr[:, :, 1] == result_arr[:, :, 2])
    for color in result_arr.reshape(-1, 3):
        assert tuple(color) in allowed
