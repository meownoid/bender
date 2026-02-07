import numpy as np
from PIL import Image

from bender.editors.extract_channel import ExtractChannelEditor


def _make_rgb_image() -> Image.Image:
    data = np.array([[[10, 20, 30], [40, 50, 60]]], dtype=np.uint8)
    return Image.fromarray(data, mode="RGB")


def test_extract_channel_rgb_red():
    image = _make_rgb_image()
    editor = ExtractChannelEditor(mode="RGB", channel=0)

    result = editor.edit([image])
    result_arr = np.asarray(result)

    expected = np.repeat(np.asarray(image)[:, :, 0:1], 3, axis=2)

    assert result.mode == "RGB"
    assert np.array_equal(result_arr, expected)


def test_extract_channel_clamps_channel_high():
    image = _make_rgb_image()
    editor = ExtractChannelEditor(mode="RGB", channel=10)

    result = editor.edit([image])
    result_arr = np.asarray(result)

    expected = np.repeat(np.asarray(image)[:, :, 2:3], 3, axis=2)

    assert result.mode == "RGB"
    assert np.array_equal(result_arr, expected)
