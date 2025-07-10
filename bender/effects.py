import numba
import numpy as np


@numba.jit(nopython=True)
def brick_wall_limiter(
    signal: np.ndarray,
    sample_rate: int,
    attack_time: float = 0.001,
    release_time: float = 0.05,
    threshold: float = 1.0,
) -> np.ndarray:
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
