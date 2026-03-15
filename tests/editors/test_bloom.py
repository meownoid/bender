import numpy as np
from PIL import Image

from bender.editors.bloom import BloomEditor


def _make_highlight_image(size: int = 7) -> tuple[Image.Image, np.ndarray]:
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    arr[:] = 16
    center = size // 2
    arr[center, center] = 255
    return Image.fromarray(arr, mode="RGB"), arr


def _make_dual_highlight_image() -> tuple[Image.Image, np.ndarray, int, int, int]:
    arr = np.zeros((17, 41, 3), dtype=np.uint8)
    arr[:] = 8
    y = arr.shape[0] // 2
    dim_x = 12
    bright_x = 28
    arr[y, dim_x] = 180
    arr[y, bright_x] = 255
    return Image.fromarray(arr, mode="RGB"), arr, y, dim_x, bright_x


def test_bloom_factor_zero_returns_original():
    image, arr = _make_highlight_image()
    editor = BloomEditor(factor=0.0, blend_mode="screen")

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), arr)


def test_bloom_spreads_bright_highlight():
    image, arr = _make_highlight_image()
    editor = BloomEditor(factor=0.6, blend_mode="screen")

    result = editor.edit([image])
    result_arr = np.asarray(result)
    center = arr.shape[0] // 2

    assert result_arr[center, center, 0] >= arr[center, center, 0]
    assert result_arr[center - 1, center, 0] >= arr[center - 1, center, 0]
    assert result_arr[center, center - 1, 0] >= arr[center, center - 1, 0]


def test_bloom_blend_modes_differ():
    image, _, y, dim_x, bright_x = _make_dual_highlight_image()
    screen_editor = BloomEditor(factor=0.8, blend_mode="screen")
    add_editor = BloomEditor(factor=0.8, blend_mode="add")

    screen_arr = np.asarray(screen_editor.edit([image]), dtype=np.int16)
    add_arr = np.asarray(add_editor.edit([image]), dtype=np.int16)

    assert add_arr[y, bright_x, 0] >= screen_arr[y, bright_x, 0]
    assert add_arr[y, dim_x, 0] >= screen_arr[y, dim_x, 0]


def test_bloom_preserves_output_shape_and_type():
    image, arr, _, _, _ = _make_dual_highlight_image()
    editor = BloomEditor(factor=1.0, blend_mode="add")
    result = np.asarray(editor.edit([image]))

    assert result.shape == arr.shape
    assert result.dtype == np.uint8
