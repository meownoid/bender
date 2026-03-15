import numpy as np
from PIL import Image

from bender.editor import OneToOneEditor
from bender.editors.utils import image_to_linear_rgb, linear_rgb_to_image
from bender.entity import entity
from bender.parameter import FloatParameter


@entity(
    name="exposure",
    description="Adjust image exposure in stops",
    parameters={
        "stops": FloatParameter(
            description="Exposure adjustment in stops (positive = brighter, negative = darker)",
            default=0.0,
            min_value=-5.0,
            max_value=5.0,
            clamp=True,
        ),
    },
)
class ExposureEditor(OneToOneEditor):
    def __init__(self, stops: float) -> None:
        self.stops = stops

    def _edit(self, image: Image.Image) -> Image.Image:
        if self.stops == 0.0:
            return image.copy()

        factor = 2.0**self.stops
        linear = image_to_linear_rgb(image)
        adjusted = np.clip(linear * factor, 0.0, 1.0)
        return linear_rgb_to_image(adjusted)
