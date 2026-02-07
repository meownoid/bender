<p align="center"><img src=".github/logo.jpg" width="600" height="200"></p>

An image-bending tool that transforms images to sound and back.

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```bash
git clone https://github.com/meownoid/bender.git
cd bender
uv tool install --reinstall .
```

(Optional) Enable autocompletion by generating a completion script and sourcing it in your shell configuration:

```bash
_BENDER_COMPLETE=zsh_source bender > ~/.zshrc.d/bender-complete.zsh
```

## Usage

### Convert image to sound

```bash
bender convert image.jpg
```

This creates `image-xxxx.wav` and `image-xxxx.json` files using the default algorithm. The `.json` file contains metadata for reverse conversion.

Specify the output file name:

```bash
bender convert image.jpg -o image.wav
```

When converting multiple files or using `--n-times`, `--output` must be a directory (it will be created if it does not exist).

Write the metadata JSON to a specific location:

```bash
bender convert image.jpg --metadata-out ./metadata
```

### Convert processed sound back to an image

```bash
bender convert image-xxxx-processed.wav
```

The corresponding `.json` file with the longest matching prefix is selected automatically.

Use an explicit metadata file instead of auto-detection:

```bash
bender convert image-xxxx-processed.wav --metadata image-xxxx.json
```

### List available algorithms and parameters

```bash
bender convert --list
```

### Use specific algorithm and parameters

```bash
bender convert -a bmp -p sample_size 1 image.jpg
```

You can also pass parameters as `key=value`:

```bash
bender convert -a bmp -p sample_size=1 image.jpg
```

### Edit images

```bash
bender edit -a split_channels input.jpg
```

When multiple images are provided, the editor receives all inputs and produces a single output file.

### Process sounds

```bash
bender process -a delay input.wav
```

When multiple sounds are provided, the processor receives all inputs and produces a single output file.

### Monitor and convert matching files

When experimenting, it might be useful to automatically convert new files as they appear.

```bash
bender monitor 'image-*.wav'
```

This command converts new sound files with the prefix `image-` back to images. Use quotes to prevent shell expansion of the pattern.
