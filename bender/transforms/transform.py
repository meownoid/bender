from typing import Any

from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


class Transform:
    """
    Image to WAV transform interface.
    """

    def image_to_wav(
        self, input_path: str, output_path: str, transpose: bool = False
    ) -> dict[str, Any]:
        """
        Read image in any format from `input_path` and write WAV file to `output_path`, returning any data which
        should be written to the metadata file.
        """
        raise NotImplementedError()

    def wav_to_image(
        self, input_path: str, data: dict[str, Any], output_path: str
    ) -> None:
        """
        Read WAV file from `input_path` and write image in any format to `output_path`. The `data` parameter contains
        any data which was returned by `image_to_wav`.
        """
        raise NotImplementedError()
