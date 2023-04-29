"""

Dependencies
------------
Python
    3.4+ - Shebang execution on Windows through Python Launcher.
    3.4+ - Pathlib library.
    3.2+ - Argparse library.

Pillow Imaging Library

"""

# -- # Imports # ----------------------------------------------------------------------------------------------------- #
# Python
import io
import struct as st

# Libraries
# # Optional content.
try:
    from PIL import Image, UnidentifiedImageError
except ModuleNotFoundError:
    PIL_AVAILABLE = False
else:
    PIL_AVAILABLE = True


# -- # Exceptions # -------------------------------------------------------------------------------------------------- #
class UnpackerError(Exception):
    """Generic Un/packer exception."""


class InvalidDataError(UnpackerError, ValueError):
    """Data does not correspond to the expected type."""


class InvalidSotESResourceError(InvalidDataError):
    """Data does not correspond to a SotES packed bitmap resource."""


class IncompleteSotESResourceError(InvalidSotESResourceError):
    """Data cannot be unpacked into a SotES bitmap resource due to requiring a field that is out of bounds."""


class SotESResourceValidationError(InvalidSotESResourceError):
    """Data fails SotES's internal checks for packed bitmap resources."""


class InvalidBitmapError(InvalidDataError):
    """Data is not a bitmap or does not meet the expected bitmap specifications."""


class UnsupportedDataError(UnpackerError, NotImplementedError):
    """Data is in a valid format, but the Un/packer cannot handle it."""


class UnsupportedBitmapError(UnsupportedDataError):
    """Data is a valid bitmap but SotES and/or the Un/packer cannot handle it."""


class UnsupportedFunctionError(UnpackerError, RuntimeError):
    """The Un/packer cannot do the requested operation due to an external reason."""


# -- # Functions # --------------------------------------------------------------------------------------------------- #
def unpack(resource_data: bytes, additional_checks: bool = True, always_include_palette: bool = False) -> bytes:
    """De-obfuscates a bitmap image from an encrypted SotES image resource, with as little changes as possible to the
    original file.

    Parameters
    ----------
    resource_data : bytes
        The raw binary data of the resource to decrypt.

    additional_checks : bool = False
        SotES does not perform many checks to see if, after unpacking image resources, the bitmaps it gets are valid.

        The Unpacker normally adds additional checks for the bitmaps it obtains, however through this option you ignore
        those errors and obtain the unpacked files in the same way SotES does (when possible).

    always_include_palette : bool = False
        Usually only bitmaps with color depth of 8 bits per pixel and lower have palettes. However, all SotES image
        resources have space reserved for 256-color palettes, and while I'm 99% certain that this space contains only
        RAM junk for bitmaps with color depth greater than 8bpp, this option can be set to retrieve these palettes
        anyway. If you're not sure what this is talking about, do not use this option.

        Palettes in >8bpp bitmaps are only suggestions for optimization. It's not guaranteed that graphics software
        will use them.

    Returns
    -------
    bytes
        The raw binary data corresponding to the decrypted Bitmap file.

    Raises
    ------
    IncompleteDataError
        If, when decrypting the data resource, the program needs to retrieve data from an offset that is out of bounds.

    ResourceValidationError
        If the data resource fails the main validation check that SotES performs for obfuscated bitmaps.

    InvalidBitmapError
        If the data resource is successfully de-obfuscated but into an invalid bitmap file.

        It's entirely possible however that even if invalid, SotES can still handle the resource without issues. For
        that reason, it's possible to suppress errors of this nature via the additional_checks parameter. Be aware
        it's not guaranteed that files generated through this method will be readable by graphic editors.

        This is a failsafe. No SotES resources are known to unpack into invalid bitmaps.

    UnsupportedBitmapError
        If the data resource is unpacked into a valid bitmap file but that whose color depth is not expected.

        As far as I know, SotES only supports 8bpp and 24bpp images. Handling for other images would be unknown.

        This is just a failsafe to let us know if images with other color depths exist.
    """
    # Resource identification step.
    if len(resource_data) < 0x458:
        # Mandatory fields require resource data to be at least this big.
        raise IncompleteSotESResourceError("Data is too small to be a packed bitmap resource.")

    # # # There could be small quirks with subtracting the obfuscation key due to underflow.
    # # # However, afaik SotES doesn't use any such values that could cause problems.
    obf_key     = st.unpack_from('I', buffer=resource_data, offset=0x448)[0]
    val_key     = st.unpack_from('I', buffer=resource_data, offset=0x438)[0] - obf_key
    pix_off_key = st.unpack_from('I', buffer=resource_data, offset=0x450)[0] - obf_key

    if val_key != 10001 or pix_off_key > 128:
        raise SotESResourceValidationError("Data is not a valid packed bitmap resource.")

    # Retrieve bitmap dimensions.
    width_key  = st.unpack_from('I', buffer=resource_data, offset=0x440)[0] - obf_key
    height_key = st.unpack_from('I', buffer=resource_data, offset=0x018)[0] - obf_key

    width_off  = 4 * width_key  + 0x004
    height_off = 4 * height_key + 0x420

    if len(resource_data) <= max(width_off, height_off) + 4:
        # Width and/or height values cannot be accessed.
        raise IncompleteSotESResourceError("Data is too small to be a packed bitmap resource.")

    img_width  = st.unpack_from('i', buffer=resource_data, offset=width_off )[0] - obf_key
    img_height = st.unpack_from('i', buffer=resource_data, offset=height_off)[0] - obf_key

    # # Additional validation.
    if additional_checks:
        if img_width <= 0:
            raise InvalidBitmapError(f"Unpacked bitmap has invalid width: {img_width}.")
        if img_height == 0:
            raise InvalidBitmapError(f"Unpacked bitmap has invalid height: {img_height}.")

    # Retrieve color depth.
    # # De-obfuscate.
    img_color_depth = st.unpack_from('H', buffer=resource_data, offset=0x430)[0] - (obf_key & 0xFFFF)

    # # Additional validation.
    if additional_checks:
        if img_color_depth not in (1, 4, 8, 16, 24, 32):
            raise InvalidBitmapError("Unpacked bitmap has invalid color depth.")

    # ---------------------------------------------------------------------------------------------------------------- #
    # Retrieve color table.
    if img_color_depth == 8:
        img_color_table = resource_data[0x20:0x420]
        img_num_colors = 0
    elif img_color_depth == 24:
        if not always_include_palette:
            img_color_table = b''
            img_num_colors = 0
        else:
            img_color_table = resource_data[0x20:0x420]
            img_num_colors = 256
    else:
        # # This is not expected but it might happen.
        raise UnsupportedBitmapError(f"Unpacked bitmap has unsupported color depth: {img_color_depth}.")

    # # Validate "alpha" channel in color table.
    if additional_checks:
        for alpha_byte in img_color_table[3::4]:
            if alpha_byte != 0x00:
                raise InvalidBitmapError("Bitmap unpacked from resource data has invalid colors.")

    # ---------------------------------------------------------------------------------------------------------------- #
    # Retrieve pixel array.
    img_pix_off = 0x458 + pix_off_key
    img_pix_size = img_color_depth // 8 * abs(img_width) * abs(img_height)

    # # Additional validation.
    # # # Check if binary data is large enough to contain the pixel array.
    if len(resource_data) < img_pix_off + img_pix_size:
        raise IncompleteSotESResourceError("Data is too small to be a packed bitmap resource.")

    # # SotES only uses positive image dimensions that are multiples of 4, so pixel array rows are never padded.
    # # The height check and padding are extra steps.
    pix_row_raw_size = img_color_depth // 8 * abs(img_width)
    pix_row_padding = bytes((- pix_row_raw_size) % 4)  # Remainder necessary to round a row up to a multiple of 4 bytes.

    pix_rows = []
    for pix_row_i in range(abs(img_height)):
        pix_row_off = img_pix_off + pix_row_i * pix_row_raw_size
        pix_row = resource_data[pix_row_off:pix_row_off + pix_row_raw_size] + pix_row_padding
        pix_rows.append(pix_row)

    if abs(img_height) < 0:
        # Rows are stored top-down instead of bottom-up.
        pix_rows = reversed(pix_rows)

    img_pix_array = b''.join(pix_rows)

    # ---------------------------------------------------------------------------------------------------------------- #
    # Build bitmap.
    # # SotES uses a very specific bitmap format, binary manipulation is sufficient.
    bmp_header = st.pack(
        '<2sL2HL',
        b'BM',                                                    # Magic value for Windows bitmaps.
        0x0E + 0x28 + len(img_color_table) + len(img_pix_array),  # File size.
        0x00, 0x00,                                               # Reserved 1 and 2.
        0x0E + 0x28 + len(img_color_table)                        # Offset to pixel array.
    )

    dib_header = st.pack(
        '<L2l2H2L2l2L',
        0x28,                # Size of this header (BITMAPINFOHEADER).
        abs(img_width),      # Image width in pixels.
        abs(img_height),     # Image height in pixels.
        0x01,                # Number of color planes (fixed).
        img_color_depth,     # Color depth/bit density of the image.
        0x00,                # Compression (uncompressed).
        len(img_pix_array),  # Size of pixel array, in bytes.
        0x00,                # Preferred horizontal resolution (unimportant).
        0x00,                # Preferred vertical resolution (unimportant).
        img_num_colors,      # Number of colors used in the color palette (0 = auto).
        0x00                 # Number of important colors (unimportant).
    )

    return bmp_header + dib_header + img_color_table + img_pix_array


def pack(bitmap_data: bytes) -> bytes:
    if not PIL_AVAILABLE:
        raise UnsupportedFunctionError("This function requires the Pillow Image library.")

    try:
        pil_img = Image.open(io.BytesIO(bitmap_data), formats=['BMP'])
    except UnidentifiedImageError as ex:
        raise InvalidBitmapError("Data is not a valid bitmap file.") from ex

    # # There might be a small quirk here. Bitmaps support negative heights (and maybe widths?) to reverse pixel order,
    # # but I don't know if Pillow handles that.
    # # Images with dimensions surpassing 2^16 might cause errors but those shouldn't be allowed in bitmaps.
    # # SotES shouldn't have any such images though.
    img_width, img_height = pil_img.size

    # # Sotes encrypted images are only 8-bit or 24-bit.
    if pil_img.mode == 'P':
        if pil_img.palette.mode != 'RGB':
            raise UnsupportedBitmapError("Unpacker cannot handle non-RGB palettes.")

        pil_palette = pil_img.getpalette()  # Contiguous array like [R, G, B, R, G, B, R, G, B...].
        if len(pil_palette) > 3 * 256:
            raise UnsupportedBitmapError("SotES does not support palettes with more than 256 colors.")

        # Build color table.
        img_color_depth = 8
        img_palette = b''.join(
            st.pack(
                '4B',
                pil_palette[color_offset + 2],
                pil_palette[color_offset + 1],
                pil_palette[color_offset],
                0x00                            # Colors stored as BGR0 in bitmaps.
            )
            for color_offset in range(0, len(pil_palette), 3)
        ).ljust(0x400)

        # Build pixel array.
        # # SotES does not pad the pixel array.
        # # Best to use only images with dimensions multiples of 4.
        pil_pixels = list(pil_img.getdata())  # Sequence of entries into the palette (P, P, P, P...).
        pil_row_size = img_width
        img_pixel_rows = []

        for row_index in range(img_height):
            pil_row_offset = row_index * pil_row_size
            img_pixel_rows.append(
                st.pack(
                    f"{img_width}B",
                    *pil_pixels[pil_row_offset:pil_row_offset + pil_row_size]
                )
            )

        # # Bitmaps usually store rows bottom-up.
        img_pixels = b''.join(reversed(img_pixel_rows))
    elif pil_img.mode == 'RGB':
        # Color table.
        img_color_depth = 24
        img_palette = bytes(0x400)

        # Pixel array.
        # # SotES does not pad the pixel array.
        # # Best to use only images with dimensions multiples of 4.
        pil_pixels = list(pil_img.getdata())  # [(R, G, B), (R, G, B)...].
        pil_row_size = img_width
        img_pixel_rows = []

        for row_index in range(img_height):
            pil_row_offset = row_index * pil_row_size
            img_pixel_row = []

            for pixel_index in range(img_width):
                # Bitmaps store channels in BGR order.
                img_pixel_row.extend(reversed(pil_pixels[pil_row_offset + pixel_index]))

            img_pixel_rows.append(
                st.pack(f"{3 * img_width}B", *img_pixel_row)
            )

        # # Pixel array rows are stored bottom-up.
        img_pixels = b''.join(reversed(img_pixel_rows))
    else:
        raise UnsupportedBitmapError("SotES only supports 8bpp and 24bpp bitmaps.")

    # Encrypted format is as follows.
    # First 0x20 bytes are junk + encryption metadata.
    # Next 0x400 bytes are palette.
    # Next 0x38 bytes are junk + encryption metadata.
    # Pixel array is somewhere after that.
    return b''.join((
        bytes(0x04),                    # Junk.
        st.pack('i', img_width),        # Image width @ off 0x04 (this is not always here).
        bytes(0x18),                    # Junk.
        img_palette,                    # Palette @ off 0x20.
        st.pack('i', img_height),       # Image height @ off 0x420 (this is not always here).
        bytes(0x0C),                    # Junk.
        st.pack('H', img_color_depth),  # Color depth @ off 0x430.
        bytes(0x06),                    # Junk.
        st.pack('I', 10001),            # Validation key @ off 0x438.
        bytes(0x1C),                    # Junk.
        img_pixels                      # Pixel array @ off 0x458 (this is not always here).
    ))
