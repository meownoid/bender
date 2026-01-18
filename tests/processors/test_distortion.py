import numpy as np

from bender.processors.distortion import DistortionProcessor
from bender.sound import Sound


def test_process_tanh():
    left = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
    right = np.array([0.0, -0.5, -1.0, -0.5, 0.0])
    sound = Sound(left, right, 44100)

    processor = DistortionProcessor(gain=2.0, kind="tanh")
    processed = processor._process(sound)

    expected_left = np.tanh(left * 2.0)
    expected_right = np.tanh(right * 2.0)

    assert np.allclose(processed.left, expected_left)
    assert np.allclose(processed.right, expected_right)
    assert processed.sample_rate == sound.sample_rate


def test_process_hard():
    left = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    right = np.array([0.0, -0.5, -1.0, -1.5, -2.0])
    sound = Sound(left, right, 44100)

    processor = DistortionProcessor(gain=1.5, kind="hard")
    processed = processor._process(sound)

    input_left = left * 1.5
    expected_left = np.clip(input_left, -1, 1)

    input_right = right * 1.5
    expected_right = np.clip(input_right, -1, 1)

    assert np.allclose(processed.left, expected_left)
    assert np.allclose(processed.right, expected_right)
    assert processed.sample_rate == sound.sample_rate


def test_process_method():
    left = np.array([0.0, 0.5, 1.0])
    right = np.array([0.0, -0.5, -1.0])
    sound = Sound(left, right, 44100, "test_sound")

    processor = DistortionProcessor(gain=2.0, kind="tanh")
    processed_sound = processor.process([sound])

    assert isinstance(processed_sound, Sound)
