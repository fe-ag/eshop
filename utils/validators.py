"""Validators shared by models and forms (images, fonts, colors, links)."""
import os
import re

from django.core.exceptions import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_FONT_BYTES = 2 * 1024 * 1024
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
IMAGE_FORMATS = ('JPEG', 'PNG', 'WEBP')
FONT_EXTENSIONS = ('.ttf', '.otf', '.woff', '.woff2')
FONT_SIGNATURES = (b'wOFF', b'wOF2', b'\x00\x01\x00\x00', b'OTTO', b'true')

HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')
FONT_NAME_RE = re.compile(r'^[A-Za-z0-9 _-]{1,60}$')
PHONE_RE = re.compile(r'^[0-9+()\-\s]{6,20}$')


def validate_image_file(value):
    """Allow only small jpg/png/webp images. SVG is rejected on purpose (XSS risk)."""
    name = getattr(value, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValidationError('Unsupported image type. Allowed: JPG, PNG, WEBP.')
    size = getattr(value, 'size', 0) or 0
    if size > MAX_IMAGE_BYTES:
        raise ValidationError('Image is too large. Maximum size is 5 MB.')
    # Check the real format only for files that were just uploaded (not yet saved).
    if getattr(value, '_committed', True) is False:
        try:
            from PIL import Image
            value.file.seek(0)
            image = Image.open(value.file)
            image_format = image.format
            value.file.seek(0)
        except Exception:
            raise ValidationError('The uploaded file is not a valid image.')
        if image_format not in IMAGE_FORMATS:
            raise ValidationError('The image content does not match an allowed format.')


def validate_font_file(value):
    name = getattr(value, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    if ext not in FONT_EXTENSIONS:
        raise ValidationError('Unsupported font type. Allowed: TTF, OTF, WOFF, WOFF2.')
    size = getattr(value, 'size', 0) or 0
    if size > MAX_FONT_BYTES:
        raise ValidationError('Font file is too large. Maximum size is 2 MB.')
    if getattr(value, '_committed', True) is False:
        try:
            value.file.seek(0)
            head = value.file.read(4)
            value.file.seek(0)
        except Exception:
            raise ValidationError('The uploaded font file could not be read.')
        if head not in FONT_SIGNATURES:
            raise ValidationError('The file content is not a valid font.')


def validate_hex_color(value):
    if not HEX_COLOR_RE.match(value or ''):
        raise ValidationError('Enter a color such as #1a2b3c.')


def validate_optional_hex_color(value):
    if value:
        validate_hex_color(value)


def validate_link(value):
    """Links must be site-relative ("/products/") or http(s) URLs. Blocks javascript: etc."""
    if not value:
        return
    if value.startswith('/') and not value.startswith('//'):
        return
    if value.lower().startswith(('http://', 'https://')):
        return
    if value.startswith('#'):
        return
    raise ValidationError('Use a relative link starting with "/" or a full http(s) URL.')


def validate_font_name(value):
    if not FONT_NAME_RE.match(value or ''):
        raise ValidationError('Use only letters, numbers, spaces, dashes and underscores.')


def validate_phone(value):
    if value and not PHONE_RE.match(value):
        raise ValidationError('Enter a valid phone number.')
