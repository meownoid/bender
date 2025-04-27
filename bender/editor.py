from typing import List

from PIL import Image


class Editor:
    def edit(self, images: List[Image.Image]) -> Image.Image:
        raise NotImplementedError(
            f"edit is not implemented in {self.__class__.__name__}"
        )
