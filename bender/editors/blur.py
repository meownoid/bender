import numpy as np
from PIL import Image, ImageFilter

from bender.editor import OneToOneEditor
from bender.editors.utils import (
    float_rgb_to_image,
    image_to_float_rgb,
    image_to_linear_rgb,
    linear_rgb_to_image,
)
from bender.entity import entity
from bender.parameter import FloatParameter, IntParameter


def _disk_kernel(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    mask = (x * x + y * y) <= radius * radius
    kernel = mask.astype(np.float32)
    kernel_sum = float(kernel.sum())
    if kernel_sum == 0:
        kernel[radius, radius] = 1.0
        kernel_sum = 1.0
    kernel /= kernel_sum
    return kernel


def _convolve_fft(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    pad = kernel.shape[0] // 2
    padded = np.pad(image, ((pad, pad), (pad, pad), (0, 0)), mode="edge")

    out_shape = (
        padded.shape[0] + kernel.shape[0] - 1,
        padded.shape[1] + kernel.shape[1] - 1,
    )
    kernel_fft = np.fft.rfftn(kernel, out_shape)

    result = np.empty_like(padded, dtype=np.float32)
    start_y = kernel.shape[0] // 2
    start_x = kernel.shape[1] // 2

    for channel in range(padded.shape[2]):
        image_fft = np.fft.rfftn(padded[:, :, channel], out_shape)
        conv = np.fft.irfftn(image_fft * kernel_fft, out_shape)
        conv = conv[start_y : start_y + padded.shape[0], start_x : start_x + padded.shape[1]]
        result[:, :, channel] = conv.astype(np.float32)

    return result[pad : pad + image.shape[0], pad : pad + image.shape[1]]


@entity(
    name="blur-c",
    description="Box blur with circular support",
    parameters={
        "radius": IntParameter(
            description="Blur radius in pixels",
            default=2,
            min_value=0,
            clamp=True,
        ),
    },
)
class CircularBlurEditor(OneToOneEditor):
    def __init__(self, radius: int) -> None:
        self.radius = radius

    def _edit(self, image: Image.Image) -> Image.Image:
        if self.radius <= 0:
            return image.copy()
        radius = int(self.radius)
        kernel = _disk_kernel(radius)
        linear = image_to_linear_rgb(image)
        blurred = _convolve_fft(linear, kernel)
        return linear_rgb_to_image(blurred)


@entity(
    name="blur-g",
    description="Gaussian blur",
    parameters={
        "radius": FloatParameter(
            description="Gaussian blur radius",
            default=1.5,
            min_value=0.0,
            clamp=True,
        ),
    },
)
class GaussianBlurEditor(OneToOneEditor):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def _edit(self, image: Image.Image) -> Image.Image:
        if self.radius <= 0:
            return image.copy()

        linear_image = float_rgb_to_image(image_to_linear_rgb(image))
        blurred_linear = linear_image.filter(ImageFilter.GaussianBlur(radius=self.radius))
        return linear_rgb_to_image(image_to_float_rgb(blurred_linear))
