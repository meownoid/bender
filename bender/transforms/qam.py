import librosa
import numpy as np

from bender.transforms.utils import (
    quam_encode,
    am_encode,
    rgb_to_ycbcr,
    am_decode,
    qam_decode,
    ycbcr_to_rgb,
    pad_reshape,
)
from bender.entity import entity
from bender.parameter import IntParameter
from bender.sound import Sound
from bender.transform import TransformResult, Transform

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


@entity(
    name="qam",
    description="Encodes image using QAM similar to the analog TV standard.",
    parameters={
        "carrier_frequency": IntParameter(
            description="Frequency of the carrier wave",
            default=1300,
            min_value=10,
            clamp=False,
        ),
        "sample_rate": IntParameter(
            description="Sample rate of the encoding process",
            default=7800,
            min_value=10,
            clamp=False,
        ),
    },
)
class QAMTransform(Transform):
    def __init__(self, carrier_frequency: int = 1300, sample_rate: int = 7800) -> None:
        super().__init__()

        self.carrier_frequency = carrier_frequency
        self.sample_rate = sample_rate

    def encode(self, image: Image) -> TransformResult:
        arr = np.array(image)

        metadata = {
            "shape": arr.shape[:2],
        }

        arr = arr / 255.0
        r, g, b = arr[..., 0].ravel(), arr[..., 1].ravel(), arr[..., 2].ravel()
        y, c_b, c_r = rgb_to_ycbcr(r, g, b)

        left = am_encode(y, self.carrier_frequency, self.sample_rate)
        right = quam_encode(c_b, c_r, self.carrier_frequency, self.sample_rate)

        if self.sample_rate != 48000:
            left = librosa.resample(left, orig_sr=self.sample_rate, target_sr=48000)
            right = librosa.resample(right, orig_sr=self.sample_rate, target_sr=48000)

        return TransformResult(
            sound=Sound(left=left, right=right, sample_rate=4800), metadata=metadata
        )

    def decode(self, transform_result: TransformResult) -> Image:
        left, right = transform_result.sound.left, transform_result.sound.right

        if self.sample_rate != 48000:
            left = librosa.resample(left, orig_sr=48000, target_sr=self.sample_rate)
            right = librosa.resample(right, orig_sr=48000, target_sr=self.sample_rate)

        y = am_decode(left, self.carrier_frequency, self.sample_rate)
        c_b, c_r = qam_decode(right, self.carrier_frequency, self.sample_rate)

        r, g, b = ycbcr_to_rgb(y, c_b, c_r)

        shape = transform_result.metadata["shape"]
        r = pad_reshape(r, shape)
        g = pad_reshape(g, shape)
        b = pad_reshape(b, shape)

        arr = np.stack([r, g, b], axis=2) * 255.0

        return Image.fromarray(arr.astype(np.uint8))
