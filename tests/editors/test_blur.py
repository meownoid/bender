import numpy as np
from PIL import Image

from bender.editors.blur import CircularBlurEditor, GaussianBlurEditor


def _make_grid(size: int = 5) -> tuple[Image.Image, np.ndarray]:
    base = (np.arange(size * size, dtype=np.int16).reshape(size, size) * 5).astype(np.uint8)
    rgb = np.stack([base, base, base], axis=2)
    return Image.fromarray(rgb, mode="RGB"), base


def _make_impulse(size: int = 7) -> Image.Image:
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    center = size // 2
    arr[center, center] = 255
    return Image.fromarray(arr, mode="RGB")


def test_circular_blur_radius_zero_returns_original():
    image, _ = _make_grid()
    editor = CircularBlurEditor(radius=0)

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), np.asarray(image))


def test_circular_blur_radius_one_center_average():
    image, base = _make_grid()
    editor = CircularBlurEditor(radius=1)

    result = editor.edit([image])
    result_arr = np.asarray(result)

    center = base.shape[0] // 2
    expected = (
        int(base[center, center])
        + int(base[center - 1, center])
        + int(base[center + 1, center])
        + int(base[center, center - 1])
        + int(base[center, center + 1])
    ) // 5

    assert result_arr[center, center, 0] == expected
    assert np.all(result_arr[center, center] == expected)


def test_gaussian_blur_radius_zero_returns_original():
    image, _ = _make_grid()
    editor = GaussianBlurEditor(radius=0.0)

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), np.asarray(image))


def test_gaussian_blur_spreads_impulse():
    image = _make_impulse()
    editor = GaussianBlurEditor(radius=1.5)

    result = editor.edit([image])

    assert not np.array_equal(np.asarray(result), np.asarray(image))
