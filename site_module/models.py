from django.db import models

from site_module.appearance import (
    CARD_RATIO_CHOICES, COLOR_DEFAULTS, DEFAULT_PROFILE, FONT_CHOICES, IMAGE_FIT_CHOICES,
    PROFILE_CHOICES, SECTION_RATIO_CHOICES, SIZE_DEFAULTS,
)
from utils.validators import (
    validate_font_file, validate_font_name, validate_hex_color, validate_image_file,
    validate_link, validate_optional_hex_color,
)

SECTION_TYPES = [
    ('hero', 'Hero banner'),
    ('new_arrivals', 'New arrivals'),
    ('best_sellers', 'Best sellers'),
    ('featured_categories', 'Featured categories'),
    ('featured_products', 'Featured products'),
    ('promo', 'Promotional block'),
    ('banner', 'Banner'),
    ('about', 'About the store'),
    ('benefits', 'Shopping benefits'),
    ('custom', 'Custom content'),
]

SOCIAL_PLATFORMS = [
    ('facebook', 'Facebook'), ('instagram', 'Instagram'), ('x', 'X (Twitter)'),
    ('youtube', 'YouTube'), ('tiktok', 'TikTok'), ('linkedin', 'LinkedIn'),
    ('telegram', 'Telegram'), ('whatsapp', 'WhatsApp'), ('other', 'Other'),
]

TEXT_ALIGN_CHOICES = [('left', 'Left'), ('center', 'Center')]


class SiteSetting(models.Model):
    """Single-row table with the general store settings (always pk=1, use SiteSetting.load())."""
    store_name = models.CharField(max_length=120, default='TechStore')
    tagline = models.CharField(max_length=200, default='Smartphones and tablets you can trust')
    logo = models.ImageField(upload_to='site/', blank=True, validators=[validate_image_file])
    logo_alt = models.CharField(max_length=160, blank=True)
    favicon = models.ImageField(upload_to='site/', blank=True, validators=[validate_image_file])
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    default_meta_title = models.CharField(max_length=200, default='TechStore - Smartphones & Tablets')
    default_meta_description = models.CharField(
        max_length=300, default='Shop the latest smartphones and tablets from top brands.')
    currency_symbol = models.CharField(max_length=8, default='$')
    products_per_page = models.PositiveSmallIntegerField(default=12)
    announcement_text = models.CharField(max_length=250, blank=True)
    announcement_url = models.CharField(max_length=300, blank=True, validators=[validate_link])
    announcement_is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'site setting'

    def __str__(self):
        return self.store_name

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class CustomFont(models.Model):
    name = models.CharField(max_length=60, unique=True, validators=[validate_font_name])
    file = models.FileField(upload_to='fonts/', validators=[validate_font_file])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AppearanceSetting(models.Model):
    """Single-row table with colors, fonts and sizes (always pk=1, use AppearanceSetting.load())."""
    profile_name = models.CharField(max_length=30, choices=PROFILE_CHOICES, default=DEFAULT_PROFILE)

    primary_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['primary_color'], validators=[validate_hex_color])
    secondary_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['secondary_color'], validators=[validate_hex_color])
    background_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['background_color'], validators=[validate_hex_color])
    surface_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['surface_color'], validators=[validate_hex_color])
    text_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['text_color'], validators=[validate_hex_color])
    muted_text_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['muted_text_color'], validators=[validate_hex_color])
    heading_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['heading_color'], validators=[validate_hex_color])
    link_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['link_color'], validators=[validate_hex_color])
    button_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['button_color'], validators=[validate_hex_color])
    button_text_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['button_text_color'], validators=[validate_hex_color])
    button_hover_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['button_hover_color'], validators=[validate_hex_color])
    border_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['border_color'], validators=[validate_hex_color])
    header_bg_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['header_bg_color'], validators=[validate_hex_color])
    header_text_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['header_text_color'], validators=[validate_hex_color])
    footer_bg_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['footer_bg_color'], validators=[validate_hex_color])
    footer_text_color = models.CharField(max_length=7, default=COLOR_DEFAULTS['footer_text_color'], validators=[validate_hex_color])

    body_font = models.CharField(max_length=20, choices=FONT_CHOICES, default='system')
    heading_font = models.CharField(max_length=20, choices=FONT_CHOICES, default='system')
    custom_body_font = models.ForeignKey(
        CustomFont, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    custom_heading_font = models.ForeignKey(
        CustomFont, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    font_size_body = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_body'])
    font_size_h1 = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_h1'])
    font_size_h2 = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_h2'])
    font_size_h3 = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_h3'])
    font_size_button = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_button'])
    font_size_menu = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_menu'])
    font_size_footer = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['font_size_footer'])

    card_aspect_ratio = models.CharField(max_length=10, choices=CARD_RATIO_CHOICES, default='1:1')
    card_image_height = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['card_image_height'])
    product_image_fit = models.CharField(max_length=10, choices=IMAGE_FIT_CHOICES, default='contain')
    banner_max_width = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['banner_max_width'])
    hero_height = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['hero_height'])
    section_spacing = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['section_spacing'])
    container_width = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['container_width'])
    border_radius = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['border_radius'])
    card_padding = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['card_padding'])
    element_gap = models.PositiveSmallIntegerField(default=SIZE_DEFAULTS['element_gap'])

    class Meta:
        verbose_name = 'appearance setting'

    def __str__(self):
        return f'Appearance ({self.profile_name})'

    @classmethod
    def load(cls):
        obj, _created = cls.objects.select_related(
            'custom_body_font', 'custom_heading_font').get_or_create(pk=1)
        return obj


class HomeSection(models.Model):
    """A block of the home page. Order, visibility, texts, images and look are all editable."""
    internal_name = models.CharField(max_length=120, unique=True)
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES)
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to='sections/', blank=True, validators=[validate_image_file])
    mobile_image = models.ImageField(upload_to='sections/', blank=True, validators=[validate_image_file])
    image_alt = models.CharField(max_length=200, blank=True)
    button_text = models.CharField(max_length=60, blank=True)
    button_url = models.CharField(max_length=300, blank=True, validators=[validate_link])
    items_count = models.PositiveSmallIntegerField(default=8)
    background_color = models.CharField(max_length=7, blank=True, validators=[validate_optional_hex_color])
    text_color = models.CharField(max_length=7, blank=True, validators=[validate_optional_hex_color])
    padding_y = models.PositiveSmallIntegerField(null=True, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    image_aspect_ratio = models.CharField(max_length=10, choices=SECTION_RATIO_CHOICES, default='auto')
    image_fit = models.CharField(max_length=10, choices=IMAGE_FIT_CHOICES, default='cover')
    text_align = models.CharField(max_length=10, choices=TEXT_ALIGN_CHOICES, default='left')
    sort_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.internal_name

    @property
    def template_name(self):
        return f'home_module/sections/{self.section_type}.html'

    @property
    def style_attr(self):
        """Inline style built only from validated values (hex colors and integers)."""
        rules = []
        if self.background_color:
            rules.append(f'background:{self.background_color}')
        if self.text_color:
            rules.append(f'color:{self.text_color}')
        if self.padding_y is not None:
            rules.append(f'padding-top:{int(self.padding_y)}px;padding-bottom:{int(self.padding_y)}px')
        return ';'.join(rules)

    @property
    def image_ratio_css(self):
        if self.image_aspect_ratio and self.image_aspect_ratio != 'auto':
            return self.image_aspect_ratio.replace(':', ' / ')
        return ''


class SectionItem(models.Model):
    """Child entries of a section (e.g. the cards of the "Shopping benefits" section)."""
    section = models.ForeignKey(HomeSection, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=120)
    text = models.CharField(max_length=300, blank=True)
    icon = models.CharField(max_length=16, blank=True)
    image = models.ImageField(upload_to='sections/', blank=True, validators=[validate_image_file])
    image_alt = models.CharField(max_length=200, blank=True)
    url = models.CharField(max_length=300, blank=True, validators=[validate_link])
    sort_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class NavLink(models.Model):
    title = models.CharField(max_length=60)
    url = models.CharField(max_length=300, validators=[validate_link])
    open_in_new_tab = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class FooterSetting(models.Model):
    """Single-row table with the footer configuration (always pk=1, use FooterSetting.load())."""
    title = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    show_logo = models.BooleanField(default=True)
    show_description = models.BooleanField(default=True)
    show_contact = models.BooleanField(default=True)
    show_links = models.BooleanField(default=True)
    show_social = models.BooleanField(default=True)
    show_copyright = models.BooleanField(default=True)
    contact_title = models.CharField(max_length=80, default='Contact')
    social_title = models.CharField(max_length=80, default='Follow us')
    copyright_text = models.CharField(max_length=250, default='\u00a9 {year} TechStore. All rights reserved.')
    about_order = models.PositiveIntegerField(default=10)
    contact_order = models.PositiveIntegerField(default=90)
    social_order = models.PositiveIntegerField(default=95)

    class Meta:
        verbose_name = 'footer setting'

    def __str__(self):
        return 'Footer settings'

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class FooterColumn(models.Model):
    title = models.CharField(max_length=80)
    sort_order = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    column = models.ForeignKey(FooterColumn, on_delete=models.CASCADE, related_name='links')
    title = models.CharField(max_length=80)
    url = models.CharField(max_length=300, validators=[validate_link])
    open_in_new_tab = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class SocialLink(models.Model):
    platform = models.CharField(max_length=20, choices=SOCIAL_PLATFORMS, default='other')
    label = models.CharField(max_length=60, blank=True)
    url = models.URLField(max_length=300)
    sort_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.label or self.get_platform_display()

    @property
    def display_name(self):
        return self.label or self.get_platform_display()


class ContentPage(models.Model):
    """Simple text pages such as About Us. Body is plain text (escaped on output)."""
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    body = models.TextField(blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title
