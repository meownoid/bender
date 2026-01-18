from bender.cli.autocomplete_data import AUTOCOMPLETE


def filter_prefix(prefix: str, xs: list[str]) -> list[str]:
    """
    Filter a list of strings to only include those that start with the given prefix.

    :param prefix: The prefix to filter by.
    :param xs: The list of strings to filter.
    :return: A list of strings that start with the given prefix.
    """
    return [x for x in xs if x.startswith(prefix)]


def autocomplete(ctx, param, value):
    """Autocomplete based on pre-computed dictionary of algorithms and parameters."""
    if ctx.command is None:
        return []

    subcommand = AUTOCOMPLETE.get(ctx.command.name, {})

    if param.name == "algorithm":
        return filter_prefix(value, list(subcommand.keys()))

    if param.name == "parameters":
        algorithm = ctx.params.get("algorithm")

        if algorithm not in subcommand:
            return []

        return filter_prefix(value, subcommand[algorithm])

    return []
