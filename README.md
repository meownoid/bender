# bender

Data bending toolkit. Transforms images to sound and back. Applies various DSP effects.

## Installation

```bash
git clone https://github.com/meownoid/bender.git
cd bender
uv tool install .
```

## Usage

### Transforming images to sound and back

Transform image to sound:
```bash
bender transform image.jpg
```

This will create `image-default.wav` and `image-default.json` files using the default algorithm. Second file is needed for reverse transformation.

You can specify the output file name:
```bash
bender transform image.jpg -o image.wav
```

Transform sound to image:
```bash
bender transform image-default-processed.wav
```

Corresponding `json` file with the longest matching prefix will be selected automatically.

To show all available algorithms and their parameters:
```bash
bender transform --list
```

To use specific algorithm and parameters:
```bash
bender transform image.jpg -a bmp -p scale=true -p stereo=false
```

### Monitor processed sound files

To automatically monitor and process sound files with the given prefix:
```bash
bender monitor image-default-processed
```

### Process sound files

To process sound file:
```bash
bender process -a gain -p gain=1.5 sound.wav
```

To list all available algorithms and their parameters:
```bash
bender process --list
```

Some algorithms require several inputs:
```bash
bender process -a mix -p gain-1=0.3 -p gain-2=0.7  source-1.wav source-2.wav
```

### Edit images

To edit image:
 ```bash
 bender edit -a fragments -p n=100 image.jpg
 ```
