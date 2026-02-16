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


def test_bloom_intensity_zero_returns_original():
    image, arr = _make_highlight_image()
    editor = BloomEditor(radius=3.0, threshold=0.6, intensity=0.0)

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), arr)


def test_bloom_radius_zero_returns_original():
    image, arr = _make_highlight_image()
    editor = BloomEditor(radius=0.0, threshold=0.6, intensity=1.0)

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), arr)


def test_bloom_spreads_bright_highlight():
    image, arr = _make_highlight_image()
    editor = BloomEditor(radius=1.8, threshold=0.8, intensity=1.2)

    result = editor.edit([image])
    result_arr = np.asarray(result)
    center = arr.shape[0] // 2

    assert result_arr[center, center, 0] >= arr[center, center, 0]
    assert result_arr[center - 1, center, 0] > arr[center - 1, center, 0]
    assert result_arr[center, center - 1, 0] > arr[center, center - 1, 0]
    assert result_arr.shape == arr.shape


def test_bloom_brighter_highlights_spread_farther():
    image, arr, y, dim_x, bright_x = _make_dual_highlight_image()
    editor = BloomEditor(radius=8.0, threshold=0.6, intensity=1.0, buckets=6)

    result = editor.edit([image])
    result_arr = np.asarray(result)

    offset = 6
    dim_far = result_arr[y, dim_x - offset, 0]
    bright_far = result_arr[y, bright_x + offset, 0]

    assert bright_far > dim_far
    assert bright_far > arr[y, bright_x + offset, 0]


def test_bloom_bucket_count_changes_result():
    image, _, _, _, _ = _make_dual_highlight_image()

    low_quality = BloomEditor(radius=8.0, threshold=0.6, intensity=1.0, buckets=1)
    high_quality = BloomEditor(radius=8.0, threshold=0.6, intensity=1.0, buckets=6)

    low_result = np.asarray(low_quality.edit([image]))
    high_result = np.asarray(high_quality.edit([image]))

    assert not np.array_equal(low_result, high_result)


def test_bloom_threshold_one_still_uses_large_radius():
    image, arr = _make_highlight_image(size=25)
    editor = BloomEditor(radius=8.0, threshold=1.0, intensity=1.0, buckets=8)

    result = editor.edit([image])
    result_arr = np.asarray(result)
    center = arr.shape[0] // 2

    assert result_arr[center, center + 6, 0] > arr[center, center + 6, 0]
