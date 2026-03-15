import numpy as np
from PIL import Image

from bender.editors.utils import apply_noise_dither, image_to_linear_rgb, linear_rgb_to_image


def test_linear_rgb_roundtrip_is_near_identity():
    rng = np.random.default_rng(123)
    arr = rng.integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
    image = Image.fromarray(arr, mode="RGB")

    linear = image_to_linear_rgb(image)
    rebuilt = np.asarray(linear_rgb_to_image(linear), dtype=np.int16)
    original = arr.astype(np.int16)

    assert np.max(np.abs(rebuilt - original)) <= 6


def test_image_to_linear_rgb_is_monotonic_on_gray_ramp():
    ramp = np.arange(256, dtype=np.uint8)
    arr = np.stack([ramp, ramp, ramp], axis=1)[None, :, :]
    image = Image.fromarray(arr, mode="RGB")

    linear = image_to_linear_rgb(image)[0, :, 0]

    assert np.all(np.diff(linear) >= 0.0)
    assert linear[0] == 0.0
    assert 0.2 < float(linear[128]) < 0.23


def test_linear_rgb_to_image_sanitizes_non_finite_values():
    linear = np.array(
        [[[np.nan, np.inf, -np.inf], [1.5, -0.5, 0.5]]],
        dtype=np.float32,
    )

    out = np.asarray(linear_rgb_to_image(linear))

    assert out.dtype == np.uint8
    assert out.shape == (1, 2, 3)
    assert np.array_equal(out[0, 0], np.array([0, 0, 0], dtype=np.uint8))
    assert out[0, 1, 0] == 255
    assert out[0, 1, 1] == 0


def test_apply_noise_dither_uses_stable_uniform_noise():
    linear = np.zeros((4, 5, 3), dtype=np.float32)

    first = apply_noise_dither(linear)
    second = apply_noise_dither(linear)

    assert first.shape == linear.shape
    assert first.dtype == np.float32
    assert np.array_equal(first, second)
    assert np.all(first[:, :, 0] == first[:, :, 1])
    assert np.all(first[:, :, 1] == first[:, :, 2])
    assert np.max(np.abs(first)) <= (0.5 / 255.0)
