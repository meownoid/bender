import json
import tempfile
from pathlib import Path

from PIL import Image

from bender.cli.convert import _convert_command


def test_rotate():
    # Create a simple test image
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create a simple rectangular image (wider than tall) to see rotation effect
        test_image = Image.new("RGB", (100, 50), color="red")
        test_image_path = tmp_path / "test.jpg"
        test_image.save(test_image_path)

        # Convert image to sound with rotation
        sound_path = _convert_command(
            file=test_image_path,
            algorithm="bmp",
            parameters=[],
            bit_depth=16,
            output=tmp_path,
            force=True,
            rotate=True,
        )

        metadata_path = sound_path.with_suffix(".json")
        assert metadata_path.exists()

        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata.get("rotate", False), "Rotate flag not saved in metadata"

        restored_image_path = _convert_command(
            file=sound_path,
            algorithm=None,
            parameters=[],
            quality=95,
            output=tmp_path,
            force=True,
            rotate=False,
        )

        restored_image = Image.open(restored_image_path)

        assert restored_image.size == test_image.size
