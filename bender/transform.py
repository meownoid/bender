from dataclasses import dataclass
from typing import Any
from PIL import Image

from bender.sound import Sound


@dataclass(frozen=True)
class TransformResult:
    sound: Sound
    metadata: dict[str, Any]


class Transform:
    def encode(self, image: Image.Image) -> TransformResult:
        raise NotImplementedError(
            f"encode is not implemented in {self.__class__.__name__}"
        )

    def decode(self, image_sound: TransformResult) -> Image:
        raise NotImplementedError(
            f"decode is not implemented in {self.__class__.__name__}"
        )
