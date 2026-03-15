import numpy as np
from PIL import Image

from bender.editors.exposure import ExposureEditor
from bender.editors.utils import image_to_linear_rgb, linear_rgb_to_image


def _make_image() -> tuple[Image.Image, np.ndarray]:
    arr = np.array(
        [
            [[10, 20, 30], [100, 150, 200]],
            [[0, 1, 2], [250, 255, 128]],
        ],
        dtype=np.uint8,
    )
    return Image.fromarray(arr, mode="RGB"), arr


def test_exposure_zero_returns_original():
    image, arr = _make_image()
    editor = ExposureEditor(stops=0.0)

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), arr)


def test_exposure_increase_clips():
    image, arr = _make_image()
    editor = ExposureEditor(stops=1.0)

    result = editor.edit([image])

    linear = image_to_linear_rgb(image)
    expected = np.asarray(linear_rgb_to_image(np.clip(linear * 2.0, 0.0, 1.0)))
    assert np.array_equal(np.asarray(result), expected)


def test_exposure_decrease():
    image, arr = _make_image()
    editor = ExposureEditor(stops=-1.0)

    result = editor.edit([image])

    linear = image_to_linear_rgb(image)
    expected = np.asarray(linear_rgb_to_image(np.clip(linear * 0.5, 0.0, 1.0)))
    assert np.array_equal(np.asarray(result), expected)
