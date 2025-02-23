import importlib
import pkgutil
import re
from dataclasses import dataclass
from typing import Callable, Type

from bender.edit import Edit
from bender.effect import Effect
from bender.parameter import Parameter
from bender.transform import Transform


@dataclass(frozen=True)
class Entity:
    name: str
    description: str
    parameters: dict[str, Parameter]

    def get_usage(self) -> str:
        lines = [f"[{self.name}] {self.description}", "Parameters:"]

        for name, parameter in self.parameters.items():
            lines.append(f"  - {name}: {parameter.get_usage()}")

        return "\n".join(lines)


@dataclass(frozen=True)
class TransformEntity(Entity):
    transform: Type[Transform]


@dataclass(frozen=True)
class EffectEntity(Entity):
    effect: Type[Effect]


@dataclass(frozen=True)
class EditEntity(Entity):
    edit: Type[Edit]


_transforms = {}
_effects = {}
_edits = {}

_entity_name_regex = re.compile(r"[^\W0-9]\w*", re.UNICODE | re.IGNORECASE)


def entity(
    name: str, description: str, parameters: dict[str, Parameter]
) -> Callable[[Type], Type]:
    def wrapper(cls: Type):
        nonlocal name, description, parameters

        name = name.lower().strip()

        if not _entity_name_regex.match(name):
            raise ValueError(f"Invalid entity name {name}")

        if issubclass(cls, Transform):
            if name in _transforms:
                raise ValueError(f"Transform {name} already exists")

            _transforms[name] = TransformEntity(name, description, parameters, cls)
        elif issubclass(cls, Effect):
            if name in _effects:
                raise ValueError(f"Effect {name} already exists")

            _effects[name] = EffectEntity(name, description, parameters, cls)
        elif issubclass(cls, Edit):
            if name in _edits:
                raise ValueError(f"Edit {name} already exists")

            _edits[name] = EditEntity(name, description, parameters, cls)
        else:
            raise ValueError(f"{cls.__name__} must be a Transform, Effect or Edit")

        return cls

    return wrapper


def _import(name):
    # Import the parent module
    module = importlib.import_module(name)

    for _, name, is_pkg in pkgutil.iter_modules(module.__path__, name + "."):
        if is_pkg:
            continue

        importlib.import_module(name)


def get_transforms() -> dict[str, TransformEntity]:
    _import("bender.transforms")
    return dict(_transforms)


def get_effects() -> dict[str, EffectEntity]:
    return dict(_effects)


def get_edits() -> dict[str, EditEntity]:
    return dict(_edits)
