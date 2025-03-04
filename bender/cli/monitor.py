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

from bender.cli.transform import transform_options, transform_command
from bender.cli.utils import add_options


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
    def callback(path: str) -> None:
        click.echo(f"Transforming {path}")

        result_paths = transform_command([Path(path)], **kwargs)

        if not auto_open:
            return

        for result_path in result_paths:
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
