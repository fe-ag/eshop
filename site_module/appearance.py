"""
Central definition of the appearance system: defaults, design profiles, valid ranges and the
CSS-variables builder. Everything that ends up inside the <style> block is validated here.
"""
import re

HEX_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

COLOR_FIELDS = [
    ('primary_color', 'Primary color', '--c-primary'),
    ('secondary_color', 'Secondary color', '--c-secondary'),
    ('background_color', 'Page background', '--c-bg'),
    ('surface_color', 'Card background', '--c-surface'),
    ('text_color', 'Main text', '--c-text'),
    ('muted_text_color', 'Secondary text', '--c-muted'),
    ('heading_color', 'Headings', '--c-heading'),
    ('link_color', 'Links', '--c-link'),
    ('button_color', 'Buttons', '--c-btn'),
    ('button_text_color', 'Button text', '--c-btn-text'),
    ('button_hover_color', 'Button hover', '--c-btn-hover'),
    ('border_color', 'Borders', '--c-border'),
    ('header_bg_color', 'Header background', '--c-header-bg'),
    ('header_text_color', 'Header text', '--c-header-text'),
    ('footer_bg_color', 'Footer background', '--c-footer-bg'),
    ('footer_text_color', 'Footer text', '--c-footer-text'),
]

# field name -> (label, css variable, unit, min, max, default)
SIZE_FIELDS = {
    'font_size_body': ('Body text size', '--fs-body', 'px', 12, 22, 16),
    'font_size_h1': ('Main heading size', '--fs-h1', 'px', 28, 72, 44),
    'font_size_h2': ('Section heading size', '--fs-h2', 'px', 22, 54, 30),
    'font_size_h3': ('Sub-heading size', '--fs-h3', 'px', 16, 36, 20),
    'font_size_button': ('Button text size', '--fs-btn', 'px', 12, 22, 15),
    'font_size_menu': ('Menu text size', '--fs-menu', 'px', 12, 22, 15),
    'font_size_footer': ('Footer text size', '--fs-footer', 'px', 11, 20, 14),
    'card_image_height': ('Product image height (fixed ratio only)', '--card-img-h', 'px', 120, 420, 240),
    'banner_max_width': ('Banner image max width', '--banner-max', 'px', 640, 2400, 1600),
    'hero_height': ('Hero section height', '--hero-h', 'px', 240, 800, 480),
    'section_spacing': ('Space between sections', '--section-gap', 'px', 16, 140, 56),
    'container_width': ('Main content width', '--container', 'px', 960, 1600, 1200),
    'border_radius': ('Corner radius', '--radius', 'px', 0, 32, 12),
    'card_padding': ('Inner spacing (padding)', '--card-pad', 'px', 8, 40, 16),
    'element_gap': ('Outer spacing (gap)', '--gap', 'px', 8, 40, 20),
}

SIZE_RANGES = {name: (spec[3], spec[4]) for name, spec in SIZE_FIELDS.items()}
SIZE_DEFAULTS = {name: spec[5] for name, spec in SIZE_FIELDS.items()}

FONT_STACKS = {
    'system': 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'humanist': '"Trebuchet MS", "Segoe UI", Candara, Verdana, sans-serif',
    'classic': 'Helvetica, Arial, "Liberation Sans", sans-serif',
    'geometric': 'Verdana, Geneva, "DejaVu Sans", sans-serif',
    'serif': 'Georgia, "Times New Roman", "DejaVu Serif", serif',
    'mono': 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
}
FONT_LABELS = {
    'system': 'System UI (default)',
    'humanist': 'Humanist (Trebuchet)',
    'classic': 'Classic (Helvetica/Arial)',
    'geometric': 'Wide (Verdana)',
    'serif': 'Serif (Georgia)',
    'mono': 'Monospace',
}
FONT_CHOICES = [(key, FONT_LABELS[key]) for key in FONT_STACKS] + [('custom', 'Custom uploaded font')]

CARD_RATIO_CHOICES = [
    ('1:1', 'Square (1:1)'),
    ('4:3', 'Landscape (4:3)'),
    ('3:4', 'Portrait (3:4)'),
    ('16:9', 'Wide (16:9)'),
    ('fixed', 'Fixed height'),
]
SECTION_RATIO_CHOICES = [
    ('auto', 'Automatic'),
    ('1:1', 'Square (1:1)'),
    ('4:3', 'Landscape (4:3)'),
    ('3:4', 'Portrait (3:4)'),
    ('16:9', 'Wide (16:9)'),
    ('21:9', 'Ultra wide (21:9)'),
]
IMAGE_FIT_CHOICES = [('cover', 'Crop to fill'), ('contain', 'Show whole image')]

_BASE = {
    'primary_color': '#2563eb', 'secondary_color': '#0ea5e9', 'background_color': '#f8fafc',
    'surface_color': '#ffffff', 'text_color': '#0f172a', 'muted_text_color': '#64748b',
    'heading_color': '#0f172a', 'link_color': '#2563eb', 'button_color': '#2563eb',
    'button_text_color': '#ffffff', 'button_hover_color': '#1d4ed8', 'border_color': '#e2e8f0',
    'header_bg_color': '#ffffff', 'header_text_color': '#0f172a',
    'footer_bg_color': '#0f172a', 'footer_text_color': '#cbd5e1',
}

DEFAULT_PROFILE = 'modern_blue'

PRESETS = {
    'modern_blue': {'label': 'Modern Blue', 'values': dict(_BASE)},
    'midnight_black': {
        'label': 'Midnight Black',
        'values': dict(_BASE, primary_color='#fbbf24', secondary_color='#f59e0b',
                       background_color='#0b0b0f', surface_color='#16161d', text_color='#e5e7eb',
                       muted_text_color='#9ca3af', heading_color='#ffffff', link_color='#fbbf24',
                       button_color='#fbbf24', button_text_color='#111111',
                       button_hover_color='#f59e0b', border_color='#27272f',
                       header_bg_color='#0f0f14', header_text_color='#ffffff',
                       footer_bg_color='#000000', footer_text_color='#9ca3af'),
    },
    'minimal_white': {
        'label': 'Minimal White',
        'values': dict(_BASE, primary_color='#111827', secondary_color='#6b7280',
                       background_color='#ffffff', surface_color='#ffffff', text_color='#1f2937',
                       muted_text_color='#6b7280', heading_color='#111827', link_color='#111827',
                       button_color='#111827', button_text_color='#ffffff',
                       button_hover_color='#374151', border_color='#e5e7eb',
                       header_bg_color='#ffffff', header_text_color='#111827',
                       footer_bg_color='#f3f4f6', footer_text_color='#4b5563'),
        'sizes': {'border_radius': 4},
    },
    'premium_dark': {
        'label': 'Premium Dark',
        'values': dict(_BASE, primary_color='#c9a227', secondary_color='#e5c76b',
                       background_color='#12121a', surface_color='#1c1c28', text_color='#e8e8f0',
                       muted_text_color='#a0a0b8', heading_color='#f5e6b3', link_color='#e5c76b',
                       button_color='#c9a227', button_text_color='#12121a',
                       button_hover_color='#e5c76b', border_color='#2c2c3d',
                       header_bg_color='#171722', header_text_color='#f5f5ff',
                       footer_bg_color='#0a0a10', footer_text_color='#a0a0b8'),
        'sizes': {'border_radius': 6},
        'fonts': {'heading_font': 'serif'},
    },
    'tech_purple': {
        'label': 'Tech Purple',
        'values': dict(_BASE, primary_color='#7c3aed', secondary_color='#ec4899',
                       background_color='#faf5ff', surface_color='#ffffff', text_color='#1e1b4b',
                       muted_text_color='#6b7280', heading_color='#3b0764', link_color='#7c3aed',
                       button_color='#7c3aed', button_text_color='#ffffff',
                       button_hover_color='#6d28d9', border_color='#e9d5ff',
                       header_bg_color='#ffffff', header_text_color='#3b0764',
                       footer_bg_color='#2e1065', footer_text_color='#ddd6fe'),
        'sizes': {'border_radius': 16},
    },
}

PROFILE_CHOICES = [(key, preset['label']) for key, preset in PRESETS.items()]

# Plain defaults used for the model field defaults (Modern Blue)
COLOR_DEFAULTS = dict(PRESETS[DEFAULT_PROFILE]['values'])


def preset_payload(key):
    """Everything a design profile sets, as a flat dict (colors, sizes, fonts)."""
    preset = PRESETS[key]
    data = dict(preset['values'])
    data.update(SIZE_DEFAULTS)
    data.update(preset.get('sizes', {}))
    data.update({'body_font': 'system', 'heading_font': 'system'})
    data.update(preset.get('fonts', {}))
    return data


def _color(value, fallback):
    return value if isinstance(value, str) and HEX_RE.match(value) else fallback


def _size(name, value):
    low, high = SIZE_RANGES[name]
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = SIZE_DEFAULTS[name]
    return max(low, min(high, number))


def _safe_font_name(name):
    cleaned = re.sub(r'[^A-Za-z0-9 _-]', '', name or '')
    return cleaned[:60]


def _css_string(value):
    return str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '')


def _font_family(key, custom_font):
    if key == 'custom' and custom_font is not None and custom_font.is_active and custom_font.file:
        name = _safe_font_name(custom_font.name)
        if name:
            return f'"{name}", {FONT_STACKS["system"]}', custom_font
    return FONT_STACKS.get(key, FONT_STACKS['system']), None


FONT_FORMATS = {'.woff2': 'woff2', '.woff': 'woff', '.ttf': 'truetype', '.otf': 'opentype'}


def build_theme_css(appearance):
    """Return a safe CSS string (":root{...}" plus @font-face rules) for the stored appearance."""
    defaults = COLOR_DEFAULTS
    parts = []
    for field, _label, var in COLOR_FIELDS:
        parts.append(f'{var}:{_color(getattr(appearance, field, None), defaults[field])}')
    for name, spec in SIZE_FIELDS.items():
        if name == 'card_image_height':
            continue
        parts.append(f'{spec[1]}:{_size(name, getattr(appearance, name, None))}{spec[2]}')

    body_family, body_font = _font_family(appearance.body_font, appearance.custom_body_font)
    heading_family, heading_font = _font_family(appearance.heading_font, appearance.custom_heading_font)
    parts.append(f'--f-body:{body_family}')
    parts.append(f'--f-heading:{heading_family}')

    ratio = appearance.card_aspect_ratio
    if ratio in ('1:1', '4:3', '3:4', '16:9'):
        parts.append(f'--card-ratio:{ratio.replace(":", " / ")}')
        parts.append('--card-img-h:auto')
    else:
        parts.append('--card-ratio:auto')
        parts.append(f'--card-img-h:{_size("card_image_height", appearance.card_image_height)}px')
    parts.append(f'--img-fit:{"cover" if appearance.product_image_fit == "cover" else "contain"}')

    css = ':root{' + ';'.join(parts) + '}'
    seen = set()
    for font in (body_font, heading_font):
        if font is None or font.pk in seen:
            continue
        seen.add(font.pk)
        ext = '.' + font.file.name.rsplit('.', 1)[-1].lower() if '.' in font.file.name else ''
        fmt = FONT_FORMATS.get(ext)
        if not fmt:
            continue
        css += (
            f'@font-face{{font-family:"{_safe_font_name(font.name)}";'
            f'src:url("{_css_string(font.file.url)}") format("{fmt}");font-display:swap}}'
        )
    return css
