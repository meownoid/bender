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

### Convert processed sound back to an image

```bash
bender convert image-xxxx-processed.wav
```

The corresponding `.json` file with the longest matching prefix is selected automatically.

### List available algorithms and parameters

```bash
bender convert --list
```

### Use specific algorithm and parameters

```bash
bender convert -a bmp -p sample_size 1 image.jpg
```

### Monitor and convert matching sound files

When experimenting, it might be useful to automatically convert new sound files back to images.

```bash
bender monitor 'image-*.wav'
```

This command converts new sound files with the prefix `image-` back to images. Use quotes to prevent shell expansion of the pattern.
