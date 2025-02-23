from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Sound:
    left: np.array
    right: np.array
    sample_rate: int
