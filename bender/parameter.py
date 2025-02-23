class Parameter:
    def __init__(self, *, description: str):
        self.description = description

    def get_usage(self):
        return self.description


class IntParameter(Parameter):
    def __init__(
        self,
        *,
        description: str,
        default: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ):
        super().__init__(description=description)
        self.default = default
        self.min_value = min_value
        self.max_value = max_value

    def get_usage(self):
        usage = super().get_usage()
        additional = []

        if self.default is not None:
            additional.append(f"default: {self.default}")

        if self.min_value is not None:
            additional.append(f"min: {self.min_value}")

        if self.max_value is not None:
            additional.append(f"max: {self.max_value}")

        return f"{usage} ({', '.join(additional)})"
