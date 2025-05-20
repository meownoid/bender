import base64
import io

import numpy as np
from PIL import Image, ImageFile

from bender.converter import ConvertedImage, Converter
from bender.entity import entity
from bender.parameter import BoolParameter, IntParameter
from bender.sound import Sound

ImageFile.LOAD_TRUNCATED_IMAGES = True


DTYPES: dict[int, np.dtype] = {
    1: np.dtype(np.uint8),
    2: np.dtype(np.uint16),
    3: np.dtype(np.uint32),
    4: np.dtype(np.uint64),
}


@entity(
    name="bmp",
    description="Interprets raw BMP bytes as samples",
    parameters={
        "header_size": IntParameter(
            description="Size of header in bytes to preserve", default=54, min_value=0
        ),
        "sample_size": IntParameter(
            description="Number of bytes per sample",
            default=1,
            min_value=1,
            max_value=4,
        ),
        "average": BoolParameter(
            description="Average channels during decoding, otherwise use only left channel",
        ),
    },
)
class BMPConverter(Converter):
    def __init__(
        self, header_size: int = 54, sample_size: int = 1, average: bool = False
    ) -> None:
        super().__init__()

        self.header_size = header_size
        self.sample_size = sample_size
        self.average = average

        try:
            self.dtype = DTYPES[sample_size]
        except LookupError:
            raise ValueError(f"Unsupported sample size: {sample_size}")

    def encode(self, image: Image.Image) -> ConvertedImage:
        with io.BytesIO() as fd:
            image.save(fd, format="BMP")
            fd.seek(0)
            buffer = np.frombuffer(fd.read(), dtype=np.uint8).copy()

        # save header to attach it during decoding
        metadata = {
            "header": base64.b64encode(buffer[: self.header_size]).decode("utf-8"),
        }

        # raw BMP dwords
        mono = buffer[self.header_size :].view(self.dtype)
        # scale to [0, 1]
        mono = mono.astype(np.float64) / np.iinfo(self.dtype).max
        # scale to [-1, 1]
        mono = mono * 2.0 - 1.0

        return ConvertedImage(
            sound=Sound(left=mono, right=mono, sample_rate=48000), metadata=metadata
        )

    def decode(self, converted_image: ConvertedImage) -> Image.Image:
        header = np.frombuffer(
            base64.b64decode(converted_image.metadata["header"].encode("utf-8")),
            dtype=np.uint8,
        ).copy()

        # get mono signal
        if self.average:
            mono = (converted_image.sound.left + converted_image.sound.right) / 2.0
        else:
            mono = converted_image.sound.left

        # scale to [0, 1]
        mono = (mono + 1.0) / 2.0
        # convert to raw BMP dwords
        mono = (mono * np.iinfo(self.dtype).max).astype(self.dtype)

        buffer = np.concatenate([header, mono.view(np.uint8)]).tobytes()

        with io.BytesIO(buffer) as fd:
            with Image.open(fd, formats=["BMP"]) as image:
                return image.copy()
