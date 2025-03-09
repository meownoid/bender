from pathlib import Path
from typing import Any

import click

IMAGE_EXTENSIONS = [
    ".bmp",
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
]

SOUND_EXTENSIONS = [".wav", ".aiff"]

SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS + SOUND_EXTENSIONS


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


def is_image_file(name: Path | str) -> bool:
    name = Path(name)

    return name.suffix in IMAGE_EXTENSIONS


def is_sound_file(name: Path | str) -> bool:
    name = Path(name)

    return name.suffix in SOUND_EXTENSIONS


def parameters_to_dict(parameters: list[tuple[str, str]]) -> dict[str, str]:
    result = {}
    for key, value in parameters:
        if key in result:
            raise click.UsageError(f"duplicate parameter {key}")

        result[key] = value

    return result


def format_parameters(parameters: dict[str, str]) -> str:
    if not parameters:
        return "default parameters"

    return ", ".join(f"{key}={value}" for key, value in parameters.items())
