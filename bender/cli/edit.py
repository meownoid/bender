import secrets
from pathlib import Path
from typing import Any, Iterable

import click
from PIL import Image, ImageOps

from bender.cli.autocomplete import autocomplete
from bender.cli.utils import (
    import_entities,
    is_image_file,
    parameters_to_dict,
)
from bender.editor import Editor


def _build_editor(
    algorithm: str,
    parameters: dict[str, Any],
) -> Editor:
    editor_entities = import_entities(Editor, "bender.editors")

    if algorithm not in editor_entities:
        raise click.UsageError(
            f"unknown editor {algorithm}, available: {', '.join(editor_entities)}"
        )

    try:
        return editor_entities[algorithm].build(parameters)
    except ValueError as err:
        raise click.UsageError(*err.args)


def _list_editors(ctx, _, value) -> None:
    if not value:
        return

    for t in import_entities(Editor, "bender.editors").values():
        click.echo(t.get_usage())

    ctx.exit()


def _edit_command(
    files: list[Path],
    algorithm: str,
    parameters: list[tuple[str, str]] | None = None,
    quality: int = 95,
    output: Path | None = None,
    force: bool = False,
) -> Path:
    if parameters is None:
        parameters = []

    parameter_dict = parameters_to_dict(parameters)

    images = []
    for file in files:
        if not is_image_file(file):
            raise click.UsageError(f"{file}: not an image file")

        click.echo(f"Loading {file}")
        image = Image.open(file)

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = ImageOps.exif_transpose(image)
        images.append(image)

    if not images:
        raise click.UsageError("No input images provided")

    editor = _build_editor(algorithm, parameter_dict)
    click.echo(
        f"Editing {len(images)} image{'s' if len(images) > 1 else ''} with algorithm '{algorithm}'"
    )
    try:
        result = editor.edit(images)
    except ValueError as err:
        raise click.UsageError(str(err))

    if not isinstance(result, Image.Image):
        raise click.UsageError(f"Editor returned invalid result: {result}")

    # Determine output path
    first_input = files[0]
    default_name = f"{first_input.stem}-processed-{secrets.token_hex(4)}.jpg"

    if output is None:
        output_path = Path.cwd() / default_name
    elif output.is_dir():
        output_path = output / default_name
    else:
        output_path = output

    if result.mode != "RGB":
        result = result.convert("RGB")

    if not force and output_path.exists():
        raise click.UsageError(f"{output_path} already exists, use -f to overwrite")

    click.echo(f"Saving {output_path}")
    result.save(output_path, quality=quality)

    return output_path


@click.command(
    "edit",
    help="Edit image(s) using a specified algorithm.",
)
@click.argument("files", type=click.Path(exists=True, path_type=Path), nargs=-1)
@click.option(
    "-a",
    "--algorithm",
    type=str,
    help="Algorithm to use for editing.",
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
    "-q",
    "--quality",
    type=click.IntRange(0, 100, clamp=True),
    default=95,
    help="Output image quality.",
)
@click.option(
    "-f", "--force", is_flag=True, default=False, help="Overwrite existing files."
)
@click.option(
    "--list",
    is_flag=True,
    help="List all available editors and exit.",
    callback=_list_editors,
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
def edit_command(files: Iterable[Path], **kwargs) -> None:
    _edit_command(list(files), **kwargs)
