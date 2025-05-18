import numpy as np
import pytest

from bender.processors.distortion import DistortionProcessor
from bender.sound import Sound


def test_distortion_initialization():
    processor = DistortionProcessor(gain=1.0, kind="tanh")
    assert processor.gain == 1.0
    assert processor.kind == "tanh"

    # Test with custom values
    processor = DistortionProcessor(gain=5.0, kind="hard")
    assert processor.gain == 5.0
    assert processor.kind == "hard"


def test_tanh_distortion():
    processor = DistortionProcessor(gain=1.0, kind="tanh")

    input_values = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    expected_output = np.tanh(input_values) * 0.5 + 0.5

    output_values = processor.tanh(input_values)

    assert np.allclose(output_values, expected_output)


def test_hard_distortion():
    processor = DistortionProcessor(gain=1.0, kind="hard")

    input_values = np.array([-2.0, -1.0, 0.0, 0.5, 1.0, 2.0])
    expected_output = np.array([0.0, 0.0, 0.0, 0.5, 1.0, 1.0])

    output_values = processor.hard(input_values)

    assert np.allclose(output_values, expected_output)


def test_get_distortion():
    processor = DistortionProcessor(gain=1.0, kind="tanh")

    tanh_fn = processor.get_distortion("tanh")
    assert tanh_fn == processor.tanh

    hard_fn = processor.get_distortion("hard")
    assert hard_fn == processor.hard

    with pytest.raises(ValueError, match="Unknown distortion kind: invalid"):
        processor.get_distortion("invalid")


def test_process_tanh():
    left = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
    right = np.array([0.0, -0.5, -1.0, -0.5, 0.0])
    sound = Sound(left, right, 44100)

    processor = DistortionProcessor(gain=2.0, kind="tanh")
    processed = processor._process(sound)

    expected_left = np.tanh(left * 2.0) * 0.5 + 0.5
    expected_right = np.tanh(right * 2.0) * 0.5 + 0.5

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
    expected_left = np.clip(input_left, 0, 1)

    input_right = right * 1.5
    expected_right = np.clip(input_right, 0, 1)

    assert np.allclose(processed.left, expected_left)
    assert np.allclose(processed.right, expected_right)
    assert processed.sample_rate == sound.sample_rate


def test_process_method():
    left = np.array([0.0, 0.5, 1.0])
    right = np.array([0.0, -0.5, -1.0])
    sound = Sound(left, right, 44100, "test_sound")

    processor = DistortionProcessor(gain=2.0, kind="tanh")
    processed_sounds = processor.process([sound])

    assert isinstance(processed_sounds, list)
    assert len(processed_sounds) == 1

    processed_sound = processed_sounds[0]

    assert processed_sound.filename is not None
    assert processed_sound.filename != sound.filename
    assert "test_sound" in processed_sound.filename
