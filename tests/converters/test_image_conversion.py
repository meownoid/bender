import numpy as np
from PIL import Image

from bender.converter import Converter
from bender.entity import get_entities


def test_image_conversion():
    # Generate a random solid color image
    width, height = 100, 100
    color = tuple(np.random.randint(0, 256, size=3))
    image = Image.new("RGB", (width, height), color)

    # Discover all available converters
    converters = [entity.build({}) for entity in get_entities(Converter)]

    for converter in converters:
        # Convert image to sound and back
        converted = converter.encode(image)
        result_image = converter.decode(converted)

        # Calculate absolute mean difference
        original_array = np.array(image, dtype=np.float32)
        result_array = np.array(result_image, dtype=np.float32)
        mean_difference = np.abs(original_array - result_array).mean()

        # Assert the mean difference is within the acceptable range
        assert mean_difference <= 5, (
            f"Mean difference {mean_difference} exceeds threshold for {converter.__class__.__name__}"
        )
