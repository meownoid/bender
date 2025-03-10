from dataclasses import dataclass
from typing import Any

from bender.utils import Ordered


@dataclass(frozen=True)
class Parameter[T]:
    description: str | None = None
    default: T | None = None
    required: bool = False

    def get_usage(self) -> str:
        result = self.description

        if result is None:
            result = self.__class__.__name__

        if self.required:
            result += " [required]"
        elif self.default is not None:
            result += f" [default: {self.default}]"

        return result

    def parse(self, text: str) -> T:
        raise NotImplementedError(
            f"parse is not implemented in {self.__class__.__name__}"
        )


@dataclass(frozen=True)
class StringParameter(Parameter[str]):
    """
    String parameter, returns the input as is.
    """

    def parse(self, text: str) -> str:
        return text


@dataclass(frozen=True)
class BoolParameter(Parameter[bool]):
    """
    Boolean parameter, accepts true/false, yes/no, 1/0.
    """

    default = False

    def parse(self, text: str) -> bool:
        text = text.strip().lower()

        if text in ("true", "yes", "1"):
            return True
        elif text in ("false", "no", "0"):
            return False
        else:
            raise ValueError(f"Invalid boolean value: {text}")


@dataclass(frozen=True)
class MinMaxParameter[T: Ordered](Parameter[T]):
    min_value: T | None = None
    max_value: T | None = None
    clamp: bool = False

    def get_usage(self) -> str:
        result = super().get_usage()

        if self.min_value is not None:
            result += f" [min: {self.min_value}]"

        if self.max_value is not None:
            result += f" [max: {self.max_value}]"

        return result

    def _parse(self, text: str) -> T:
        raise NotImplementedError(
            f"_parse is not implemented in {self.__class__.__name__}"
        )

    def parse(self, text: str) -> T:
        value = self._parse(text)

        if self.min_value is not None and value < self.min_value:
            if self.clamp:
                value = self.min_value
            else:
                raise ValueError(f"value {value} is less than minimum {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            if self.clamp:
                value = self.max_value
            else:
                raise ValueError(
                    f"value {value} is greater than maximum {self.max_value}"
                )

        return value


@dataclass(frozen=True)
class IntParameter(MinMaxParameter[int]):
    def _parse(self, text: str) -> int:
        return int(text)


@dataclass(frozen=True)
class FloatParameter(MinMaxParameter[float]):
    def _parse(self, text: str) -> float:
        return float(text)


def build_parameters(
    prototypes: dict[str, Parameter], values: dict[str, str]
) -> dict[str, Any]:
    for key in values:
        if key not in prototypes:
            raise ValueError(f"unknown parameter {key}")

    result = {}

    for key, prototype in prototypes.items():
        if key in values:
            try:
                result[key] = prototype.parse(values[key])
            except ValueError as err:
                raise ValueError(f"parameter {key}: {err}") from err
        else:
            if prototype.required:
                raise ValueError(f"missing required parameter {key}")
            else:
                result[key] = prototype.default

    return result
