import click

from bender.cli.convert import convert_command
from bender.cli.edit import edit_command
from bender.cli.monitor import monitor_command
from bender.cli.process import process_command


@click.group()
def main():
    pass


main.add_command(convert_command)
main.add_command(monitor_command)
main.add_command(edit_command)
main.add_command(process_command)


if __name__ == "__main__":
    main()
