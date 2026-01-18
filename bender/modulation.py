import numpy as np
from numexpr import evaluate

from bender.sound import Sound
from bender.utils import clamp


class Modulation:
    def __init__(
        self,
        expression: "float | str | Modulation",
        min_value: float | None = None,
        max_value: float | None = None,
    ):
        """
        Initialize a Modulation instance.

        :param expression: A mathematical expression as a string or a float.
        :param min_value: Optional minimum value for the modulation.
        :param max_value: Optional maximum value for the modulation.
        """
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")

        if isinstance(expression, Modulation):
            expression = expression._expression

        # Special case for constant modulation
        self._constant: float | None = None
        self._expression: str

        if isinstance(expression, float):
            self._constant = expression
            self._expression = str(expression)
        elif isinstance(expression, str):
            expression = expression.strip()
            if not expression:
                raise ValueError("Expression cannot be an empty string")

            try:
                self._constant = float(expression)
            except ValueError:
                pass

            self._expression = expression
        else:
            raise TypeError("Expression must be a float or a string")

        self._min_value: float | None = min_value
        self._max_value: float | None = max_value

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Modulation instance. Only exact matches are considered equal,
        e.g., Modulation("t") is not equal to Modulation("t + 0").

        :param other: Another Modulation instance.
        :return: True if equal, False otherwise.
        """
        if isinstance(other, Modulation):
            if self._min_value != other._min_value:
                return False

            if self._max_value != other._max_value:
                return False

            if self._constant is not None and other._constant is not None:
                return self._constant == other._constant

            return self._expression == other._expression

        return False

    def with_constraints(
        self, min_value: float | None = None, max_value: float | None = None
    ) -> "Modulation":
        """
        Create a new Modulation instance with updated constraints.

        :param min_value: New minimum value for the modulation.
        :param max_value: New maximum value for the modulation.
        :return: A new Modulation instance with updated constraints.
        """
        return Modulation(self._expression, min_value=min_value, max_value=max_value)

    @property
    def constant(self) -> float | None:
        return self._constant

    def __call__(self, t: np.ndarray) -> np.ndarray:
        """
        Evaluate the modulation expression at given time points.

        :param t: A 1D numpy array of time points.
        :return: A 1D numpy array of evaluated modulation values.
        """
        if not isinstance(t, np.ndarray):
            raise TypeError("Input must be a 1D numpy array")

        if t.ndim != 1:
            raise ValueError("Input array must be 1D")

        # Fast path for constant modulation
        if self._constant is not None:
            c = clamp(self._constant, self._min_value, self._max_value)
            return np.full_like(t, c, dtype=np.float32)

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
        """
        Generate a modulation signal based on the input sound or array.

        :param x: A Sound object, numpy array, or list to base the modulation on.
        :param sr: Sample rate to use for time calculation, default is 48000.
        :return: A 1D numpy array of modulation values.
        """
        if isinstance(x, Sound):
            duration = x.duration
            length = len(x)
        elif isinstance(x, np.ndarray):
            if x.ndim != 1:
                raise ValueError("Input array must be 1D")
            duration = len(x) / sr
            length = len(x)
        elif isinstance(x, list):
            duration = len(x) / sr
            length = len(x)
        else:
            raise TypeError("Input must be a Sound, numpy array, or list")

        # Fast path for constant modulation
        if self._constant is not None:
            c = clamp(self._constant, self._min_value, self._max_value)
            return np.full(length, c, dtype=np.float32)

        return self(np.linspace(0, duration, num=length))
