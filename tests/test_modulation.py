import numpy as np
import pytest
from numpy import pi

from bender.modulation import Modulation
from bender.sound import Sound


def test_constant_modulation():
    mod = Modulation(5.0)
    t = np.linspace(0, 1, 100)
    result = mod(t)
    assert np.allclose(result, 5.0)


def test_expression_modulation():
    mod = Modulation("sin(2*pi*t)")
    t = np.linspace(0, 1, 1000)
    result = mod(t)
    expected = np.sin(2 * pi * t)
    assert np.allclose(result, expected)


def test_min_max_values():
    mod = Modulation("sin(2*pi*t)", min_value=-0.5, max_value=0.5)
    t = np.linspace(0, 1, 1000)
    result = mod(t)
    assert np.min(result) >= -0.5
    assert np.max(result) <= 0.5


def test_modulation_from_modulation():
    mod1 = Modulation("sin(2*pi*t)")
    mod2 = Modulation(mod1, min_value=-0.5, max_value=0.5)
    t = np.linspace(0, 1, 1000)
    result1 = mod1(t)
    result2 = mod2(t)
    assert np.all(result2 >= -0.5)
    assert np.all(result2 <= 0.5)
    mask = (result1 >= -0.5) & (result1 <= 0.5)
    assert np.allclose(result1[mask], result2[mask])


def test_like_method_with_array():
    mod = Modulation("t")
    x = np.zeros(1000)
    sr = 48000
    result = mod.like(x, sr)
    expected = np.linspace(0, len(x) / sr, num=len(x))
    assert np.allclose(result, expected)


def test_like_method_with_list():
    mod = Modulation("t")
    x = [0] * 1000
    sr = 48000
    result = mod.like(x, sr)
    expected = np.linspace(0, len(x) / sr, num=len(x))
    assert np.allclose(result, expected)


def test_like_method_with_sound():
    sound = Sound(np.zeros(1000), np.zeros(1000), 48000)
    mod = Modulation("t")
    result = mod.like(sound)
    expected = np.linspace(0, sound.duration, num=len(sound))
    assert np.allclose(result, expected)


def test_invalid_array_inputs():
    mod = Modulation("t")
    with pytest.raises(ValueError):
        mod(np.zeros((10, 10)))
    with pytest.raises(ValueError):
        mod.like(np.zeros((10, 10)))


def test_fast_path_constant():
    mod1 = Modulation(3.0)
    assert mod1._constant == 3.0

    mod2 = Modulation("3.0")
    assert mod2._constant == 3.0

    mod3 = Modulation("t")
    assert mod3._constant is None
