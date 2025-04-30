from bender.cli.autocomplete_data import AUTOCOMPLETE


def filter_prefix(prefix: str, xs: list[str]) -> list[str]:
    return [x for x in xs if x.startswith(prefix)]


def autocomplete(ctx, param, value):
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
