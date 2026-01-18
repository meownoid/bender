from PIL import Image


class Editor:
    def edit(self, images: list[Image.Image]) -> Image.Image:
        raise NotImplementedError(
            f"edit is not implemented in {self.__class__.__name__}"
        )


class OneToOneEditor(Editor):
    def edit(self, images: list[Image.Image]) -> Image.Image:
        if not images:
            raise ValueError("No input images provided")
        if len(images) > 1:
            raise ValueError(
                "Multiple input images provided: this editor accepts a single image"
            )
        return self._edit(images[0])

    def _edit(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError(
            f"_edit is not implemented in {self.__class__.__name__}"
        )
