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
        assert self.left.shape == self.right.shape, (
            "Left and right channels must have the same shape"
        )
        assert self.sample_rate > 0, "Sample rate must be positive"

    def save(
        self, path: str | Path, sample_rate: int | None = None, bit_depth: int = 16
    ):
        assert sample_rate is None or sample_rate > 0, "Sample rate must be positive"

        if sample_rate is None:
            sample_rate = self.sample_rate

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
            path, np.vstack([self.left, self.right]).T, sample_rate, subtype=subtype
        )


def load_sound(path: str | Path, sample_rate: int | None = None) -> Sound:
    assert sample_rate is None or sample_rate >= 0, "Sample rate must be positive"

    buffer, sr = librosa.load(path, sr=sample_rate, mono=False, dtype=np.float32)
    if buffer.ndim == 1:
        left, right = buffer, buffer
    else:
        left, right = buffer[0], buffer[1]

    return Sound(left, right, sr)
