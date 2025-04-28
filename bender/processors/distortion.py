import numpy as np

from bender.entity import entity
from bender.parameter import FloatParameter
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
        )
    },
)
class DistortionProcessor(OneToOneProcessor):
    def __init__(self, gain: float) -> None:
        self.gain = gain

    def _tanh(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(x) * 0.5 + 0.5

    def _process(self, sound: Sound) -> Sound:
        sound = sound.process(lambda x: x * self.gain)
        sound = sound.process(self._tanh)

        return sound
