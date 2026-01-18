from PIL import Image

from bender.editor import OneToOneEditor
from bender.entity import entity
from bender.parameter import ChoiceParameter, IntParameter


@entity(
    name="extract_channel",
    description="Extract a single channel from an image",
    parameters={
        "mode": ChoiceParameter(
            description="Color mode to convert the image before extracting the channel",
            default="RGB",
            choices=["RGB", "CMYK", "YCbCr", "HSV", "LAB"],
        ),
        "channel": IntParameter(
            description="Channel index to extract (0-based)",
            default=0,
            min_value=0,
            max_value=3,
            clamp=True,
        ),
    },
)
class ExtractChannelEditor(OneToOneEditor):
    def __init__(self, mode: str, channel: int):
        self.mode = mode
        self.channel = channel

    def _edit(self, image: Image.Image) -> Image.Image:
        channels = image.convert(self.mode).split()
        idx = max(0, min(self.channel, len(channels) - 1))
        # Return the selected channel converted back to RGB for consistency
        return Image.merge("RGB", (channels[idx], channels[idx], channels[idx]))
