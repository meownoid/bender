from abc import abstractmethod
from typing import runtime_checkable, Protocol


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
