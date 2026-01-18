import numpy as np

from bender.converters.utils import (
    lowpass,
    pad_reshape,
    rgb_to_ycbcr,
    ycbcr_to_rgb,
)


def test_pad_reshape():
    data = np.array([1, 2, 3])
    reshaped_data = pad_reshape(data, (2, 2))
    expected = np.array([[1, 2], [3, 0]])
    assert np.array_equal(reshaped_data, expected)


def test_lowpass():
    data = np.sin(2 * np.pi * 0.5 * np.linspace(0, 1, 500))
    filtered_data = lowpass(data, 0.1, 1, order=4)
    assert filtered_data.shape == data.shape


def test_rgb_to_ycbcr_and_back():
    r = np.array([0.1, 0.2, 0.3])
    g = np.array([0.4, 0.5, 0.6])
    b = np.array([0.7, 0.8, 0.9])

    y, cb, cr = rgb_to_ycbcr(r, g, b)
    r_new, g_new, b_new = ycbcr_to_rgb(y, cb, cr)

    assert np.allclose(r, r_new, atol=0.01)
    assert np.allclose(g, g_new, atol=0.01)
    assert np.allclose(b, b_new, atol=0.01)
