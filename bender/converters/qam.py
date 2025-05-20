import numpy as np
from PIL import Image, ImageFile

from bender.converter import ConvertedImage, Converter
from bender.converters.utils import (
    am_decode,
    am_encode,
    pad_reshape,
    qam_decode,
    qam_encode,
    rgb_to_ycbcr,
    ycbcr_to_rgb,
)
from bender.entity import entity
from bender.parameter import IntParameter
from bender.sound import Sound

ImageFile.LOAD_TRUNCATED_IMAGES = True


@entity(
    name="qam",
    description="Encodes image using QAM similar to the analog TV standard.",
    parameters={
        "carrier_frequency": IntParameter(
            description="Frequency of the carrier wave",
            default=1300,
            min_value=1,
        ),
        "sample_rate": IntParameter(
            description="Sample rate of the encoding process, must be greater than twice the carrier frequency",
            default=7800,
            min_value=3,
        ),
    },
)
class QAMConverter(Converter):
    def __init__(self, carrier_frequency: int = 1300, sample_rate: int = 7800) -> None:
        super().__init__()

        if carrier_frequency >= sample_rate / 2:
            raise ValueError(
                "Carrier frequency must be less than half of the sample rate"
            )

        self.carrier_frequency = carrier_frequency
        self.sample_rate = sample_rate

    def encode(self, image: Image.Image) -> ConvertedImage:
        arr = np.array(image)

        metadata = {
            "shape": arr.shape[:2],
        }

        arr = arr / 255.0
        r, g, b = arr[..., 0].ravel(), arr[..., 1].ravel(), arr[..., 2].ravel()
        y, c_b, c_r = rgb_to_ycbcr(r, g, b)

        left = am_encode(y, self.carrier_frequency, self.sample_rate)
        right = qam_encode(c_b, c_r, self.carrier_frequency, self.sample_rate)

        # Bring left channel down to be closer to right channel
        left /= 2.0

        return ConvertedImage(
            sound=Sound(left=left, right=right, sample_rate=self.sample_rate),
            metadata=metadata,
        )

    def decode(self, converted_image: ConvertedImage) -> Image.Image:
        sound = converted_image.sound.resample(self.sample_rate)

        y = am_decode(sound.left * 2.0, self.carrier_frequency, self.sample_rate)
        c_b, c_r = qam_decode(sound.right, self.carrier_frequency, self.sample_rate)

        r, g, b = ycbcr_to_rgb(y, c_b, c_r)

        shape = converted_image.metadata["shape"]
        r = pad_reshape(r, shape)
        g = pad_reshape(g, shape)
        b = pad_reshape(b, shape)

        arr = np.stack([r, g, b], axis=2) * 255.0

        return Image.fromarray(arr.astype(np.uint8))
