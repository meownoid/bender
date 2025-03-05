from typing import Any


class Parameter[T]:
    def __init__(
        self,
        *,
        description: str | None,
        default: T | None = None,
        required: bool = False,
    ):
        if description is None:
            description = self.__class__.__name__

        self._description = description
        self._default = default
        self._required = required

    def get_usage(self) -> str:
        usage = self._description

        if self._required:
            usage += " (required)"
        elif self._default is not None:
            usage += f" (default: {self._default})"

        return usage

    @property
    def default(self) -> T | None:
        return self._default

    @property
    def required(self) -> bool:
        return self._required

    def parse(self, text: str) -> T:
        raise NotImplementedError(
            f"parse is not implemented in {self.__class__.__name__}"
        )


class StringParameter(Parameter[str]):
    def parse(self, text: str) -> str:
        return text


class BoolParameter(Parameter[bool]):
    def parse(self, text: str) -> bool:
        return text.lower() in ("true", "yes", "y", "1")


class IntParameter(Parameter[int]):
    def __init__(
        self,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        clamp: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        self.min_value = min_value
        self.max_value = max_value
        self.clamp = clamp

    def get_usage(self) -> str:
        usage = super().get_usage()
        additional = []

        if self.min_value is not None:
            additional.append(f"min: {self.min_value}")

        if self.max_value is not None:
            additional.append(f"max: {self.max_value}")

        return f"{usage} ({', '.join(additional)})"

    def parse(self, text: str) -> int:
        value = int(text)

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
