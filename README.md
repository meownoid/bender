# bender

Data bending tool. Transforms images to sound and back.

## Installation

You need to have [uv](https://github.com/astral-sh/uv) installed.

```bash
git clone https://github.com/meownoid/bender.git
cd bender
uv tool install --reinstall  .
```

(Optional) To enable autocompletion, generate completion script and source it from your shell configuration.
If you are using bash, replace `zsh` with `bash`.

```bash
_BENDER_COMPLETE=zsh_source bender > ~/.zshrc.d/bender-complete.zsh
```

## Usage

### Convert images to sound and back

Convert image to sound:

```bash
bender convert image.jpg
```

This will create `image-xxxx.wav` and `image-xxxx.json` files using the default algorithm. Second file contains metadata needed for reverse conversion.

You can specify the output file name:

```bash
bender convert image.jpg -o image.wav
```

Convert sound to image:

```bash
bender convert image-xxxx-processed.wav
```

Corresponding `json` file with the longest matching prefix will be selected automatically.

To show all available algorithms and their parameters:

```bash
bender convert --list
```

To use specific algorithm and parameters:

```bash
bender convert -a bmp -p sample_size 1 image.jpg
```

### Monitor processed sound files

To automatically monitor and process sound files matching given patterns:

```bash
bender monitor 'image1-*.wav'
```

As soon as new sound file with prefix `image1-` or `image2-` appears in the directory, it will be converted back to image.
Notice the use of quotes to prevent shell from expanding the pattern.

To monitor all sound files in the directory and open resulting images after conversion:

```bash
bender monitor -o '*.wav'
```
