import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import click
from PIL import Image, ImageOps

from bender.cli.autocomplete import autocomplete
from bender.cli.utils import (
    SUPPORTED_EXTENSIONS,
    MappedChoice,
    add_options,
    import_entities,
    is_image_file,
    is_sound_file,
    parameters_to_dict,
)
from bender.converter import ConvertedImage, Converter
from bender.sound import Sound

DEFAULT_ALGORITHM = "bmp"


# options shared with monitor command
converter_shared_options = [
    click.option(
        "-a",
        "--algorithm",
        type=str,
        help=f"Algorithm to use for conversion (default: {DEFAULT_ALGORITHM}).",
        default=None,
        shell_complete=autocomplete,
    ),
    click.option(
        "-p",
        "--parameter",
        "parameters",
        type=(str, str),
        multiple=True,
        help="Algorithm parameters.",
        shell_complete=autocomplete,
    ),
    click.option(
        "-q",
        "--quality",
        type=click.IntRange(0, 100, clamp=True),
        default=95,
        help="Output image quality.",
    ),
    click.option(
        "-b",
        "--bit-depth",
        type=MappedChoice({"8": 8, "16": 16, "24": 24, "32": 32}),
        default="16",
        help="Output sound file bit depth.",
    ),
    click.option(
        "-r",
        "--rotate",
        is_flag=True,
        default=False,
        help="Rotate image 90 degrees clockwise before processing.",
    ),
    click.option(
        "-f", "--force", is_flag=True, default=False, help="Overwrite existing files."
    ),
]


def _find_metadata_file(path: Path) -> Path | None:
    candidates = []

    for candidate in path.parent.iterdir():
        if path.name.startswith(candidate.stem) and candidate.suffix == ".json":
            candidates.append(candidate)

    if not candidates:
        return None

    return max(candidates, key=lambda p: len(p.stem))


def _build_converter(
    algorithm: str,
    parameters: dict[str, Any],
) -> Converter:
    converter_entities = import_entities(Converter, "bender.converters")

    if algorithm not in converter_entities:
        raise click.UsageError(
            f"unknown converter {algorithm}, available: {', '.join(converter_entities)}"
        )

    try:
        return converter_entities[algorithm].build(parameters)
    except ValueError as err:
        raise click.UsageError(*err.args)


def _image_to_sound(
    file: Path,
    algorithm: str | None,
    parameters: dict[str, str],
    bit_depth: int,
    output: Path,
    force: bool,
    rotate: bool = False,
) -> Path:
    if algorithm is None:
        algorithm = DEFAULT_ALGORITHM

    image = Image.open(file)

    if image.mode != "RGB":
        image = image.convert("RGB")

    # for some reason exif_transpose returns None
    # if orientation is not supported
    if (image_rotated := ImageOps.exif_transpose(image)) is not None:
        image = image_rotated

    if rotate:
        image = image.rotate(-90, expand=True)

    if not hasattr(image, "filename") or not image.filename:
        image.filename = str(file)

    converter = _build_converter(algorithm, parameters)
    result = converter.encode(image)

    if not isinstance(result, ConvertedImage):
        raise click.UsageError(f"converter returned invalid result: {result}")

    metadata = {
        "version": 1,
        "algorithm": algorithm,
        "parameters": parameters,
        "rotate": rotate,
        "metadata": result.metadata,
    }

    dumped_metadata = json.dumps(metadata, indent=2, ensure_ascii=False)
    unique_id = hashlib.sha1(dumped_metadata.encode("utf-8")).hexdigest()[:7]
    stem = file.with_suffix("").stem

    if output.is_dir():
        sound_path = output / f"{stem}-{unique_id}.wav"
        metadata_path = output / f"{stem}-{unique_id}.json"
    else:
        sound_path = output
        metadata_path = output.with_suffix(".json")

    if not force:
        if sound_path.exists():
            raise click.UsageError(f"{sound_path} already exists, use -f to overwrite")

        if metadata_path.exists():
            raise click.UsageError(
                f"{metadata_path} already exists, use -f to overwrite"
            )

    click.echo(f"Saving {sound_path}")
    result.sound.resample(48000).save(sound_path, bit_depth=bit_depth)

    click.echo(f"Saving {metadata_path}")
    metadata_path.write_text(dumped_metadata)

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

    if not force and output.exists():
        raise click.UsageError(f"{output} already exists, use -f to overwrite")

    if (metadata_path := _find_metadata_file(file)) is None:
        raise click.UsageError(
            f"no metadata file for {file}, make sure it is in the same directory and has the same prefix"
        )

    click.echo(f"Found metadata at {metadata_path}")

    sound = Sound.load(file)
    metadata = json.loads(metadata_path.read_text())

    if algorithm is None:
        if "algorithm" not in metadata:
            raise click.UsageError(
                f"no algorithm specified and no metadata found in {metadata_path}"
            )
        algorithm = metadata["algorithm"]

    if not algorithm:
        raise click.UsageError("no algorithm specified")

    parameters = {**metadata.get("parameters", {}), **parameters}

    converter = _build_converter(algorithm, parameters)
    image = converter.decode(ConvertedImage(sound, metadata.get("metadata", {})))

    if not isinstance(image, Image.Image):
        raise click.UsageError(f"converter returned invalid result: {image}")

    if image.mode != "RGB":
        image = image.convert("RGB")

    was_rotated = metadata.get("rotate", False)
    if was_rotated:
        image = image.rotate(90, expand=True)

    click.echo(f"Saving {output}")
    image.save(output, quality=quality)

    return output


def _list_converters(ctx, _, value) -> None:
    if not value:
        return

    for t in import_entities(Converter, "bender.converters").values():
        click.echo(t.get_usage())

    ctx.exit()


def _convert_command(
    file: Path,
    algorithm: str | None,
    parameters: list[tuple[str, str]] | None = None,
    quality: int = 95,
    bit_depth: int = 24,
    output: Path | None = None,
    force: bool = False,
    rotate: bool = False,
) -> Path:
    if parameters is None:
        parameters = []

    parameter_dict = parameters_to_dict(parameters)

    if output is None:
        output = Path.cwd()

    click.echo(f"Converting {file}")

    if is_image_file(file):
        return _image_to_sound(
            file,
            algorithm=algorithm,
            parameters=parameter_dict,
            bit_depth=bit_depth,
            output=output,
            force=force,
            rotate=rotate,
        )

    if is_sound_file(file):
        return _sound_to_image(
            file,
            algorithm=algorithm,
            parameters=parameter_dict,
            quality=quality,
            output=output,
            force=force,
        )

    raise click.UsageError(
        f"{file}: unknown file type, expected one of {', '.join(SUPPORTED_EXTENSIONS)}"
    )


@click.command(
    "convert",
    help="Convert images to sound and vice versa.",
)
@click.argument("files", type=click.Path(exists=True, path_type=Path), nargs=-1)
@add_options(converter_shared_options)
@click.option(
    "--list",
    is_flag=True,
    help="List all available converters and exit.",
    callback=_list_converters,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=True, dir_okay=True, writable=True, path_type=Path),
    help="Output file name.",
    default=None,
)
@click.option(
    "-n",
    "--n-times",
    type=int,
    default=1,
    help="Number of times to apply the conversion.",
)
def convert_command(files: Iterable[Path], n_times: int = 1, **kwargs) -> None:
    for file in files:
        for _ in range(n_times):
            file = _convert_command(file, **kwargs)
