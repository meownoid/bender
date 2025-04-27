# bender

Data bending tool. Transforms images to sound and back.

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```bash
git clone https://github.com/meownoid/bender.git
cd bender
uv tool install --reinstall .
```

(Optional) Enable autocompletion by generating a completion script and sourcing it in your shell configuration. For bash, replace `zsh` with `bash`:

```bash
_BENDER_COMPLETE=zsh_source bender > ~/.zshrc.d/bender-complete.zsh
```

## Usage

### Convert Images to Sound and Back

#### Convert Image to Sound

```bash
bender convert image.jpg
```

This creates `image-xxxx.wav` and `image-xxxx.json` files using the default algorithm. The `.json` file contains metadata for reverse conversion.

Specify the output file name:

```bash
bender convert image.jpg -o image.wav
```

#### Convert Sound to Image

```bash
bender convert image-xxxx-processed.wav
```

The corresponding `.json` file with the longest matching prefix is selected automatically.

#### List Available Algorithms and Parameters

```bash
bender convert --list
```

#### Use Specific Algorithm and Parameters

```bash
bender convert -a bmp -p sample_size 1 image.jpg
```

### Monitor Converted Sound Files

#### Monitor and Convert Matching Sound Files

```bash
bender monitor 'image1-*.wav'
```

Automatically converts new sound files with the prefix `image1-` or `image2-` back to images. Use quotes to prevent shell expansion of the pattern.

#### Monitor All Sound Files and Open Results

```bash
bender monitor -o '*.wav'
```

### Edit Images

#### Apply Editing Algorithms

```bash
bender edit -a split_channels image.jpg
```

This creates three output images, one per channel. Different algorithms may produce varying numbers of inputs and outputs.

#### List Available Image Editors and Parameters

```bash
bender edit --list
```

#### Set Specific Parameters and Quality

```bash
bender edit -a split_channels -p mode CMYK -q 90 image.jpg
```

#### Process Multiple Images

If the algorithm requires one input image, it can process multiple images independently:

```bash
bender edit -a split_channels image1.jpg image2.jpg
```

### Process Sound Files with Audio Effects

#### Apply Processing Algorithms

```bash
bender process -a distortion sound.wav
```

Different algorithms may produce varying numbers of inputs and outputs.

#### List Available Sound Processors and Parameters

```bash
bender process --list
```

#### Set Specific Parameters and Bit Depth

```bash
bender process -a distortion -p gain 2.5 -b 24 sound.wav
```

#### Process Multiple Sound Files

Most algorithms can process multiple sound files at once:

```bash
bender process -a distortion sound1.wav sound2.wav
```
