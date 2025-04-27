import itertools

from PIL import Image


class Editor:
    def edit(self, images: list[Image.Image]) -> list[Image.Image]:
        raise NotImplementedError(
            f"edit is not implemented in {self.__class__.__name__}"
        )


class SingleImageEditor(Editor):
    def edit(self, images: list[Image.Image]) -> list[Image.Image]:
        return list(
            itertools.chain.from_iterable(self._edit(image) for image in images)
        )

    def _edit(self, image: Image.Image) -> list[Image.Image]:
        raise NotImplementedError(
            f"_edit is not implemented in {self.__class__.__name__}"
        )
