from PIL import Image


class Edit:
    def process(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError(
            f"process is not implemented in {self.__class__.__name__}"
        )
