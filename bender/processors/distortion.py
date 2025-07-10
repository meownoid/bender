from typing import Callable

import numpy as np

from bender.entity import entity
from bender.modulation import Modulation
from bender.parameter import ChoiceParameter, ModulationParameter
from bender.processor import OneToOneProcessor
from bender.sound import Sound


@entity(
    name="distortion",
    description="Increase gain and add distortion to the sound",
    parameters={
        "gain": ModulationParameter(
            default=Modulation(1.0),
            min_value=0.0,
            max_value=10.0,
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
    def __init__(self, gain: float | str | Modulation, kind: str) -> None:
        self.gain = Modulation(gain)
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
        gain = self.gain.like(sound)
        return sound.process(lambda x, _: fn(x * gain))
