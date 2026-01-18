import librosa.effects
import numpy as np

from bender.effects import mix
from bender.entity import entity
from bender.modulation import Modulation
from bender.parameter import (
    BoolParameter,
    IntParameter,
    ModulationParameter,
)
from bender.processor import OneToOneProcessor
from bender.sound import Sound


@entity(
    name="delay",
    description="Delay sound",
    parameters={
        "lt": ModulationParameter(
            default=Modulation(0.6),
            min_value=0.0,
            description="Left delay time in seconds",
        ),
        "rt": ModulationParameter(
            default=Modulation(0.6),
            min_value=0.0,
            description="Right delay time in seconds",
        ),
        "pingpong": BoolParameter(
            default=False,
            description="Enable ping-pong delay",
        ),
        "feedback": ModulationParameter(
            default=Modulation(0.5),
            min_value=0.0,
            max_value=0.95,
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
        lt: float | str | Modulation,
        rt: float | str | Modulation,
        pingpong: bool,
        feedback: float | str | Modulation,
        pitch: float,
        mix: float | str | Modulation,
    ) -> None:
        self.lt = Modulation(lt)
        self.rt = Modulation(rt)
        self.pingpong = pingpong
        self.feedback = Modulation(feedback)
        self.pitch = pitch
        self.mix = Modulation(mix)

    @staticmethod
    def _variable_delay(signal: np.ndarray, delay_samples: np.ndarray) -> np.ndarray:
        x = np.arange(len(signal))
        sample_points = np.arange(len(signal)) - delay_samples

        # Find valid sample points (not before the start of the signal)
        valid_mask = sample_points >= 0

        # Use linear interpolation for valid sample points
        output = np.zeros_like(signal)
        output[valid_mask] = np.interp(
            sample_points[valid_mask],  # x-coordinates to interpolate at
            x,  # x-coordinates of original signal
            signal,  # y-coordinates of original signal
        )

        return output

    @staticmethod
    def _constant_delay(signal: np.ndarray, delay_samples: int) -> np.ndarray:
        if delay_samples <= 0:
            return signal

        delayed_signal = np.zeros_like(signal)
        delayed_signal[delay_samples:] = signal[:-delay_samples]

        return delayed_signal

    def _delay(
        self, signal: np.ndarray, delay_seconds: Modulation, sr: int
    ) -> np.ndarray:
        if (constant_delay := delay_seconds.constant) is not None:
            delayed_signal = self._constant_delay(signal, int(constant_delay * sr))
        else:
            delay_samples = delay_seconds.like(signal, sr) * sr
            delayed_signal = self._variable_delay(signal, delay_samples)

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

        delay_left = self._delay(left, self.lt, sr)
        delay_right = self._delay(right, self.rt, sr)

        result_left = delay_left
        result_right = delay_right

        feedback_left = self.feedback.like(delay_left)
        feedback_right = self.feedback.like(delay_right)
        feedback_max = max(feedback_left.max(), feedback_right.max())

        # Limit feedback iterations
        for _ in range(int(3 / (1.0 - feedback_max))):
            delay_left = self._delay(delay_left, self.lt, sr) * feedback_left
            delay_right = self._delay(delay_right, self.rt, sr) * feedback_right

            if self.pingpong:
                delay_left, delay_right = delay_right, delay_left

            result_left += delay_left
            result_right += delay_right

        out_left = mix(left, result_left, sr, self.mix)
        out_right = mix(right, result_right, sr, self.mix)

        return Sound(out_left, out_right, sr)
