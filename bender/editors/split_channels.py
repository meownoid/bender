import os

from PIL import Image

from bender.editor import OneToManyEditor
from bender.entity import entity
from bender.parameter import ChoiceParameter


@entity(
    name="split_channels",
    description="Split image into its channels",
    parameters={
        "mode": ChoiceParameter(
            description="Color mode to split the image into channels",
            default="RGB",
            choices=["RGB", "CMYK", "YCbCr", "HSV", "LAB"],
        ),
    },
)
class SplitChannelsEditor(OneToManyEditor):
    def __init__(self, mode: str):
        self.mode = mode

    def _edit(self, image: Image.Image) -> list[Image.Image]:
        filename = os.path.splitext(os.path.basename(image.filename))[0]
        result = image.convert(self.mode).split()

        for i, channel in enumerate(result):
            channel.filename = f"{filename}_{self.mode}_{i}.jpg"

        return result
