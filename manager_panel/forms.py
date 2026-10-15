from django import forms
from django.forms import inlineformset_factory

from product_module.models import (
    Brand, Category, ColorOption, Product, ProductImage, ProductVariant, StorageOption,
)
from site_module.appearance import COLOR_FIELDS, SIZE_FIELDS, SIZE_RANGES
from site_module.models import (
    AppearanceSetting, ContentPage, CustomFont, FooterColumn, FooterLink, FooterSetting,
    HomeSection, NavLink, SectionItem, SiteSetting, SocialLink,
)
from utils.text import unique_slug


class ColorInput(forms.TextInput):
    input_type = 'color'


class StyledFormMixin:
    """Adds CSS classes to every widget and lets a form group its fields into fieldsets."""
    fieldsets = None

    def style_fields(self):
        for field in self.fields.values():
            widget = field.widget
            classes = widget.attrs.get('class', '')
            if isinstance(widget, forms.CheckboxInput):
                css = 'form-check'
            elif isinstance(widget, (forms.FileInput, forms.ClearableFileInput)):
                css = 'form-file'
            elif isinstance(widget, ColorInput):
                css = 'form-color'
            else:
                css = 'form-control'
            widget.attrs['class'] = f'{classes} {css}'.strip()

    def get_fieldsets(self):
        visible = {bound.name: bound for bound in self.visible_fields()}
        if not self.fieldsets:
            return [(None, list(visible.values()))]
        result, used = [], set()
        for title, names in self.fieldsets:
            bounds = [visible[name] for name in names if name in visible]
            used.update(name for name in names if name in visible)
            if bounds:
                result.append((title, bounds))
        leftover = [bound for name, bound in visible.items() if name not in used]
        if leftover:
            result.append(('Other', leftover))
        return result


class ManagerModelForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class BrandForm(ManagerModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'logo', 'logo_alt', 'description', 'is_active', 'sort_order']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'slug': 'Leave empty to generate it from the name.',
                      'sort_order': 'Lower numbers appear first.'}


class CategoryForm(ManagerModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'image', 'image_alt', 'description', 'is_active', 'show_on_home', 'sort_order']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'slug': 'Leave empty to generate it from the name.',
                      'show_on_home': 'Show in the "Featured categories" section of the home page.',
                      'sort_order': 'Lower numbers appear first.'}


class StorageOptionForm(ManagerModelForm):
    class Meta:
        model = StorageOption
        fields = ['label', 'sort_order']
        help_texts = {'label': 'For example 128GB, 256GB, 512GB or 1TB.'}


class ColorOptionForm(ManagerModelForm):
    class Meta:
        model = ColorOption
        fields = ['name', 'hex_code', 'sort_order']
        widgets = {'hex_code': ColorInput()}
        labels = {'hex_code': 'Swatch color'}


class ProductForm(ManagerModelForm):
    fieldsets = [
        ('Basic information', ['name', 'slug', 'brand', 'category', 'short_description', 'description']),
        ('Main image', ['image', 'image_alt']),
        ('Visibility', ['is_active', 'is_featured', 'show_on_home', 'is_bestseller_pick', 'home_sort_order',
                        'sales_count']),
        ('Specifications', ['model_number', 'operating_system', 'processor', 'ram', 'screen_size',
                            'battery_capacity', 'camera', 'connectivity', 'warranty']),
        ('SEO', ['meta_title', 'meta_description']),
    ]

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'brand', 'category', 'short_description', 'description', 'image', 'image_alt',
            'is_active', 'is_featured', 'show_on_home', 'is_bestseller_pick', 'home_sort_order', 'sales_count',
            'model_number', 'operating_system', 'processor', 'ram', 'screen_size', 'battery_capacity',
            'camera', 'connectivity', 'warranty', 'meta_title', 'meta_description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'name': 'Product name', 'ram': 'RAM', 'is_active': 'Active (visible in the shop)',
            'is_featured': 'Featured product', 'show_on_home': 'Show in "New arrivals" on the home page',
            'is_bestseller_pick': 'Manager pick for "Best sellers"',
            'home_sort_order': 'Home page order',
            'sales_count': 'Units sold (real sales)',
        }
        help_texts = {
            'slug': 'Used in the product URL. Leave empty to generate it from the name.',
            'home_sort_order': 'Lower numbers appear first; products with the same number are sorted by date.',
            'is_bestseller_pick': 'Used for the "Best sellers" section until real sales data exists.',
            'sales_count': 'Counted from real orders. Edit only to correct historical data.',
            'image': 'JPG, PNG or WEBP up to 5 MB.',
            'model_number': 'Specifications left empty are not shown to customers.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brand'].queryset = Brand.objects.all()
        self.fields['category'].queryset = Category.objects.all()


class VariantForm(ManagerModelForm):
    class Meta:
        model = ProductVariant
        fields = ['storage', 'color', 'sku', 'price', 'discount_price', 'stock', 'is_active', 'sort_order']
        labels = {'storage': 'Storage Capacity', 'discount_price': 'Sale price', 'sku': 'SKU'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('price', 'discount_price'):
            self.fields[name].widget.attrs.update({'min': '0', 'step': '0.01'})
        self.fields['stock'].widget.attrs['min'] = '0'

    def clean(self):
        cleaned = super().clean()
        price = cleaned.get('price')
        sale = cleaned.get('discount_price')
        if price is not None and price <= 0:
            self.add_error('price', 'Price must be greater than zero.')
        if sale is not None:
            if sale <= 0:
                self.add_error('discount_price', 'Sale price must be greater than zero.')
            elif price is not None and sale >= price:
                self.add_error('discount_price', 'Sale price must be lower than the regular price.')
        return cleaned


class ProductImageForm(ManagerModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'sort_order']


ProductVariantFormSet = inlineformset_factory(
    Product, ProductVariant, form=VariantForm, extra=1, can_delete=True, min_num=1, validate_min=True)
ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=2, can_delete=True)


class SectionForm(ManagerModelForm):
    custom_colors = forms.BooleanField(
        required=False, label='Use custom colors for this section',
        help_text='When off, the section uses the colors of the active design profile.')

    fieldsets = [
        ('General', ['internal_name', 'section_type', 'is_active', 'sort_order']),
        ('Content', ['title', 'subtitle', 'body', 'button_text', 'button_url', 'items_count']),
        ('Images', ['image', 'mobile_image', 'image_alt', 'image_aspect_ratio', 'image_fit']),
        ('Look', ['text_align', 'custom_colors', 'background_color', 'text_color', 'padding_y', 'height']),
    ]

    class Meta:
        model = HomeSection
        fields = [
            'internal_name', 'section_type', 'is_active', 'sort_order', 'title', 'subtitle', 'body',
            'button_text', 'button_url', 'items_count', 'image', 'mobile_image', 'image_alt',
            'image_aspect_ratio', 'image_fit', 'text_align', 'background_color', 'text_color',
            'padding_y', 'height',
        ]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
            'background_color': ColorInput(),
            'text_color': ColorInput(),
        }
        labels = {
            'internal_name': 'Internal name (only shown in this panel)',
            'section_type': 'Section type',
            'items_count': 'Number of items to show',
            'image': 'Image (desktop)',
            'mobile_image': 'Image (mobile, optional)',
            'padding_y': 'Vertical padding (px)',
            'height': 'Minimum height (px, hero/banner)',
            'image_aspect_ratio': 'Image aspect ratio',
            'image_fit': 'Image cropping',
        }
        help_texts = {
            'sort_order': 'Lower numbers appear first. You can also use the arrows in the sections list.',
            'button_url': 'Example: /products/ or https://example.com',
            'items_count': 'For product and category sections (1-24).',
            'padding_y': 'Leave empty to use the global section spacing (0-200).',
            'height': 'Leave empty to use the global hero height (200-900).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        self.fields['custom_colors'].initial = bool(instance.pk and (instance.background_color or instance.text_color))
        if not instance.background_color:
            self.initial['background_color'] = '#ffffff'
        if not instance.text_color:
            self.initial['text_color'] = '#111827'
        self.fields['section_type'].widget.attrs['data-section-type'] = '1'

    def clean_items_count(self):
        value = self.cleaned_data.get('items_count') or 8
        if not 1 <= value <= 24:
            raise forms.ValidationError('Enter a number between 1 and 24.')
        return value

    def clean_padding_y(self):
        value = self.cleaned_data.get('padding_y')
        if value is not None and not 0 <= value <= 200:
            raise forms.ValidationError('Enter a value between 0 and 200.')
        return value

    def clean_height(self):
        value = self.cleaned_data.get('height')
        if value is not None and not 200 <= value <= 900:
            raise forms.ValidationError('Enter a value between 200 and 900.')
        return value

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('custom_colors'):
            cleaned['background_color'] = ''
            cleaned['text_color'] = ''
        return cleaned


class SectionItemForm(ManagerModelForm):
    class Meta:
        model = SectionItem
        fields = ['title', 'text', 'icon', 'image', 'image_alt', 'url', 'sort_order', 'is_active']
        labels = {'icon': 'Icon (emoji or short text)'}


SectionItemFormSet = inlineformset_factory(
    HomeSection, SectionItem, form=SectionItemForm, extra=2, can_delete=True)


class NavLinkForm(ManagerModelForm):
    class Meta:
        model = NavLink
        fields = ['title', 'url', 'open_in_new_tab', 'sort_order', 'is_active']
        help_texts = {'url': 'Example: /products/ or https://example.com'}


class FooterColumnForm(ManagerModelForm):
    class Meta:
        model = FooterColumn
        fields = ['title', 'sort_order', 'is_active']
        help_texts = {'sort_order': 'Lower numbers appear first (the About block uses 10, Contact 90, Social 95).'}


class FooterLinkForm(ManagerModelForm):
    class Meta:
        model = FooterLink
        fields = ['title', 'url', 'open_in_new_tab', 'sort_order', 'is_active']


FooterLinkFormSet = inlineformset_factory(
    FooterColumn, FooterLink, form=FooterLinkForm, extra=2, can_delete=True)


class SocialLinkForm(ManagerModelForm):
    class Meta:
        model = SocialLink
        fields = ['platform', 'label', 'url', 'sort_order', 'is_active']
        help_texts = {'label': 'Optional. Shown instead of the platform name.'}


class FooterSettingForm(ManagerModelForm):
    fieldsets = [
        ('About block', ['show_logo', 'title', 'show_description', 'description', 'about_order']),
        ('Link columns', ['show_links']),
        ('Contact block', ['show_contact', 'contact_title', 'contact_order']),
        ('Social block', ['show_social', 'social_title', 'social_order']),
        ('Bottom bar', ['show_copyright', 'copyright_text']),
    ]

    class Meta:
        model = FooterSetting
        fields = [
            'show_logo', 'title', 'show_description', 'description', 'about_order', 'show_links',
            'show_contact', 'contact_title', 'contact_order', 'show_social', 'social_title',
            'social_order', 'show_copyright', 'copyright_text',
        ]
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
        help_texts = {
            'copyright_text': 'Use {year} to insert the current year.',
            'about_order': 'Column order: lower numbers appear first.',
        }
        labels = {'title': 'Footer title', 'show_logo': 'Show store logo / name'}


class ContentPageForm(ManagerModelForm):
    class Meta:
        model = ContentPage
        fields = ['title', 'slug', 'body', 'meta_title', 'meta_description', 'is_active']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 12}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'slug': 'Used in the page URL (/pages/<slug>/). Leave empty to generate it from the title.',
            'body': 'Plain text. Blank lines start a new paragraph.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('slug') and cleaned.get('title'):
            cleaned['slug'] = unique_slug(ContentPage, cleaned['title'], instance=self.instance, max_length=180)
        return cleaned


class SiteSettingForm(ManagerModelForm):
    fieldsets = [
        ('Branding', ['store_name', 'tagline', 'logo', 'logo_alt', 'favicon']),
        ('Contact information', ['contact_email', 'contact_phone', 'address']),
        ('Search engines (defaults)', ['default_meta_title', 'default_meta_description']),
        ('Shop', ['currency_symbol', 'products_per_page']),
        ('Announcement bar', ['announcement_is_active', 'announcement_text', 'announcement_url']),
    ]

    class Meta:
        model = SiteSetting
        fields = [
            'store_name', 'tagline', 'logo', 'logo_alt', 'favicon', 'contact_email', 'contact_phone',
            'address', 'default_meta_title', 'default_meta_description', 'currency_symbol',
            'products_per_page', 'announcement_is_active', 'announcement_text', 'announcement_url',
        ]
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}
        labels = {'logo_alt': 'Logo alternative text', 'announcement_is_active': 'Show the announcement bar'}
        help_texts = {
            'logo': 'JPG, PNG or WEBP up to 5 MB.',
            'favicon': 'Small square image (PNG recommended).',
            'products_per_page': 'Between 4 and 48.',
        }

    def clean_products_per_page(self):
        value = self.cleaned_data['products_per_page']
        if not 4 <= value <= 48:
            raise forms.ValidationError('Enter a number between 4 and 48.')
        return value

    def clean_currency_symbol(self):
        return self.cleaned_data['currency_symbol'].strip() or '$'


class CustomFontForm(ManagerModelForm):
    class Meta:
        model = CustomFont
        fields = ['name', 'file', 'is_active']
        help_texts = {
            'name': 'Letters, numbers, spaces, dashes. This is the font family name.',
            'file': 'TTF, OTF, WOFF or WOFF2 up to 2 MB. Only upload fonts you are licensed to use.',
        }


class AppearanceForm(ManagerModelForm):
    class Meta:
        model = AppearanceSetting
        fields = (
            ['profile_name']
            + [name for name, _label, _var in COLOR_FIELDS]
            + ['body_font', 'heading_font', 'custom_body_font', 'custom_heading_font']
            + [name for name in SIZE_FIELDS]
            + ['card_aspect_ratio', 'product_image_fit']
        )
        widgets = {name: ColorInput() for name, _label, _var in COLOR_FIELDS}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, label, var in COLOR_FIELDS:
            self.fields[name].label = label
            self.fields[name].widget.attrs['data-css-var'] = var
        for name, spec in SIZE_FIELDS.items():
            field = self.fields[name]
            field.label = f'{spec[0]} ({spec[2]})'
            field.help_text = f'Allowed range: {spec[3]} - {spec[4]}'
            field.widget.attrs.update({
                'min': spec[3], 'max': spec[4], 'data-css-var': spec[1], 'data-unit': spec[2]})
        self.fields['profile_name'].label = 'Design profile'
        self.fields['custom_body_font'].queryset = CustomFont.objects.filter(is_active=True)
        self.fields['custom_heading_font'].queryset = CustomFont.objects.filter(is_active=True)
        self.fields['custom_body_font'].label = 'Custom body font'
        self.fields['custom_heading_font'].label = 'Custom heading font'
        self.fields['card_aspect_ratio'].label = 'Product image shape'
        self.fields['product_image_fit'].label = 'Product image cropping'

    def clean(self):
        cleaned = super().clean()
        for name, (low, high) in SIZE_RANGES.items():
            value = cleaned.get(name)
            if value is not None and not low <= value <= high:
                self.add_error(name, f'Enter a value between {low} and {high}.')
        if cleaned.get('body_font') == 'custom' and not cleaned.get('custom_body_font'):
            self.add_error('custom_body_font', 'Choose an uploaded font or pick another body font.')
        if cleaned.get('heading_font') == 'custom' and not cleaned.get('custom_heading_font'):
            self.add_error('custom_heading_font', 'Choose an uploaded font or pick another heading font.')
        return cleaned
