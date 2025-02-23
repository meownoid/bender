import time
from pathlib import Path
from typing import Callable, Any

import click
from watchdog.events import (
    DirCreatedEvent,
    FileCreatedEvent,
    DirModifiedEvent,
    FileModifiedEvent,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer

from bender.entity import get_transforms


class MappedChoice(click.Choice):
    def __init__(self, mapping: dict[str, Any], *args, **kwargs):
        super().__init__(list(mapping), *args, **kwargs)
        self.mapping = mapping

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        return self.mapping[value]


class WatchdogEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns: list[str], callback: Callable[[str], None]):
        super().__init__(
            patterns=patterns, ignore_directories=True, case_sensitive=False
        )
        self.callback = callback

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if not isinstance(event, FileCreatedEvent):
            return

        self.callback(event.src_path)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if not isinstance(event, FileModifiedEvent):
            return

        self.callback(event.src_path)


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


transform_options = [
    click.option(
        "-a", "--algorithm", type=str, help="Algorithm to use for transformation."
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
        "-b",
        "--bit-depth",
        type=MappedChoice({"8": 8, "16": 16, "24": 24, "32": 32}),
        default="16",
        help="Output sound file bit depth.",
    ),
]


@click.group()
@click.version_option()
def main():
    pass


def _list_transforms(*_) -> None:
    for t in get_transforms().values():
        click.echo(t.get_usage())


@main.command("transform", help="Convert images to sound and vice versa.")
@click.argument("files", type=click.Path(exists=True), nargs=-1)
@add_options(transform_options)
@click.option(
    "--list", is_flag=True, callback=_list_transforms, expose_value=False, is_eager=True
)
def _transform(
    files: tuple[Path, ...],
    algorithm: str | None = None,
    parameters: tuple[str, str] | None = None,
    quality: int = 95,
    bit_depth: int = 24,
) -> str:
    return "test"


@main.command(
    "monitor", help="Automatically transform sound files with a given pattern."
)
@click.argument("patterns", nargs=-1)
@add_options(transform_options)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="Automatically open transformed files.",
)
@click.option(
    "-o",
    "--open",
    "auto_open",
    is_flag=True,
    default=False,
    help="Automatically open transformed files.",
)
def _monitor(
    patterns: list[str],
    recursive: bool = False,
    auto_open: bool = False,
    **kwargs: Any,
) -> None:
    def callback(path: str) -> None:
        click.echo(f"Transforming {path}")

        result_path = _transform((Path(path),), **kwargs)

        if auto_open:
            click.launch(result_path, wait=False, locate=False)

    event_handler = WatchdogEventHandler(patterns=patterns, callback=callback)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=recursive)

    click.echo("Monitoring directory for changes...")
    click.echo("Press Ctrl+C to stop monitoring.")
    observer.start()
    try:
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            click.echo()
            click.echo("Stopping...")
    finally:
        observer.stop()
        observer.join()

    click.echo("Done.")


@main.command("process", help="Process sound files.")
def _process():
    click.echo("process")


@main.command("edit", help="Edit images.")
def _edit():
    click.echo("edit")


if __name__ == "__main__":
    main()
