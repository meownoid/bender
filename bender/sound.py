import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import librosa
import numpy as np
import soundfile


@dataclass(frozen=True)
class Sound:
    left: np.ndarray
    right: np.ndarray
    sample_rate: int
    filename: str | None = None

    def __post_init__(self):
        if self.left.ndim != 1:
            raise ValueError("Left channel must be 1D")
        if self.right.ndim != 1:
            raise ValueError("Right channel must be 1D")
        if len(self.left) != len(self.right):
            raise ValueError("Left and right channels must have the same length")
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")

    def resample(self, sample_rate: int) -> "Sound":
        """
        Resample both channels to the given sample rate and return a new Sound object. If the sample rate
        is the same as the current sample rate, return the original Sound object.

        :param sample_rate: new sample rate
        :return: new Sound object with the resampled channels
        """
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

        return Sound(
            resample(self.left), resample(self.right), sample_rate, self.filename
        )

    def process(self, fn: Callable[[np.ndarray, int], np.ndarray]) -> "Sound":
        """
        Apply a function to each channel separately and return a new Sound object.

        :param fn: function to apply to both channels that takes a numpy array and sample rate as arguments
        :return: new Sound object with the processed channels
        """
        return Sound(
            fn(self.left, self.sample_rate),
            fn(self.right, self.sample_rate),
            self.sample_rate,
            self.filename,
        )

    def with_filename(self, filename: str) -> "Sound":
        """
        Set the filename of the Sound object.

        :param filename: new filename
        :return: new Sound object with the updated filename
        """
        return Sound(self.left, self.right, self.sample_rate, filename)

    def save(self, path: str | Path, bit_depth: int = 16) -> None:
        """
        Save the sound to a file.

        :param path: path to the file
        :param bit_depth: bit depth of the sound file, must be one of 8, 16, 24 or 32
        """
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

    @staticmethod
    def load(path: str | Path, sample_rate: int | None = None) -> "Sound":
        """
        Load a sound from a file.

        :param path: path to the sound file
        :param sample_rate: sample rate to resample the sound to, if None, use the original sample rate
        :return: Sound object with the loaded sound
        """
        assert sample_rate is None or sample_rate >= 0, "Sample rate must be positive"

        buffer, sr = librosa.load(path, sr=sample_rate, mono=False, dtype=np.float32)
        if buffer.ndim == 1:
            left, right = buffer, buffer
        else:
            left, right = buffer[0], buffer[1]

        return Sound(left, right, int(sr), str(path))

    def __len__(self) -> int:
        """
        Get the length of the sound in samples.

        :return: length of the sound in samples
        """
        return max(len(self.left), len(self.right))

    @property
    def duration(self) -> float:
        """
        Get the duration of the sound in seconds.

        :return: duration of the sound in seconds
        """
        return len(self) / self.sample_rate
