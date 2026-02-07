import sys

import click

from bender.cli.convert import convert_command
from bender.cli.edit import edit_command
from bender.cli.monitor import monitor_command
from bender.cli.process import process_command


def _split_parameter_assignment(value: str) -> tuple[str, str] | None:
    if "=" not in value:
        return None

    key, val = value.split("=", 1)
    if not key:
        return None

    return key, val


def _expand_parameter_equals(args: list[str]) -> list[str]:
    expanded: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ("-p", "--parameter"):
            if i + 1 < len(args):
                split = _split_parameter_assignment(args[i + 1])
                if split is not None:
                    key, val = split
                    expanded.extend([arg, key, val])
                    i += 2
                    continue

        if arg.startswith("--parameter="):
            split = _split_parameter_assignment(arg.split("=", 1)[1])
            if split is not None:
                key, val = split
                expanded.extend(["--parameter", key, val])
                i += 1
                continue

        expanded.append(arg)
        i += 1

    return expanded


@click.group()
def cli():
    pass


cli.add_command(convert_command)
cli.add_command(monitor_command)
cli.add_command(edit_command)
cli.add_command(process_command)


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else list(argv)
    cli.main(args=_expand_parameter_equals(args))


if __name__ == "__main__":
    main()
