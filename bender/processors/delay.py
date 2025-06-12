import librosa.effects
import numpy as np

from bender.entity import entity
from bender.modulation import Modulation
from bender.parameter import (
    BoolParameter,
    FloatParameter,
    IntParameter,
    ModulationParameter,
)
from bender.processor import OneToOneProcessor
from bender.sound import Sound


@entity(
    name="delay",
    description="Delay sound",
    parameters={
        "lt": FloatParameter(
            default=0.6,
            min_value=0.0,
            clamp=True,
            description="Left delay time in seconds",
        ),
        "rt": FloatParameter(
            default=0.6,
            min_value=0.0,
            clamp=True,
            description="Right delay time in seconds",
        ),
        "pingpong": BoolParameter(
            default=False,
            description="Enable ping-pong delay",
        ),
        "feedback": FloatParameter(
            default=0.5,
            min_value=0.0,
            max_value=0.95,
            clamp=True,
            description="Feedback amount",
        ),
        "pitch": IntParameter(
            default=0,
            min_value=-48,
            max_value=48,
            clamp=True,
            description="Pitch shift amount",
        ),
        "mix": ModulationParameter(
            default=Modulation(0.5),
            min_value=0.0,
            max_value=1.0,
            description="Mix amount",
        ),
    },
)
class DelayProcessor(OneToOneProcessor):
    def __init__(
        self,
        lt: float,
        rt: float,
        pingpong: bool,
        feedback: float,
        pitch: float,
        mix: float | str | Modulation,
    ) -> None:
        self.lt = lt
        self.rt = rt
        self.pingpong = pingpong
        self.feedback = feedback
        self.pitch = pitch
        self.mix = Modulation(mix)

    def _delay(self, signal: np.ndarray, sr: int, samples: int) -> np.ndarray:
        if samples == 0:
            return signal

        # Create a delayed version of the signal
        delayed_signal = np.zeros_like(signal)
        delayed_signal[samples:] = signal[:-samples]

        # Apply pitch shifting if needed
        if self.pitch != 0:
            delayed_signal = librosa.effects.pitch_shift(
                delayed_signal,
                sr=sr,
                n_steps=self.pitch,
                bins_per_octave=12,
            )

        return delayed_signal

    def _process(self, sound: Sound) -> Sound:
        left = sound.left.copy()
        right = sound.right.copy()
        sr = sound.sample_rate

        lt_samples = int(self.lt * sr)
        rt_samples = int(self.rt * sr)

        # If there is no delay to apply
        if lt_samples == 0 and rt_samples == 0:
            return sound

        delay_left = self._delay(left, sr, lt_samples)
        delay_right = self._delay(right, sr, rt_samples)

        result_left = delay_left
        result_right = delay_right

        # Limit feedback iterations
        for _ in range(int(3 / (1.0 - self.feedback))):
            delay_left = self._delay(delay_left, sr, lt_samples) * self.feedback
            delay_right = self._delay(delay_right, sr, rt_samples) * self.feedback

            if self.pingpong:
                delay_left, delay_right = delay_right, delay_left

            result_left += delay_left
            result_right += delay_right

        # Mix the original and delayed signals
        mix_left = self.mix.like(left, sr)
        mix_right = self.mix.like(right, sr)

        out_left = (1 - mix_left) * left + mix_left * result_left
        out_right = (1 - mix_right) * right + mix_right * result_right

        return Sound(out_left, out_right, sr)
