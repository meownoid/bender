import numpy as np
import pytest

from bender.sound import Sound


def test_sound_initialization():
    left = np.array([0.0, 1.0, 0.5])
    right = np.array([0.0, 1.0, 0.5])
    sample_rate = 44100

    sound = Sound(left, right, sample_rate)

    assert np.array_equal(sound.left, left)
    assert np.array_equal(sound.right, right)
    assert sound.sample_rate == sample_rate

    with pytest.raises(ValueError):
        Sound(left[:-1], right, sample_rate)  # Unequal channel lengths

    with pytest.raises(ValueError):
        Sound(np.array([]), np.array([]), -44100)  # Negative sample rate


def test_resample():
    left = np.array([0.0, 1.0, 0.5])
    right = np.array([0.0, 1.0, 0.5])
    sample_rate = 44100
    new_sample_rate = 22050

    sound = Sound(left, right, sample_rate)
    resampled_sound = sound.resample(new_sample_rate)

    assert resampled_sound.sample_rate == new_sample_rate
    assert resampled_sound.left.shape[0] != left.shape[0]
    assert resampled_sound.right.shape[0] != right.shape[0]

    # Resampling to the same rate should return the same object
    same_sample_rate_sound = sound.resample(sample_rate)
    assert same_sample_rate_sound is sound


def test_process():
    left = np.array([0.0, 1.0, 0.5])
    right = np.array([0.0, 1.0, 0.5])
    sample_rate = 44100

    sound = Sound(left, right, sample_rate)
    processed_sound = sound.process(lambda x, _: np.negative(x))

    assert np.array_equal(processed_sound.left, -left)
    assert np.array_equal(processed_sound.right, -right)


def test_save_load(tmp_path):
    left = np.array([0.0, 1.0, 0.5])
    right = np.array([0.0, 1.0, 0.5])
    sample_rate = 44100
    sound = Sound(left, right, sample_rate)

    path = tmp_path / "test.wav"
    sound.save(path, bit_depth=16)

    # Verify that file is saved
    assert path.exists()

    # Load the saved file
    loaded_sound = Sound.load(path)

    # Verify that the loaded sound matches the original sound
    assert np.allclose(loaded_sound.left, sound.left, atol=1e-3)
    assert np.allclose(loaded_sound.right, sound.right, atol=1e-3)
    assert loaded_sound.sample_rate == sample_rate
