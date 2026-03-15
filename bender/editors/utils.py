import struct
from enum import StrEnum
from io import BytesIO
from typing import Final

import numpy as np
from PIL import Image, ImageCms

UINT8_MAX: Final[float] = 255.0
UINT8_INV: Final[float] = 1.0 / UINT8_MAX
LUMA_WEIGHTS: Final[np.ndarray] = np.array([0.299, 0.587, 0.114], dtype=np.float32)
DEFAULT_DITHER_SEED: Final[int] = 0
_ICC_TAG_TABLE_OFFSET: Final[int] = 128
_ICC_TAG_ENTRY_SIZE: Final[int] = 12
_ICC_TAG_RTRC: Final[bytes] = b"rTRC"
_ICC_TAG_GTRC: Final[bytes] = b"gTRC"
_ICC_TAG_BTRC: Final[bytes] = b"bTRC"
_ICC_LINEAR_TRC_SIZE: Final[int] = 32


def _fixed_16_16(value: float) -> bytes:
    return struct.pack(">i", int(round(value * 65536.0)))


def _build_linear_trc_tag() -> bytes:
    # ICC parametric curve type 3: Y = (aX + b)^g for X >= d, cX otherwise.
    # Choosing g=1, a=1, b=0, c=1, d=0 yields an identity transfer curve.
    payload = bytearray(_ICC_LINEAR_TRC_SIZE)
    payload[0:4] = b"para"
    payload[8:10] = struct.pack(">H", 3)
    payload[12:16] = _fixed_16_16(1.0)  # g
    payload[16:20] = _fixed_16_16(1.0)  # a
    payload[20:24] = _fixed_16_16(0.0)  # b
    payload[24:28] = _fixed_16_16(1.0)  # c
    payload[28:32] = _fixed_16_16(0.0)  # d
    return bytes(payload)


def _build_linear_srgb_profile() -> ImageCms.ImageCmsProfile:
    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    profile_bytes = bytearray(srgb_profile.tobytes())
    tag_count = struct.unpack(
        ">I", profile_bytes[_ICC_TAG_TABLE_OFFSET : _ICC_TAG_TABLE_OFFSET + 4]
    )[0]
    trc_tag = _build_linear_trc_tag()

    table_pos = _ICC_TAG_TABLE_OFFSET + 4
    for _ in range(tag_count):
        tag_sig = bytes(profile_bytes[table_pos : table_pos + 4])
        tag_offset = struct.unpack(">I", profile_bytes[table_pos + 4 : table_pos + 8])[0]
        tag_size = struct.unpack(">I", profile_bytes[table_pos + 8 : table_pos + 12])[0]
        if (
            tag_sig in {_ICC_TAG_RTRC, _ICC_TAG_GTRC, _ICC_TAG_BTRC}
            and tag_size >= _ICC_LINEAR_TRC_SIZE
        ):
            profile_bytes[tag_offset : tag_offset + _ICC_LINEAR_TRC_SIZE] = trc_tag
        table_pos += _ICC_TAG_ENTRY_SIZE

    return ImageCms.ImageCmsProfile(BytesIO(bytes(profile_bytes)))


_SRGB_PROFILE: Final[ImageCms.ImageCmsProfile] = ImageCms.ImageCmsProfile(
    ImageCms.createProfile("sRGB")
)
_LINEAR_SRGB_PROFILE: Final[ImageCms.ImageCmsProfile] = _build_linear_srgb_profile()
_SRGB_TO_LINEAR_TRANSFORM: Final[ImageCms.ImageCmsTransform] = (
    ImageCms.buildTransformFromOpenProfiles(
        _SRGB_PROFILE,
        _LINEAR_SRGB_PROFILE,
        "RGB",
        "RGB",
    )
)
_LINEAR_TO_SRGB_TRANSFORM: Final[ImageCms.ImageCmsTransform] = (
    ImageCms.buildTransformFromOpenProfiles(
        _LINEAR_SRGB_PROFILE,
        _SRGB_PROFILE,
        "RGB",
        "RGB",
    )
)


class BlendMode(StrEnum):
    SCREEN = "screen"
    ADD = "add"


def image_to_float_rgb(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"), dtype=np.float32) * UINT8_INV


def float_rgb_to_uint8(rgb: np.ndarray) -> np.ndarray:
    return np.clip(rgb * UINT8_MAX + 0.5, 0.0, UINT8_MAX).astype(np.uint8)


def float_rgb_to_image(rgb: np.ndarray) -> Image.Image:
    return Image.fromarray(float_rgb_to_uint8(rgb), mode="RGB")


def rgb_to_luminance(rgb: np.ndarray) -> np.ndarray:
    return (
        rgb[:, :, 0] * LUMA_WEIGHTS[0]
        + rgb[:, :, 1] * LUMA_WEIGHTS[1]
        + rgb[:, :, 2] * LUMA_WEIGHTS[2]
    ).astype(np.float32)


def _to_srgb_image(image: Image.Image) -> Image.Image:
    rgb_image = image.convert("RGB")
    source_icc = image.info.get("icc_profile")
    if source_icc is None:
        return rgb_image
    try:
        source_profile = ImageCms.ImageCmsProfile(BytesIO(source_icc))
        return ImageCms.profileToProfile(
            rgb_image,
            source_profile,
            _SRGB_PROFILE,
            outputMode="RGB",
        )
    except (OSError, ImageCms.PyCMSError):
        return rgb_image


def image_to_linear_rgb(image: Image.Image) -> np.ndarray:
    srgb_image = _to_srgb_image(image)
    linear_image = ImageCms.applyTransform(srgb_image, _SRGB_TO_LINEAR_TRANSFORM)
    return image_to_float_rgb(linear_image)


def linear_rgb_to_image(linear_rgb: np.ndarray) -> Image.Image:
    linear_rgb = np.asarray(linear_rgb, dtype=np.float32)
    linear_rgb = np.nan_to_num(linear_rgb, nan=0.0, posinf=0.0, neginf=0.0)
    linear_image = float_rgb_to_image(np.clip(linear_rgb, 0.0, 1.0))
    return ImageCms.applyTransform(linear_image, _LINEAR_TO_SRGB_TRANSFORM)


def apply_noise_dither(rgb: np.ndarray, seed: int = DEFAULT_DITHER_SEED) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float32)
    rng = np.random.default_rng(seed)
    dither = (rng.random(rgb.shape[:2], dtype=np.float32) - 0.5) * UINT8_INV
    return rgb + dither[:, :, None]


def blend(
    base: np.ndarray,
    bloom_color: np.ndarray,
    blend_mode: BlendMode,
) -> np.ndarray:
    match blend_mode:
        case BlendMode.ADD:
            return base + bloom_color
        case BlendMode.SCREEN:
            return 1.0 - (1.0 - base) * (1.0 - bloom_color)
        case _:
            return base
