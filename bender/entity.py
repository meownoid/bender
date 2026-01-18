from dataclasses import dataclass, field
from typing import Callable, Iterable

import click

from bender.parameter import Parameter, build_parameters


@dataclass(frozen=True)
class Entity[T]:
    name: str
    description: str
    parameters: dict[str, Parameter]
    cls: type[T]

    def get_usage(self) -> str:
        # Entity name in bold and bright green, description in white
        lines = [
            f"{click.style(self.name, fg='green', bold=True)}: "
            f"{click.style(self.description, fg='white', bold=True)}"
        ]

        # Parameters in cyan with yellow parameter names
        for name, parameter in self.parameters.items():
            name_colorized = click.style(name, fg="yellow")
            description = parameter.description or "no description"
            description_colorized = click.style(description, fg="cyan")
            traits = ", ".join(parameter.traits)
            traits_colorized = click.style(f"({traits})", fg="white")
            lines.append(
                f"  - {name_colorized}: {description_colorized} {traits_colorized}"
            )

        return "\n".join(lines)

    def build(self, parameter_values: dict[str, str]) -> T:
        return self.cls(**build_parameters(self.parameters, parameter_values))


@dataclass
class _Node[K, V]:
    value: V | None = None
    children: dict[K, "_Node[K, V]"] = field(default_factory=dict)


def _tree_add[K, V](root: _Node[K, V], path: Iterable[K], value: V) -> None:
    node = root
    for key in path:
        node = node.children.setdefault(key, _Node())

    if node.value is not None:
        raise ValueError(f"Duplicate path: {path}")

    node.value = value


def _tree_leafs[K, V](root: _Node[K, V]) -> list[V]:
    leafs = []

    def recurse(node: _Node[K, V]):
        if node.value is not None:
            leafs.append(node.value)

        for child in node.children.values():
            recurse(child)

    recurse(root)
    return leafs


def _tree_find[K, V](root: _Node[K, V], path: Iterable[K]) -> list[V]:
    node = root

    for key in path:
        if (maybe_node := node.children.get(key)) is None:
            return []

        node = maybe_node

    return _tree_leafs(node)


_entities_root = _Node[type, Entity]()


def entity[T](
    name: str, description: str, parameters: dict[str, Parameter]
) -> Callable[[type[T]], type[T]]:
    name = name.lower().strip()

    def wrapper(cls: type[T]) -> type[T]:
        nonlocal name, description, parameters

        # object will always be the last class in the mro
        _tree_add(
            _entities_root,
            reversed(cls.__mro__),
            Entity(name=name, description=description, parameters=parameters, cls=cls),
        )

        return cls

    return wrapper


def get_entities[T](cls: type[T]) -> list[Entity[T]]:
    return _tree_find(_entities_root, reversed(cls.__mro__))
