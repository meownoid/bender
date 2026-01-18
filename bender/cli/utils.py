import importlib
import pkgutil
from pathlib import Path
from typing import Any

import click

from bender.entity import Entity, get_entities
from bender.modulation import Modulation

SUPPORTED_IMAGE_EXTENSIONS = [
    ".bmp",
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
]

SUPPORTED_SOUND_EXTENSIONS = [".wav", ".aiff", ".aif"]

SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_SOUND_EXTENSIONS


class MappedChoice(click.Choice):
    def __init__(self, mapping: dict[str, Any], *args, **kwargs):
        super().__init__(list(mapping), *args, **kwargs)
        self.mapping = mapping

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        return self.mapping[value]


class ModulationParamType(click.ParamType):
    name = "modulation"

    def convert(self, value, param, ctx):
        if isinstance(value, Modulation):
            return value

        try:
            return Modulation(value)
        except (ValueError, TypeError):
            self.fail(f"{value!r} cannot be converted to modulation", param, ctx)


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


def is_image_file(name: Path | str) -> bool:
    name = Path(name)

    return name.suffix in SUPPORTED_IMAGE_EXTENSIONS


def is_sound_file(name: Path | str) -> bool:
    name = Path(name)

    return name.suffix in SUPPORTED_SOUND_EXTENSIONS


def parameters_to_dict(parameters: list[tuple[str, str]]) -> dict[str, str]:
    result = {}
    for key, value in parameters:
        if key in result:
            raise click.UsageError(f"duplicate parameter {key}")

        result[key] = value

    return result


def _import(name):
    module = importlib.import_module(name)

    for _, name, is_pkg in pkgutil.iter_modules(module.__path__, name + "."):
        if is_pkg:
            continue

        importlib.import_module(name)


def import_entities[T](cls: type[T], path: str) -> dict[str, Entity[T]]:
    _import(path)

    result = {}
    for entity in get_entities(cls):
        if entity.name in result:
            raise RuntimeError(f"duplicate {cls.__class__.__name__} {entity.name}")

        result[entity.name] = entity

    return result
