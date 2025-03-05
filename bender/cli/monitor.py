import time
from pathlib import Path
from typing import Callable, Any

import click
from watchdog.events import (
    DirModifiedEvent,
    FileModifiedEvent,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer

from bender.cli.transform import transform_options, _transform_command
from bender.cli.utils import add_options, is_image_file, is_sound_file


class WatchdogEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns: list[str], callback: Callable[[str], None]):
        super().__init__(
            patterns=patterns, ignore_directories=True, case_sensitive=False
        )
        self.callback = callback

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if not isinstance(event, FileModifiedEvent):
            return

        if not is_image_file(event.src_path) and not is_sound_file(event.src_path):
            return

        self.callback(event.src_path)


@click.command(
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

        click.echo(f"Transforming {path}")

        try:
            result_path = _transform_command(path, **kwargs)
        except Exception as e:
            click.echo(f"Error transforming {path}: {e}")
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
