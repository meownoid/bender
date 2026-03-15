import numpy as np
from PIL import Image

from bender.editors.grain import FilmGrainEditor
from bender.editors.utils import image_to_linear_rgb, linear_rgb_to_image


def _make_image() -> tuple[Image.Image, np.ndarray]:
    arr = np.array(
        [
            [[10, 20, 30], [100, 150, 200], [42, 42, 42]],
            [[0, 1, 2], [250, 255, 128], [80, 90, 100]],
        ],
        dtype=np.uint8,
    )
    return Image.fromarray(arr, mode="RGB"), arr


def _apply_reference(
    arr: np.ndarray, amount: float, size: float, monochrome: bool, seed: int | None
) -> np.ndarray:
    base = image_to_linear_rgb(Image.fromarray(arr, mode="RGB"))
    height, width = base.shape[:2]
    rng = np.random.default_rng(seed)

    if size <= 1.0:
        if monochrome:
            noise = rng.standard_normal((height, width, 1), dtype=np.float32)
        else:
            noise = rng.standard_normal((height, width, 3), dtype=np.float32)
    else:
        small_h = max(1, int(round(height / size)))
        small_w = max(1, int(round(width / size)))

        if monochrome:
            noise_small = rng.standard_normal((small_h, small_w), dtype=np.float32)
            noise_img = Image.fromarray(noise_small, mode="F").resize(
                (width, height), resample=Image.BILINEAR
            )
            noise = np.asarray(noise_img, dtype=np.float32)[:, :, None]
        else:
            channels = []
            for _ in range(3):
                noise_small = rng.standard_normal((small_h, small_w), dtype=np.float32)
                noise_img = Image.fromarray(noise_small, mode="F").resize(
                    (width, height), resample=Image.BILINEAR
                )
                channels.append(np.asarray(noise_img, dtype=np.float32))
            noise = np.stack(channels, axis=2)

    noisy = np.clip(base + noise * amount, 0.0, 1.0)
    return np.asarray(linear_rgb_to_image(noisy))


def test_film_grain_zero_returns_original():
    image, arr = _make_image()
    editor = FilmGrainEditor(amount=0.0, size=1.0, monochrome=True, seed=123)

    result = editor.edit([image])

    assert np.array_equal(np.asarray(result), arr)


def test_film_grain_seeded_monochrome():
    image, arr = _make_image()
    editor = FilmGrainEditor(amount=0.2, size=1.0, monochrome=True, seed=42)

    result = editor.edit([image])

    expected = _apply_reference(arr, amount=0.2, size=1.0, monochrome=True, seed=42)
    assert np.array_equal(np.asarray(result), expected)


def test_film_grain_seeded_color_and_scaled():
    image, arr = _make_image()
    editor = FilmGrainEditor(amount=0.1, size=2.5, monochrome=False, seed=7)

    result = editor.edit([image])

    expected = _apply_reference(arr, amount=0.1, size=2.5, monochrome=False, seed=7)
    assert np.array_equal(np.asarray(result), expected)
