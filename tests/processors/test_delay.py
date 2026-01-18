import numpy as np

from bender.modulation import Modulation
from bender.processors.delay import DelayProcessor
from bender.sound import Sound


def test_delay_with_single_impulse():
    """Test delay effect with a single impulse signal."""
    # Create a signal with a single impulse at the beginning
    sample_rate = 44100
    signal_length = sample_rate * 2  # 2 seconds

    # Create a signal with a single impulse at the beginning
    left = np.zeros(signal_length)
    right = np.zeros(signal_length)
    left[0] = 1.0  # Impulse in left channel
    right[0] = 1.0  # Impulse in right channel

    sound = Sound(left, right, sample_rate)

    # Test with simple delay (no feedback, no ping-pong)
    delay_time = 0.5  # 500ms delay
    processor = DelayProcessor(
        lt=delay_time,
        rt=delay_time,
        pingpong=False,
        feedback=0.0,  # No feedback
        pitch=0,  # No pitch shift
        mix=1.0,  # 100% wet signal to clearly see the delay
    )

    processed = processor._process(sound)

    # Calculate the expected position of the impulse
    delay_samples = int(delay_time * sample_rate)

    # Check that the impulse appears at the delay position
    assert np.isclose(processed.left[0], 0.0)  # Original is removed due to mix=1.0
    assert np.isclose(
        processed.left[delay_samples], 1.0
    )  # Delayed impulse appears here
    assert np.sum(processed.left) == 1.0  # No other impulses should be present

    assert np.isclose(processed.right[0], 0.0)
    assert np.isclose(processed.right[delay_samples], 1.0)
    assert np.sum(processed.right) == 1.0


def test_delay_with_feedback():
    """Test delay effect with feedback using a single impulse signal."""
    sample_rate = 44100
    signal_length = sample_rate * 3  # 3 seconds

    # Create a signal with a single impulse at the beginning
    left = np.zeros(signal_length)
    right = np.zeros(signal_length)
    left[0] = 1.0
    right[0] = 1.0

    sound = Sound(left, right, sample_rate)

    # Test with feedback
    delay_time = 0.5  # 500ms delay
    feedback_amount = 0.5  # 50% feedback
    processor = DelayProcessor(
        lt=delay_time,
        rt=delay_time,
        pingpong=False,
        feedback=feedback_amount,
        pitch=0,
        mix=1.0,  # 100% wet signal to clearly see the delay
    )

    processed = processor._process(sound)

    # Calculate the expected position of the impulses with feedback
    delay_samples = int(delay_time * sample_rate)

    # Original impulse is removed due to mix=1.0
    assert np.isclose(processed.left[0], 0.0)
    assert np.isclose(processed.right[0], 0.0)

    # First delayed impulse
    assert np.isclose(processed.left[delay_samples], 1.0)
    assert np.isclose(processed.right[delay_samples], 1.0)

    # Second delayed impulse (with feedback attenuation)
    assert np.isclose(processed.left[2 * delay_samples], feedback_amount)
    assert np.isclose(processed.right[2 * delay_samples], feedback_amount)

    # Third delayed impulse (with more feedback attenuation)
    assert np.isclose(processed.left[3 * delay_samples], feedback_amount**2)
    assert np.isclose(processed.right[3 * delay_samples], feedback_amount**2)

    # Fourth delayed impulse (with more feedback attenuation)
    assert np.isclose(processed.left[4 * delay_samples], feedback_amount**3)
    assert np.isclose(processed.right[4 * delay_samples], feedback_amount**3)


def test_delay_with_pingpong():
    """Test ping-pong delay effect with a single impulse signal."""
    sample_rate = 44100
    signal_length = sample_rate * 3  # 3 seconds

    # Create a signal with a single impulse in left channel only
    left = np.zeros(signal_length)
    right = np.zeros(signal_length)
    left[0] = 1.0
    right[0] = 0.0  # No impulse in right channel to clearly see ping-pong effect

    sound = Sound(left, right, sample_rate)

    # Test with ping-pong
    delay_time = 0.5  # 500ms delay
    feedback_amount = 0.5  # 50% feedback
    processor = DelayProcessor(
        lt=delay_time,
        rt=delay_time,
        pingpong=True,  # Enable ping-pong
        feedback=feedback_amount,
        pitch=0,
        mix=1.0,  # 100% wet signal
    )

    processed = processor._process(sound)

    delay_samples = int(delay_time * sample_rate)

    # Initial impulse goes to left delay
    assert np.isclose(processed.left[delay_samples], 1.0)
    assert np.isclose(processed.right[delay_samples], 0.0)

    # First feedback goes to right channel (ping)
    assert np.isclose(processed.left[2 * delay_samples], 0.0, atol=1e-6)
    assert np.isclose(processed.right[2 * delay_samples], feedback_amount)

    # Second feedback back to left channel (pong)
    assert np.isclose(processed.left[3 * delay_samples], feedback_amount**2)
    assert np.isclose(processed.right[3 * delay_samples], 0.0, atol=1e-6)


def test_delay_with_different_times():
    """Test delay effect with different delay times for left and right channels."""
    sample_rate = 44100
    signal_length = sample_rate * 3  # 3 seconds

    # Create a signal with a single impulse
    left = np.zeros(signal_length)
    right = np.zeros(signal_length)
    left[0] = 1.0
    right[0] = 1.0

    sound = Sound(left, right, sample_rate)

    # Test with different delay times
    left_delay_time = 0.3  # 300ms delay for left
    right_delay_time = 0.6  # 600ms delay for right

    processor = DelayProcessor(
        lt=left_delay_time,
        rt=right_delay_time,
        pingpong=False,
        feedback=0.0,  # No feedback to simplify test
        pitch=0,
        mix=1.0,  # 100% wet signal
    )

    processed = processor._process(sound)

    left_delay_samples = int(left_delay_time * sample_rate)
    right_delay_samples = int(right_delay_time * sample_rate)

    # Check that the impulses appear at the expected positions
    assert np.isclose(processed.left[left_delay_samples], 1.0)
    assert np.isclose(processed.right[right_delay_samples], 1.0)

    assert np.sum(processed.left) == 1.0
    assert np.sum(processed.right) == 1.0


def test_process_method():
    """Test the process method which handles file naming."""
    sample_rate = 44100
    signal_length = 1000  # Short signal for quick test

    left = np.zeros(signal_length)
    right = np.zeros(signal_length)
    left[0] = 1.0
    right[0] = 1.0

    sound = Sound(left, right, sample_rate, "test_sound")

    processor = DelayProcessor(
        lt=0.5, rt=0.5, pingpong=False, feedback=0.0, pitch=0, mix=0.5
    )
    processed_sound = processor.process([sound])

    assert isinstance(processed_sound, Sound)


def test_delay_modulation():
    sample_rate = 44100
    signal_length = sample_rate * 2

    left = np.zeros(signal_length)
    right = np.zeros(signal_length)
    left[0] = 1.0
    right[0] = 1.0
    left[sample_rate] = 1.0
    right[sample_rate] = 1.0

    sound = Sound(left, right, sample_rate)

    delay_const = DelayProcessor(
        lt=0.6,
        rt=0.6,
        pingpong=False,
        feedback=0.0,
        pitch=0,
        mix=1.0,
    )

    delay_mod = DelayProcessor(
        lt=Modulation(0.6),
        rt=Modulation(0.6),
        pingpong=False,
        feedback=Modulation(0.0),
        pitch=0,
        mix=Modulation(1.0),
    )

    processed_const = delay_const._process(sound)
    processed_mod = delay_mod._process(sound)

    assert np.allclose(processed_const.left, processed_mod.left)
    assert np.allclose(processed_const.right, processed_mod.right)
