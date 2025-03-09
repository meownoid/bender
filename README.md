# bender

Data bending toolkit. Transforms images to sound and back.

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

### Transform images to sound and back

Transform image to sound:

```bash
bender transform image.jpg
```

This will create `image-xxxx.wav` and `image-xxxx.json` files using the default algorithm. Second file contains metadata needed for reverse transformation.

You can specify the output file name:

```bash
bender transform image.jpg -o image.wav
```

Transform sound to image:

```bash
bender transform image-xxxx-processed.wav
```

Corresponding `json` file with the longest matching prefix will be selected automatically.

To show all available algorithms and their parameters:

```bash
bender transform --list
```

To use specific algorithm and parameters:

```bash
bender transform image.jpg -a bmp -p sample_size=16
```

### Monitor processed sound files

To automatically monitor and process sound files matching given patterns:

```bash
bender monitor 'image1-*.wav' 'image2-*.wav'
```

As soon as new sound file with prefix `image1-` or `image2-` appears in the directory, it will be transformed back to image.
Notice the use of quotes to prevent shell from expanding the pattern.

To monitor all sound files in the directory:

```bash
bender monitor '*.wav'
```
