import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import click
from PIL import Image, ImageOps

from bender.cli.autocomplete import autocomplete
from bender.cli.utils import (
    DEFAULT_OUTPUT_IMAGE_FORMAT,
    OUTPUT_IMAGE_FORMATS,
    SUPPORTED_EXTENSIONS,
    MappedChoice,
    add_options,
    apply_image_output_format,
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
        help="Algorithm parameters (repeatable). Use -p key value or -p key=value.",
        shell_complete=autocomplete,
    ),
    click.option(
        "-q",
        "--quality",
        type=click.IntRange(0, 100, clamp=True),
        default=95,
        help="Output image quality (jpeg only; sound -> image only).",
    ),
    click.option(
        "-b",
        "--bit-depth",
        type=MappedChoice({"8": 8, "16": 16, "24": 24, "32": 32}),
        default="16",
        help="Output sound file bit depth (image -> sound only).",
    ),
    click.option(
        "-r",
        "--rotate",
        is_flag=True,
        default=False,
        help="Rotate image 90 degrees clockwise before processing.",
    ),
    click.option("-f", "--force", is_flag=True, default=False, help="Overwrite existing files."),
]


def _is_dir_path(path: Path) -> bool:
    if path.exists():
        return path.is_dir()

    return path.suffix == ""


def _ensure_dir(path: Path, option_name: str) -> Path:
    if path.exists():
        if not path.is_dir():
            raise click.UsageError(f"{option_name} must be a directory")
        return path

    if path.suffix:
        raise click.UsageError(f"{option_name} must be a directory")

    path.mkdir(parents=True, exist_ok=True)
    return path


def _find_metadata_file(path: Path) -> Path | None:
    candidates = []

    for candidate in path.parent.iterdir():
        if path.name.startswith(candidate.stem) and candidate.suffix.lower() == ".json":
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
    metadata_out: Path | None = None,
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
    else:
        sound_path = output

    if metadata_out is None:
        metadata_path = sound_path.with_suffix(".json")
    else:
        if _is_dir_path(metadata_out):
            metadata_out.mkdir(parents=True, exist_ok=True)
            metadata_path = metadata_out / sound_path.with_suffix(".json").name
        else:
            metadata_path = metadata_out

    if not force:
        if sound_path.exists():
            raise click.UsageError(f"{sound_path} already exists, use -f to overwrite")

        if metadata_path.exists():
            raise click.UsageError(f"{metadata_path} already exists, use -f to overwrite")

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
    output_format: str | None = None,
    metadata: Path | None = None,
) -> Path:
    if output.is_dir():
        ext = OUTPUT_IMAGE_FORMATS[output_format or DEFAULT_OUTPUT_IMAGE_FORMAT][0]
        output = output / file.with_suffix(ext).name
    else:
        output = apply_image_output_format(output, output_format)

    if not force and output.exists():
        raise click.UsageError(f"{output} already exists, use -f to overwrite")

    metadata_path = metadata or _find_metadata_file(file)
    if metadata_path is None:
        raise click.UsageError(
            f"no metadata file for {file}, use --metadata or place it in the same directory with the same prefix"
        )

    if metadata:
        click.echo(f"Using metadata at {metadata_path}")
    else:
        click.echo(f"Found metadata at {metadata_path}")

    sound = Sound.load(file)
    metadata_data = json.loads(metadata_path.read_text())

    if algorithm is None:
        if "algorithm" not in metadata_data:
            raise click.UsageError(
                f"no algorithm specified and no metadata found in {metadata_path}"
            )
        algorithm = metadata_data["algorithm"]

    if not algorithm:
        raise click.UsageError("no algorithm specified")

    parameters = {**metadata_data.get("parameters", {}), **parameters}

    converter = _build_converter(algorithm, parameters)
    image = converter.decode(ConvertedImage(sound, metadata_data.get("metadata", {})))

    if not isinstance(image, Image.Image):
        raise click.UsageError(f"converter returned invalid result: {image}")

    if image.mode != "RGB":
        image = image.convert("RGB")

    was_rotated = metadata_data.get("rotate", False)
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
    output_format: str | None = None,
    metadata: Path | None = None,
    metadata_out: Path | None = None,
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
            metadata_out=metadata_out,
        )

    if is_sound_file(file):
        return _sound_to_image(
            file,
            algorithm=algorithm,
            parameters=parameter_dict,
            quality=quality,
            output=output,
            force=force,
            output_format=output_format,
            metadata=metadata,
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
    "--format",
    "output_format",
    type=click.Choice(list(OUTPUT_IMAGE_FORMATS), case_sensitive=False),
    default=None,
    help="Output image format (sound -> image only).",
)
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
    help="Output file or directory.",
    default=None,
)
@click.option(
    "--metadata",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help="Metadata JSON file to use for sound -> image conversion.",
    default=None,
)
@click.option(
    "--metadata-out",
    type=click.Path(file_okay=True, dir_okay=True, writable=True, path_type=Path),
    help="Metadata JSON output path for image -> sound conversion.",
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
    files_list = list(files)

    output = kwargs.get("output")
    metadata = kwargs.get("metadata")
    metadata_out = kwargs.get("metadata_out")

    multi = len(files_list) > 1 or n_times > 1

    if output is not None and multi:
        kwargs["output"] = _ensure_dir(output, "--output")

    if metadata is not None:
        if len(files_list) != 1:
            raise click.UsageError("--metadata can only be used with a single sound file")
        if n_times != 1:
            raise click.UsageError("--metadata cannot be used with --n-times")
        if any(not is_sound_file(f) for f in files_list):
            raise click.UsageError("--metadata can only be used when converting sound to image")

    if metadata_out is not None:
        if any(not is_image_file(f) for f in files_list):
            raise click.UsageError("--metadata-out can only be used when converting image to sound")

        if multi and not _is_dir_path(metadata_out):
            raise click.UsageError(
                "--metadata-out must be a directory when converting multiple files or using --n-times"
            )

        if multi:
            kwargs["metadata_out"] = _ensure_dir(metadata_out, "--metadata-out")
        elif not metadata_out.exists() and metadata_out.suffix == "":
            metadata_out.mkdir(parents=True, exist_ok=True)

    for file in files_list:
        for _ in range(n_times):
            file = _convert_command(file, **kwargs)
