from pathlib import Path
from typing import Any, Iterable, List

import click
from PIL import Image

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
    files: List[Path],
    algorithm: str,
    parameters: list[tuple[str, str]] | None = None,
    quality: int = 95,
    output: Path | None = None,
    force: bool = False,
) -> Path:
    if parameters is None:
        parameters = []

    parameter_dict = parameters_to_dict(parameters)

    if output is None:
        output = Path.cwd() / "edited.jpg"
    elif output.is_dir():
        output = output / "edited.jpg"

    if not force and output.exists():
        raise click.UsageError(f"{output} already exists, use -f to overwrite")

    images = []
    for file in files:
        if not is_image_file(file):
            raise click.UsageError(f"{file}: not an image file")

        click.echo(f"Loading {file}")
        image = Image.open(file)
        if image.mode != "RGB":
            image = image.convert("RGB")
        images.append(image)

    if not images:
        raise click.UsageError("No input images provided")

    editor = _build_editor(algorithm, parameter_dict)
    click.echo(f"Editing {len(images)} images with algorithm '{algorithm}'")
    result = editor.edit(images)

    click.echo(f"Saving result to {output}")
    result.save(output, quality=quality)

    return output


@click.command(
    "edit",
    help="Edit and combine multiple images into one.",
)
@click.argument("files", type=click.Path(exists=True, path_type=Path), nargs=-1)
@click.option(
    "-a",
    "--algorithm",
    type=str,
    help="Algorithm to use for editing.",
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
