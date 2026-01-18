# Copilot Coding Agent: Onboarding Instructions for this Repo

Welcome! This guide gives you the minimum you need to build, test, lint, and ship changes reliably in this repository.

## What this repo is
- Purpose: "Data bending" toolkit that converts images to sound and back, applies image editors and audio processors, and exposes CLI commands.
- Tech: uv, Python 3.12, CLI via click, image via Pillow, audio via librosa + soundfile, numerical ops via numpy/numexpr/numba. File watching via watchdog.
- Package layout: installable as `bender`, with CLI entry `bender` routing to subcommands: convert, edit, monitor, process.
- Size: Small Python library + CLI, ~100 files, tests included. No compiled extensions.

## Project layout and key files
- Root files: `pyproject.toml` (deps, test config, CLI entry), `uv.lock` (locked deps), `.pre-commit-config.yaml` (lint/type), `README.md` (usage), `generate_autocomplete.py` (rebuild CLI completion data), `.gitignore`.
- Library code: `bender/`
  - `__main__.py` (click group/entry), `converter.py`, `editor.py`, `processor.py`, `parameter.py`, `modulation.py`, `sound.py`, `utils.py`, `entity.py`.
  - Algorithms live under subpackages:
    - Converters: `bender/converters/`.
    - Editors: `bender/editors/`.
    - Processors: `bender/processors/`.
  - CLI: `bender/cli/` (subcommands; autocomplete uses generated `autocomplete_data.py`).
- Tests: `tests/` with unit tests for core modules and algorithms; PyTest config is in `pyproject.toml`.
- Configs: no GitHub Actions configured; local validation is via tests and pre-commit.

## Environment and tools
- Python: 3.12 (required; see `pyproject.toml` requires-python ">=3.12,<4").
- Package manager: uv. Use only it to manage dependencies and run commands.
- Linters/formatters/types: ruff (lint+format), mypy (type-check; numpy plugin), all driven by pre-commit.

## Preconditions and tips
- If you add new CLI algorithms, regenerate autocomplete: `uv run python generate_autocomplete.py` (updates `bender/cli/autocomplete_data.py`). Commit the generated file.
- Pillow may warn about truncated images; this is handled (see converters like BMP using `ImageFile.LOAD_TRUNCATED_IMAGES = True`).
- librosa/soundfile read/write require valid audio file paths; tests use temp files.

## Common commands (zsh/macOS)
- Bootstrap once per clone:
  - `uv sync --dev`
- Validate a change:
  - `uv run pytest -q`
  - `uvx pre-commit run -a`
- Regenerate CLI autocomplete data:
  - `uv run python generate_autocomplete.py`
- Try the CLI:
  - `uv run bender convert --list`

## Validation details and gotchas
- Tests: Use `uv run pytest -q`. PyTest warnings are filtered via `pyproject.toml` to ignore deprecations.
- Pre-commit: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-added-large-files`, `ruff` (with `--fix` and import sort), `ruff-format`, `mypy` (with numpy plugin). If `pre-commit run -a` changes files, stage and re-run.
- Type checking: mypy respects the numpy typing plugin configured in `pyproject.toml`.

## Architectural notes to orient changes
- Entities and discovery: New algorithms are declared with `@entity(name, description, parameters)` on a subclass of `Converter`, `Editor`, or `Processor`. They’re discovered via `bender.cli.utils.import_entities`, which imports all modules in the corresponding package and indexes by `Entity.name`.
- Parameters: Use `Parameter` subclasses in `bender/parameter.py` to define CLI-exposed parameters with parsing, defaults, required flags, and traits. `build_parameters` wires CLI strings into typed constructor args.
- Sound abstraction: `bender/sound.py` holds stereo arrays and sample rate, provides `resample`, `process`, `save`, `load`. Uses librosa for resampling and reading; soundfile for writing; numpy arrays for data.
- CLI: `bender/__main__.py` registers subcommands from `bender/cli/*.py`. `convert` can infer direction based on file extension and uses metadata JSON to round-trip image parameters.
- File-type helpers and Click param types live in `bender/cli/utils.py`.

## CI and local checks before PR
- There is no CI in this repo. Your PR should at least pass locally:
  - `uv sync --dev`
  - `uv run pytest -q`
  - `uvx pre-commit run -a`
  - If you changed algorithms or params, run `uv run python generate_autocomplete.py` and commit changes.

## Trust these instructions
Follow these steps as-is. Only search the repo if something here fails or is unclear. If you discover inaccuracies, update this file in your PR with the corrected steps.
