import numpy as np

from bender.effects import brick_wall_limit, mix
from bender.modulation import Modulation


def test_mix_zero_returns_dry():
    dry = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    wet = np.array([4.0, 5.0, 6.0], dtype=np.float32)

    result = mix(dry, wet, sample_rate=44100, mix=Modulation(0.0))

    assert result is dry
    assert np.allclose(result, dry)


def test_mix_one_returns_wet():
    dry = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    wet = np.array([4.0, 5.0, 6.0], dtype=np.float32)

    result = mix(dry, wet, sample_rate=44100, mix=Modulation(1.0))

    assert result is wet
    assert np.allclose(result, wet)


def test_mix_pads_shorter_signal():
    dry = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    wet = np.array([10.0, 20.0, 30.0, 40.0, 50.0], dtype=np.float32)

    result = mix(dry, wet, sample_rate=44100, mix=Modulation(0.5))

    expected_dry = np.pad(dry, (0, len(wet) - len(dry)), mode="constant")
    expected = 0.5 * expected_dry + 0.5 * wet

    assert len(result) == len(wet)
    assert np.allclose(result, expected)


def test_mix_modulation_signal():
    dry = np.ones(5, dtype=np.float32)
    wet = np.zeros(5, dtype=np.float32)

    result = mix(dry, wet, sample_rate=5, mix=Modulation("t"))

    mix_value = np.linspace(0, 1, num=5)
    expected = (1 - mix_value) * dry

    assert np.allclose(result, expected)


def test_brick_wall_limit_no_change_below_threshold():
    sample_rate = 48000
    signal = np.full(1000, 0.1, dtype=np.float32)

    result = brick_wall_limit(signal, sample_rate, threshold=1.0)

    assert np.allclose(result, signal, atol=1e-6)


def test_brick_wall_limit_caps_peaks():
    sample_rate = 48000
    signal = np.zeros(5000, dtype=np.float32)
    signal[1000] = 2.0
    signal[2000] = -1.5

    result = brick_wall_limit(signal, sample_rate, threshold=1.0)

    assert np.max(np.abs(result)) <= 1.0 + 1e-2
    assert np.abs(result[1000]) < np.abs(signal[1000])
    assert np.abs(result[2000]) < np.abs(signal[2000])
