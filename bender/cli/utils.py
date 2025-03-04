from typing import Any

import click


class MappedChoice(click.Choice):
    def __init__(self, mapping: dict[str, Any], *args, **kwargs):
        super().__init__(list(mapping), *args, **kwargs)
        self.mapping = mapping

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        return self.mapping[value]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


def is_image_file(name):
    return name.lower().endswith(
        (".bmp", ".gif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")
    )


def is_sound_file(name):
    return name.lower().endswith((".wav", ".aiff"))


def parameters_to_dict(parameters: list[tuple[str, str]]) -> dict[str, str]:
    result = {}
    for key, value in parameters:
        if key in result:
            raise click.BadParameter(f"duplicate parameter {key}")

        result[key] = value

    return result
