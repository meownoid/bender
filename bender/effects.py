import numba
import numpy as np

from bender.modulation import Modulation


@numba.jit(nopython=True)
def brick_wall_limit(
    signal: np.ndarray,
    sample_rate: int,
    attack_time: float = 0.001,
    release_time: float = 0.05,
    threshold: float = 1.0,
) -> np.ndarray:
    """
    A simple brick wall limiter effect.

    :param signal: Input audio signal as a NumPy array.
    :param sample_rate: Sample rate of the audio signal in Hz.
    :param attack_time: Attack time in seconds.
    :param release_time: Release time in seconds.
    :param threshold: Threshold level for limiting.
    :return: Processed audio signal with limiting applied.
    """
    n_releases = 4
    attack_samples = int(attack_time * sample_rate)
    if attack_samples % 2 != 0:
        attack_samples += 1
    attack_samples_2 = attack_samples // 2
    release_samples = int(release_time / n_releases / 2.5 * sample_rate)

    signal_length = len(signal)

    # Calculate gain reduction based on threshold
    gain_reduction = np.ones(signal_length)
    for i in range(signal_length):
        level = abs(signal[i])
        if level > threshold:
            gain_reduction[i] = threshold / level

    # Apply look-ahead: find minimum gain in future window
    hold_gain = np.ones(signal_length)
    for i in range(signal_length):
        hold_gain[i] = np.min(gain_reduction[i : i + attack_samples])

    # Smooth gain reduction
    attack_kernel = 1 / (1 + np.exp(np.linspace(-2, 2, attack_samples)))
    attack_kernel /= np.sum(attack_kernel)
    padded_gain = np.hstack(
        (hold_gain[:attack_samples][::-1], hold_gain, hold_gain[-attack_samples:][::-1])
    )
    smoothed_gain = np.convolve(padded_gain, attack_kernel, mode="same")[
        attack_samples_2 : -3 * attack_samples_2
    ]

    # Apply stacked release
    release_states = [1.0] * n_releases
    release_slew = 1.0 - np.exp(-1.0 / release_samples)

    release_gain = np.ones(signal_length)
    for i in range(signal_length):
        release_states[0] += (smoothed_gain[i] - release_states[0]) * release_slew
        release_states[0] = min(release_states[0], smoothed_gain[i])
        for j in range(1, n_releases):
            release_states[j] += (
                release_states[j - 1] - release_states[j]
            ) * release_slew
            release_states[j] = min(release_states[j], smoothed_gain[i])
        release_gain[i] = release_states[-1]

    return release_gain * signal


def mix(
    dry: np.ndarray,
    wet: np.ndarray,
    sample_rate: int,
    mix: Modulation = Modulation(0.5),
) -> np.ndarray:
    """
    Mix two audio signals using a modulated dry/wet amount.

    :param dry: Dry audio signal
    :param wet: Wet audio signal
    :param mix: Amount of the wet signal (1.0 = all wet, 0.0 = all dry)
    :return: Mixed audio signal
    """
    if mix == Modulation(0.0):
        return dry

    if mix == Modulation(1.0):
        return wet

    if len(dry) < len(wet):
        dry = np.pad(dry, (0, len(wet) - len(dry)), mode="constant")
    elif len(wet) < len(dry):
        wet = np.pad(wet, (0, len(dry) - len(wet)), mode="constant")

    mix_value = mix.like(dry, sample_rate)

    return (1 - mix_value) * dry + mix_value * wet
