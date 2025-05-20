from dataclasses import dataclass
from typing import Any

from PIL import Image

from bender.sound import Sound


@dataclass(frozen=True)
class ConvertedImage:
    sound: Sound
    metadata: dict[str, Any]


class Converter:
    def encode(self, image: Image.Image) -> ConvertedImage:
        raise NotImplementedError(
            f"encode is not implemented in {self.__class__.__name__}"
        )

    def decode(self, converted_image: ConvertedImage) -> Image.Image:
        raise NotImplementedError(
            f"decode is not implemented in {self.__class__.__name__}"
        )
