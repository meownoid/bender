import functools
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import soundfile


@dataclass(frozen=True)
class Sound:
    left: np.ndarray
    right: np.ndarray
    sample_rate: int

    def __post_init__(self):
        assert self.left.ndim == 1, "Left channel must be 1D"
        assert self.right.ndim == 1, "Right channel must be 1D"
        assert len(self.left) == len(self.right), (
            "Left and right channels must have the same length"
        )
        assert self.sample_rate > 0, "Sample rate must be positive"

    def resample(self, sample_rate: int) -> "Sound":
        assert sample_rate > 0, "Sample rate must be positive"

        if sample_rate == self.sample_rate:
            return self

        resample = functools.partial(
            librosa.resample,
            orig_sr=self.sample_rate,
            target_sr=sample_rate,
            fix=False,
            scale=False,
            res_type="soxr_vhq",
        )

        return Sound(resample(self.left), resample(self.right), sample_rate)

    def save(self, path: str | Path, bit_depth: int = 16):
        match bit_depth:
            case 8:
                subtype = "PCM_S8"
            case 16:
                subtype = "PCM_16"
            case 24:
                subtype = "PCM_24"
            case 32:
                subtype = "PCM_32"
            case _:
                raise ValueError(
                    f"Unsupported bit depth: {bit_depth}, expected 8, 16, 24 or 32"
                )

        soundfile.write(
            path,
            np.vstack([self.left, self.right]).T,
            self.sample_rate,
            subtype=subtype,
        )


def load_sound(path: str | Path, sample_rate: int | None = None) -> Sound:
    assert sample_rate is None or sample_rate >= 0, "Sample rate must be positive"

    buffer, sr = librosa.load(path, sr=sample_rate, mono=False, dtype=np.float32)
    if buffer.ndim == 1:
        left, right = buffer, buffer
    else:
        left, right = buffer[0], buffer[1]

    return Sound(left, right, sr)
