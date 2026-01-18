import time
from pathlib import Path
from typing import Any, Callable

import click
from watchdog.events import (
    DirModifiedEvent,
    FileModifiedEvent,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer

from bender.cli.convert import _convert_command, converter_shared_options
from bender.cli.utils import add_options, is_image_file, is_sound_file
from bender.utils import bytes_to_str


class WatchdogEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns: list[str], callback: Callable[[str], None]):
        super().__init__(
            patterns=patterns, ignore_directories=True, case_sensitive=False
        )
        self.callback = callback

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if not isinstance(event, FileModifiedEvent):
            return

        src_path = bytes_to_str(event.src_path)

        if not is_image_file(src_path) and not is_sound_file(src_path):
            return

        self.callback(src_path)


@click.command(
    "monitor", help="Automatically convert sound files with a given pattern."
)
@click.argument("patterns", nargs=-1)
@add_options(converter_shared_options)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="Automatically open converted files.",
)
@click.option(
    "-o",
    "--open",
    "auto_open",
    is_flag=True,
    default=False,
    help="Automatically open converted files.",
)
def monitor_command(
    patterns: list[str],
    recursive: bool = False,
    auto_open: bool = False,
    **kwargs: Any,
) -> None:
    processing_results = set()

    def callback(path_str: str) -> None:
        nonlocal processing_results

        path = Path(path_str)

        # avoid recursive processing
        if path in processing_results:
            return

        click.echo(f"Converting {path}")

        try:
            result_path = _convert_command(path, **kwargs)
        except Exception as e:
            click.echo(f"Error converting {path}: {e}")
            return

        processing_results.add(result_path)

        if not auto_open:
            return

        click.echo(f"Opening {result_path}")
        click.launch(str(result_path.absolute()), wait=False, locate=False)

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
