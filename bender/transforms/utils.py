import numpy as np
from scipy.signal import butter, sosfilt


def pad_reshape(data: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    assert len(data.shape) == 1, "data must be 1D"
    assert len(shape) > 0, "shape must be non-empty"

    total_pixels = np.prod(shape).item()

    if len(data) > total_pixels:
        data = data[:total_pixels]
    elif len(data) < total_pixels:
        data = np.pad(data, (0, total_pixels - len(data)), mode="constant")

    return data.reshape(shape)


def lowpass(
    data: np.ndarray, cutoff: float, sampling_rate: float, order: int = 6
) -> np.ndarray:
    normal_cutoff = 2 * cutoff / sampling_rate
    sos = butter(order, normal_cutoff, btype="low", output="sos", analog=False)
    return sosfilt(sos, data)


def _get_carriers(n, carrier_freq, sr):
    t = np.linspace(0, n / sr, n)
    c1 = np.cos(2 * np.pi * carrier_freq * t)
    c2 = np.sin(2 * np.pi * carrier_freq * t)
    return c1, c2


def quam_encode(
    m1: np.ndarray, m2: np.ndarray, carrier_freq: float = 1000, sr: float = 48000
) -> np.ndarray:
    """
    Encode two messages into a single signal using Quadrature Amplitude Modulation (QAM).

    :param m1: First message
    :param m2: Second message
    :param carrier_freq: Carrier frequency
    :param sr: Sampling rate
    :return: Encoded signal
    """
    assert m1.shape == m2.shape, "messages must have the same shape"
    assert len(m1.shape) == 1, "messages must be 1D"
    assert carrier_freq > 0, "carrier frequency must be positive"
    assert sr > 0, "sampling rate must be positive"
    assert carrier_freq < sr / 2, (
        "carrier frequency must be less than half the sampling rate"
    )

    c1, c2 = _get_carriers(m1.shape[0], carrier_freq, sr)

    return m1 * c1 + m2 * c2


def qam_decode(
    signal: np.ndarray,
    carrier_freq: float = 1000,
    sr: float = 48000,
    offset: float = 1.5,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Decode a signal into two messages using Quadrature Amplitude Modulation (QAM).

    :param signal: Encoded signal
    :param carrier_freq: Carrier frequency
    :param sr: Sampling rate
    :param offset: Offset for the lowpass filter
    :return: Decoded messages (m1, m2)
    """
    assert len(signal.shape) == 1
    assert carrier_freq > 0, "carrier frequency must be positive"
    assert sr > 0, "sampling rate must be positive"
    assert carrier_freq < sr / 2, (
        "carrier frequency must be less than half the sampling rate"
    )
    assert offset >= 1, "offset must be greater or equal than 1"

    c1, c2 = _get_carriers(signal.shape[0], carrier_freq, sr)

    m1 = lowpass(signal * c1, carrier_freq * offset, sr, 6) * 2.0
    m2 = lowpass(signal * c2, carrier_freq * offset, sr, 6) * 2.0

    return m1, m2


def am_encode(
    message: np.ndarray, carrier_freq: float = 1000, sr: float = 48000
) -> np.ndarray:
    """
    Encode a message using Amplitude Modulation (AM).

    :param message: Message to encode
    :param carrier_freq: Carrier frequency
    :param sr: Sampling rate
    :return: Encoded signal (AM modulated)
    """
    assert len(message.shape) == 1, "message must be 1D"
    assert carrier_freq > 0, "carrier frequency must be positive"
    assert sr > 0, "sampling rate must be positive"
    assert carrier_freq < sr / 2, (
        "carrier frequency must be less than half the sampling rate"
    )

    carrier, _ = _get_carriers(message.shape[0], carrier_freq, sr)
    return message * carrier


def am_decode(
    signal: np.ndarray,
    carrier_freq: float = 1000,
    sr: float = 48000,
    offset: float = 1.5,
) -> np.ndarray:
    """
    Decode a message using Amplitude Modulation (AM).

    :param signal: Signal to decode
    :param carrier_freq: Carrier frequency
    :param sr: Sampling rate
    :param offset: Offset for the lowpass filter
    :return: Decoded message (AM demodulated)
    """
    assert len(signal.shape) == 1, "message must be 1D"
    assert carrier_freq > 0, "carrier frequency must be positive"
    assert sr > 0, "sampling rate must be positive"
    assert carrier_freq < sr / 2, (
        "carrier frequency must be less than half the sampling rate"
    )
    assert offset >= 1, "offset must be greater or equal than 1"

    carrier, _ = _get_carriers(signal.shape[0], carrier_freq, sr)
    return lowpass(signal * carrier, carrier_freq * offset, sr, 6) * 2.0


def rgb_to_ycbcr(
    r: np.ndarray, g: np.ndarray, b: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert RGB to YCbCr

    :param r: Red channel [0, 1]
    :param g: Green channel [0, 1]
    :param b: Blue channel [0, 1]
    :return: Y [0, 1], Cb [-0.5, 0.5] and Cr [-0.5, 0.5] channels
    """
    y = 0.299 * r + 0.587 * g + 0.114 * b
    c_b = -0.168736 * r + -0.331264 * g + 0.500 * b
    c_r = 0.500 * r + -0.418688 * g + -0.081312 * b

    y = np.clip(y, 0.0, 1.0)
    c_b = np.clip(c_b, -0.5, 0.5)
    c_r = np.clip(c_r, -0.5, 0.5)

    return y, c_b, c_r


def ycbcr_to_rgb(
    y: np.ndarray, c_b: np.ndarray, c_r: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert YCbCr to RGB
    :param y: Y channel [0, 1]
    :param c_b: Cb channel [-0.5, 0.5]
    :param c_r: Cr channel [-0.5, 0.5]
    :return: R [0, 1], G [0, 1] and B [0, 1] channels
    """
    r = 1.0 * y + 0 * c_b + 1.402 * c_r
    g = 1.0 * y + -0.344136 * c_b + -0.714136 * c_r
    b = 1.0 * y + 1.772 * c_b + 0 * c_r

    r = np.clip(r, 0, 1)
    g = np.clip(g, 0, 1)
    b = np.clip(b, 0, 1)

    return r, g, b
