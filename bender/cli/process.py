import os
import secrets
from pathlib import Path
from typing import Any, Iterable

import click

from bender.cli.utils import (
    import_entities,
    is_sound_file,
    parameters_to_dict,
)
from bender.processor import Processor
from bender.sound import Sound


def _build_processor(
    algorithm: str,
    parameters: dict[str, Any],
) -> Processor:
    processor_entities = import_entities(Processor, "bender.processors")

    if algorithm not in processor_entities:
        raise click.UsageError(
            f"unknown processor {algorithm}, available: {', '.join(processor_entities)}"
        )

    try:
        return processor_entities[algorithm].build(parameters)
    except ValueError as err:
        raise click.UsageError(*err.args)


def _list_processors(ctx, _, value) -> None:
    if not value:
        return

    for t in import_entities(Processor, "bender.processors").values():
        click.echo(t.get_usage())

    ctx.exit()


def _process_command(
    files: list[Path],
    algorithm: str,
    parameters: list[tuple[str, str]] | None = None,
    bit_depth: int = 16,
    output: Path | None = None,
    force: bool = False,
) -> Path:
    if parameters is None:
        parameters = []

    parameter_dict = parameters_to_dict(parameters)

    sounds = []
    for file in files:
        if not is_sound_file(file):
            raise click.UsageError(f"{file}: not a sound file")

        click.echo(f"Loading {file}")
        sound = Sound.load(file)

        sounds.append(sound)

    if not sounds:
        raise click.UsageError("No input sounds provided")

    processor = _build_processor(algorithm, parameter_dict)
    click.echo(
        f"Processing {len(sounds)} sound{'s' if len(sounds) > 1 else ''} with algorithm '{algorithm}'"
    )
    results = processor.process(sounds)

    if output is None:
        output = Path.cwd()

    if output is not None and output.is_file() and len(results) > 1:
        raise click.UsageError(
            f"{output} is not a directory, but multiple sounds were returned"
        )

    for result in results:
        if not isinstance(result, Sound):
            raise click.UsageError(f"Processor returned invalid result: {result}")

        if result.filename is None:
            filename = f"processed-{secrets.token_hex(4)}.wav"
        else:
            filename = os.path.basename(result.filename)

        if output.is_dir():
            output_path = output / filename
        else:
            output_path = output

        if not force and output_path.exists():
            raise click.UsageError(f"{output_path} already exists, use -f to overwrite")

        # Change extension to .wav
        filename = f"{Path(filename).stem}.wav"

        click.echo(f"Saving {output_path}")
        result.save(output_path, bit_depth=bit_depth)

    return output


@click.command(
    "process",
    help="Process sound(s) using a specified algorithm.",
)
@click.argument("files", type=click.Path(exists=True, path_type=Path), nargs=-1)
@click.option(
    "-a",
    "--algorithm",
    type=str,
    help="Algorithm to use for processing.",
    required=True,
)
@click.option(
    "-p",
    "--parameter",
    "parameters",
    type=(str, str),
    multiple=True,
    help="Algorithm parameters.",
)
@click.option(
    "-b",
    "--bit-depth",
    type=click.Choice(["8", "16", "24", "32"]),
    default="16",
    help="Output bit depth.",
    callback=lambda _, __, v: int(v) if v else 16,
)
@click.option(
    "-f", "--force", is_flag=True, default=False, help="Overwrite existing files."
)
@click.option(
    "--list",
    is_flag=True,
    help="List all available processors and exit.",
    callback=_list_processors,
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
def process_command(files: Iterable[Path], **kwargs) -> None:
    _process_command(list(files), **kwargs)
