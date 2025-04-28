import secrets
from abc import abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Ordered(Protocol):
    """An ABC which supports ordering."""

    __slots__ = ()

    @abstractmethod
    def __lt__(self, other):
        pass

    @abstractmethod
    def __gt__(self, other):
        pass


def get_result_name(input_path: str, ext: str, n: int | None = None) -> str:
    n_str = f"-{n}" if n is not None else ""
    random_suffix = f"-{secrets.token_hex(4)}"
    return f"{Path(input_path).stem}{n_str}{random_suffix}{ext}"
