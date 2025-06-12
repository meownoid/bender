import numpy as np
from numexpr import evaluate

from bender.sound import Sound


class Modulation:
    def __init__(
        self,
        expression: "float | str | Modulation",
        min_value: float | None = None,
        max_value: float | None = None,
    ):
        if isinstance(expression, Modulation):
            expression = expression._expression

        if not isinstance(expression, str):
            expression = str(expression)

        self._expression: str = expression
        self._min_value: float | None = min_value
        self._max_value: float | None = max_value

    def __call__(self, t: np.ndarray) -> np.ndarray:
        if not isinstance(t, np.ndarray):
            raise TypeError("Input must be a 1D numpy array")

        if t.ndim != 1:
            raise ValueError("Input array must be 1D")

        result = evaluate(
            self._expression,
            local_dict={},
            global_dict={"t": t, "pi": np.pi},
            casting="unsafe",
            sanitize=True,
            optimization="aggressive",
            truediv=True,
        )

        if self._min_value is not None:
            result = np.maximum(result, self._min_value)

        if self._max_value is not None:
            result = np.minimum(result, self._max_value)

        return result

    def like(self, x: list | np.ndarray | Sound, sr: int = 48000) -> np.ndarray:
        if isinstance(x, Sound):
            t = np.linspace(0, x.duration, num=len(x))
        elif isinstance(x, np.ndarray):
            if x.ndim != 1:
                raise ValueError("Input array must be 1D")
            t = np.linspace(0, len(x) / sr, num=len(x))
        elif isinstance(x, list):
            t = np.linspace(0, len(x) / sr, num=len(x))
        else:
            raise TypeError("Input must be a Sound, numpy array, or list")

        return self(t)
