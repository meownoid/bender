from typing import Callable

import numpy as np

from bender.entity import entity
from bender.parameter import ChoiceParameter, FloatParameter
from bender.processor import OneToOneProcessor
from bender.sound import Sound


@entity(
    name="distortion",
    description="Increase gain and add distortion to the sound",
    parameters={
        "gain": FloatParameter(
            default=1.0,
            min_value=0.0,
            max_value=10.0,
            clamp=True,
            description="Gain factor",
        ),
        "kind": ChoiceParameter(
            default="tanh",
            choices=["tanh", "hard"],
            description="Distortion type",
        ),
    },
)
class DistortionProcessor(OneToOneProcessor):
    def __init__(self, gain: float, kind: str) -> None:
        self.gain = gain
        self.kind = kind

    def get_distortion(self, kind: str) -> Callable[[np.ndarray], np.ndarray]:
        if kind == "tanh":
            return lambda x: np.tanh(x)
        elif kind == "hard":
            return lambda x: np.clip(x, -1, 1)
        else:
            raise ValueError(f"Unknown distortion kind: {kind}")

    def _process(self, sound: Sound) -> Sound:
        fn = self.get_distortion(self.kind)
        return sound.process(lambda x: fn(x * self.gain))
