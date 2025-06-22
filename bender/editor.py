from PIL import Image

from bender.utils import make_unique_output_path


class Editor:
    def edit(self, images: list[Image.Image]) -> list[Image.Image]:
        raise NotImplementedError(
            f"edit is not implemented in {self.__class__.__name__}"
        )


class OneToOneEditor(Editor):
    def edit(self, images: list[Image.Image]) -> list[Image.Image]:
        output = []
        for image in images:
            result = self._edit(image)
            if result.filename is None or result.filename == image.filename:
                filename = image.filename if image.filename is not None else "edited"
                result = result.with_filename(make_unique_output_path(filename, ".jpg"))
            output.append(result)

        return output

    def _edit(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError(
            f"_edit is not implemented in {self.__class__.__name__}"
        )


class OneToManyEditor(Editor):
    def edit(self, images: list[Image.Image]) -> list[Image.Image]:
        output = []
        for image in images:
            results = self._edit(image)
            for i, result in enumerate(results):
                if result.filename is None or result.filename == image.filename:
                    filename = (
                        image.filename if image.filename is not None else "edited"
                    )
                    result = result.with_filename(
                        make_unique_output_path(filename, ".jpg", i)
                    )
                output.append(result)

        return output

    def _edit(self, image: Image.Image) -> list[Image.Image]:
        raise NotImplementedError(
            f"_edit is not implemented in {self.__class__.__name__}"
        )
