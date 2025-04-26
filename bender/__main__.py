import click

from bender.cli.monitor import monitor_command
from bender.cli.convert import convert_command


@click.group()
def main():
    pass


main.add_command(convert_command)
main.add_command(monitor_command)


if __name__ == "__main__":
    main()
