import numpy as np
from PIL import Image

from bender.editor import OneToOneEditor
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
        arr = np.asarray(image.convert("RGB"), dtype=np.float32)
        adjusted = np.clip(arr * factor + 0.5, 0.0, 255.0).astype(np.uint8)
        return Image.fromarray(adjusted, mode="RGB")
