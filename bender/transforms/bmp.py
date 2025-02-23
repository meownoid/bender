import base64
import io
import numpy as np

from bender.entity import entity
from bender.parameter import IntParameter
from bender.sound import Sound
from bender.transform import ImageSound, Transform

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


DTYPES = {
    1: np.uint8,
    2: np.uint16,
    3: np.uint32,
    4: np.uint64,
}


@entity(
    name="bmp",
    description="Interprets raw BMP bytes as samples",
    parameters={
        "header_size": IntParameter(
            default=54, min_value=0, description="Size of header in bytes to preserve"
        ),
        "sample_size": IntParameter(
            default=1,
            min_value=1,
            max_value=4,
            description="Number of bytes per sample",
        ),
    },
)
class BMPTransform(Transform):
    def __init__(self, header_size: int = 54, sample_size: int = 1) -> None:
        super().__init__()

        self.header_size = header_size
        self.sample_size = sample_size

    def encode(self, image: Image) -> ImageSound:
        try:
            dtype = DTYPES[self.sample_size]
        except LookupError:
            raise ValueError(f"Unsupported sample size: {self.sample_size}")

        with io.BytesIO() as fd:
            image.save(fd, format="BMP")
            fd.seek(0)
            buffer = np.frombuffer(fd.read(), dtype=np.uint8).copy()

        # save header to attach it during decoding
        metadata = {
            "header": base64.b64encode(buffer[: self.header_size]).decode("utf-8"),
        }

        # raw BMP dwords
        mono = buffer[self.header_size :].view(dtype)
        # scale to [0, 1]
        mono = mono.astype(np.float64) / np.iinfo(dtype).max
        # scale to [-1, 1]
        mono = mono * 2.0 - 1.0

        return ImageSound(
            sound=Sound(left=mono, right=mono, sample_rate=48000), metadata=metadata
        )

    def decode(self, image_sound: ImageSound) -> Image:
        try:
            dtype = DTYPES[self.sample_size]
        except LookupError:
            raise ValueError(f"Unsupported sample size: {self.sample_size}")

        header = np.frombuffer(
            base64.b64decode(image_sound.metadata["header"].encode("utf-8")),
            dtype=np.uint8,
        ).copy()

        mono = image_sound.sound.left
        # scale to [0, 1]
        mono = (mono + 1.0) / 2.0
        # convert to raw BMP dwords
        mono = (mono * np.iinfo(dtype).max).astype(dtype)

        buffer = np.concatenate([header, mono.view(np.uint8)]).tobytes()

        with io.BytesIO(buffer) as fd:
            with Image.open(fd, formats=["BMP"]) as image:
                return image.copy()
