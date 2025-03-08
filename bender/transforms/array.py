import itertools

import numpy as np

from bender.transforms.utils import pad_reshape
from bender.entity import entity
from bender.parameter import IntParameter, BoolParameter
from bender.sound import Sound
from bender.transform import TransformResult, Transform

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


@entity(
    name="array",
    description="Interprets raw image pixel values as samples. Very similar to the BMP algorithm, but avoids artifacts caused by the BMP header.",
    parameters={
        "order": IntParameter(
            description="Ordering of axes of the image tensor",
            default=0,
            min_value=0,
            clamp=False,
        ),
        "average": BoolParameter(
            description="Average channels during decoding, otherwise use only left channel",
            default=False,
        ),
    },
)
class ArrayTransform(Transform):
    _axes_permutations = list(itertools.permutations([0, 1, 2]))

    def __init__(self, order: int = 1, average: bool = False) -> None:
        super().__init__()

        self.order = order
        self.average = average

    def _get_axes(self) -> tuple[int, ...]:
        return self._axes_permutations[self.order % len(self._axes_permutations)]

    def encode(self, image: Image) -> TransformResult:
        # scale to [-1, 1]
        arr = np.array(image).astype(np.float32) / 255.0
        arr = arr * 2.0 - 1.0

        # permute axes
        arr = arr.transpose(self._get_axes())

        # save original shape
        metadata = {"shape": arr.shape}

        # flatten
        mono = arr.reshape(-1)

        return TransformResult(
            sound=Sound(left=mono, right=mono, sample_rate=48000), metadata=metadata
        )

    def decode(self, transform_result: TransformResult) -> Image:
        shape = transform_result.metadata["shape"]

        # get mono signal
        if self.average:
            mono = (transform_result.sound.left + transform_result.sound.right) / 2.0
        else:
            mono = transform_result.sound.left

        # reshape
        arr = pad_reshape(mono, shape)

        # permute axes back
        arr = arr.transpose(np.argsort(self._get_axes()))

        # scale back to [0, 255]
        arr = (arr + 1.0) / 2.0
        arr = (arr * 255.0).astype(np.uint8)

        return Image.fromarray(arr)
