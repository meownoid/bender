import numpy as np
from PIL import Image

from bender.editor import OneToOneEditor
from bender.entity import entity
from bender.parameter import BoolParameter, FloatParameter, IntParameter


def _resize_noise(noise: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    noise_img = Image.fromarray(noise, mode="F").resize(size, resample=Image.BILINEAR)
    return np.asarray(noise_img, dtype=np.float32)


@entity(
    name="grain",
    description="Add film grain to the image",
    parameters={
        "amount": FloatParameter(
            description="Grain strength (standard deviation in normalized space)",
            default=0.15,
            min_value=0.0,
            max_value=1.0,
            clamp=True,
        ),
        "size": FloatParameter(
            description="Approximate grain size in pixels (>= 1.0)",
            default=1.0,
            min_value=1.0,
            clamp=True,
        ),
        "monochrome": BoolParameter(
            description="Use monochrome grain across channels",
            default=True,
        ),
        "seed": IntParameter(
            description="Random seed for reproducible grain",
            default=None,
        ),
    },
)
class FilmGrainEditor(OneToOneEditor):
    def __init__(self, amount: float, size: float, monochrome: bool, seed: int | None) -> None:
        self.amount = amount
        self.size = size
        self.monochrome = monochrome
        self.seed = seed

    def _edit(self, image: Image.Image) -> Image.Image:
        if self.amount <= 0.0:
            return image.copy()

        base = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
        height, width = base.shape[:2]

        rng = np.random.default_rng(self.seed)

        if self.size <= 1.0:
            if self.monochrome:
                noise = rng.standard_normal((height, width, 1), dtype=np.float32)
            else:
                noise = rng.standard_normal((height, width, 3), dtype=np.float32)
        else:
            small_h = max(1, int(round(height / self.size)))
            small_w = max(1, int(round(width / self.size)))

            if self.monochrome:
                noise_small = rng.standard_normal((small_h, small_w), dtype=np.float32)
                noise = _resize_noise(noise_small, (width, height))[:, :, None]
            else:
                channels = []
                for _ in range(3):
                    noise_small = rng.standard_normal((small_h, small_w), dtype=np.float32)
                    channels.append(_resize_noise(noise_small, (width, height)))
                noise = np.stack(channels, axis=2)

        noisy = np.clip(base + noise * self.amount, 0.0, 1.0)
        out = np.clip(noisy * 255.0 + 0.5, 0.0, 255.0).astype(np.uint8)
        return Image.fromarray(out, mode="RGB")
