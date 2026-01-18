import secrets
from abc import abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Ordered[T](Protocol):
    """An ABC which supports ordering."""

    __slots__ = ()

    @abstractmethod
    def __lt__(self, other: T, /) -> bool:
        pass

    @abstractmethod
    def __gt__(self, other: T, /) -> bool:
        pass


def make_unique_output_path(input_path: str, ext: str, n: int | None = None) -> str:
    """
    Generate a unique output path based on the input path, extension, and an optional number.

    :param input_path: The original input path.
    :param ext: The file extension to use for the output path.
    :param n: An optional number to append to the output path.
    :return: A unique output path string.
    """
    n_str = f"-{n}" if n is not None else ""
    random_suffix = f"-{secrets.token_hex(4)}"
    return f"{Path(input_path).stem}{n_str}{random_suffix}{ext}"


def clamp(x, min_value: float | None = None, max_value: float | None = None) -> float:
    """
    Clamp a value between a minimum and maximum.

    :param x: The value to clamp.
    :param min_value: The minimum value (inclusive).
    :param max_value: The maximum value (inclusive).
    :return: The clamped value.
    """
    if min_value is not None and x < min_value:
        return min_value

    if max_value is not None and x > max_value:
        return max_value

    return x


def bytes_to_str(b: str | bytes | bytearray | memoryview) -> str:
    """Convert bytes, bytearray, or memoryview to str."""
    if isinstance(b, str):
        return b

    if isinstance(b, memoryview):
        b = b.tobytes()

    if isinstance(b, bytearray):
        b = bytes(b)

    if isinstance(b, bytes):
        return b.decode("utf-8")

    raise TypeError(f"Expected str, bytes, bytearray, or memoryview, got {type(b)}")
