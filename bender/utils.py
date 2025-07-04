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


def get_result_name(input_path: str, ext: str, n: int | None = None) -> str:
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
