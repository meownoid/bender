import secrets
from pathlib import Path
from typing import Any, Iterable

import click

from bender.cli.autocomplete import autocomplete
from bender.cli.utils import (
    import_entities,
    is_sound_file,
    parameters_to_dict,
)
from bender.effects import brick_wall_limit
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
    limit: bool = True,
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
    try:
        result = processor.process(sounds)
    except ValueError as err:
        raise click.UsageError(str(err))

    if not isinstance(result, Sound):
        raise click.UsageError(f"Processor returned invalid result: {result}")

    # Determine output path
    first_input = files[0]
    default_name = f"{first_input.stem}-processed-{secrets.token_hex(4)}.wav"

    if output is None:
        output_path = Path.cwd() / default_name
    elif output.is_dir():
        output_path = output / default_name
    else:
        output_path = output

    if limit:
        result = result.process(brick_wall_limit)

    if not force and output_path.exists():
        raise click.UsageError(f"{output_path} already exists, use -f to overwrite")

    click.echo(f"Saving {output_path}")
    result.save(output_path, bit_depth=bit_depth)

    return output_path


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
    shell_complete=autocomplete,
)
@click.option(
    "-p",
    "--parameter",
    "parameters",
    type=(str, str),
    multiple=True,
    help="Algorithm parameters.",
    shell_complete=autocomplete,
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
    "-l",
    "--limit",
    is_flag=True,
    default=False,
    help="Apply brick wall limiter to the result.",
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
