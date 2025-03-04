import importlib
import json
import pkgutil
import secrets
from pathlib import Path
from typing import Iterable

import click
from PIL import Image

from bender.cli.utils import (
    MappedChoice,
    add_options,
    is_image_file,
    is_sound_file,
    parameters_to_dict,
)
from bender.entity import get_entities, Entity
from bender.sound import load_sound
from bender.transform import Transform, TransformResult

DEFAULT_ALGORITHM = "bmp"


transform_options = [
    click.option(
        "-a",
        "--algorithm",
        type=str,
        help=f"Algorithm to use for transformation (default: {DEFAULT_ALGORITHM}).",
        default=None,
    ),
    click.option(
        "-p",
        "--parameter",
        "parameters",
        type=(str, str),
        multiple=True,
        help="Algorithm parameters.",
    ),
    click.option(
        "-q",
        "--quality",
        type=click.IntRange(0, 100, clamp=True),
        default=95,
        help="Output image quality.",
    ),
    click.option(
        "-s",
        "--sample-rate",
        type=click.IntRange(11025, 384000, clamp=True),
        default=48000,
        help="Output sound file sample rate.",
    ),
    click.option(
        "-b",
        "--bit-depth",
        type=MappedChoice({"8": 8, "16": 16, "24": 24, "32": 32}),
        default="16",
        help="Output sound file bit depth.",
    ),
    click.option(
        "-f", "--force", is_flag=True, default=False, help="Overwrite existing files."
    ),
]


def _import(name):
    # Import the parent module
    module = importlib.import_module(name)

    for _, name, is_pkg in pkgutil.iter_modules(module.__path__, name + "."):
        if is_pkg:
            continue

        importlib.import_module(name)


def _import_transforms() -> dict[str, Entity[Transform]]:
    _import("bender.transforms")

    result = {}
    for entity in get_entities(Transform):
        if entity.name in result:
            raise RuntimeError(f"duplicate transform {entity.name}")

        result[entity.name] = entity

    return result


def _find_metadata_file(path: Path) -> Path | None:
    candidates = []

    for candidate in path.parent.iterdir():
        if path.name.startswith(candidate.stem) and candidate.suffix == ".json":
            candidates.append(candidate)

    if not candidates:
        return None

    return max(candidates, key=lambda p: len(p.stem))


def _build_transform(
    algorithm: str,
    parameters: dict[str, str],
) -> Transform:
    transform_entities = _import_transforms()

    if algorithm not in transform_entities:
        raise click.BadParameter(
            f"unknown transform {algorithm}, available: {', '.join(transform_entities)}"
        )

    try:
        return transform_entities[algorithm].build(parameters)
    except ValueError as err:
        raise click.BadParameter(*err.args)


def _image_to_sound(
    file: Path,
    algorithm: str | None,
    parameters: dict[str, str],
    sample_rate: int,
    bit_depth: int,
    output: Path,
    force: bool,
) -> Path:
    if algorithm is None:
        algorithm = DEFAULT_ALGORITHM

    unique_id = secrets.token_hex(4)
    stem = file.with_suffix("").stem

    if output.is_dir():
        sound_path = output / f"{stem}_{unique_id}.wav"
        metadata_path = output / f"{stem}_{unique_id}.json"
    else:
        sound_path = output
        metadata_path = output.with_suffix(".json")

    if not force:
        if sound_path.exists():
            raise click.BadParameter(
                f"{sound_path} already exists, use -f to overwrite"
            )

        if metadata_path.exists():
            raise click.BadParameter(
                f"{metadata_path} already exists, use -f to overwrite"
            )

    image = Image.open(file)

    if image.mode != "RGB":
        image = image.convert("RGB")

    transform = _build_transform(algorithm, parameters)
    result = transform.encode(image)
    metadata = {
        "version": 1,
        "algorithm": algorithm,
        "parameters": parameters,
        "metadata": result.metadata,
    }

    result.sound.save(sound_path, sample_rate=sample_rate, bit_depth=bit_depth)
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    return sound_path


def _sound_to_image(
    file: Path,
    algorithm: str | None,
    parameters: dict[str, str],
    quality: int,
    output: Path,
    force: bool,
) -> Path:
    if output.is_dir():
        output = output / file.with_suffix(".jpg").name

    if force and output.exists():
        raise click.BadParameter(f"{output} already exists, use -f to overwrite")

    if (metadata_path := _find_metadata_file(file)) is None:
        raise click.BadParameter(
            f"no metadata file for {file}, make sure it is in the same directory and has the same prefix"
        )

    sound = load_sound(file)
    metadata = json.loads(metadata_path.read_text())

    if algorithm is None:
        algorithm = metadata["algorithm"]

    parameters = metadata["parameters"].update(parameters)

    transform = _build_transform(algorithm, parameters)
    image = transform.decode(TransformResult(sound, metadata["metadata"]))

    image.save(output, quality=quality)

    return output


def _list_transforms(ctx, _, value) -> None:
    if not value:
        return

    for t in _import_transforms().values():
        click.echo(t.get_usage())

    ctx.exit()


@click.command(
    "transform",
    help="Convert images to sound and vice versa.",
)
@click.argument("files", type=click.Path(exists=True), nargs=-1)
@add_options(transform_options)
@click.option(
    "--list",
    is_flag=True,
    help="List all available transforms and exit.",
    callback=_list_transforms,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=True, dir_okay=True, writable=True),
    help="Output file name.",
    default=None,
)
def transform_command(
    files: Iterable[Path],
    algorithm: str | None,
    parameters: list[tuple[str, str]] | None = None,
    quality: int = 95,
    bit_depth: int = 24,
    sample_rate: int = 48000,
    output: Path | None = None,
    force: bool = False,
) -> list[Path]:
    if parameters is None:
        parameters = []

    parameter_dict = parameters_to_dict(parameters)

    if output is None:
        output = Path.cwd()

    result = []
    for file in files:
        if is_image_file(file):
            result.append(
                _image_to_sound(
                    file,
                    algorithm=algorithm,
                    parameters=parameter_dict,
                    sample_rate=sample_rate,
                    bit_depth=bit_depth,
                    output=output,
                    force=force,
                )
            )
        elif is_sound_file(file):
            result.append(
                _sound_to_image(
                    file,
                    algorithm=algorithm,
                    parameters=parameter_dict,
                    quality=quality,
                    output=output,
                    force=force,
                )
            )
        else:
            raise click.BadParameter(
                f"{file}: unknown file type, expected image or sound"
            )

    return result
