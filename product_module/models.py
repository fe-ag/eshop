from django.db import models
from django.db.models import Case, DecimalField, F, When
from django.urls import reverse

from utils.text import unique_slug
from utils.validators import validate_hex_color, validate_image_file

PLACEHOLDER_IMAGE = 'img/placeholder.svg'


class Brand(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, validators=[validate_image_file])
    logo_alt = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Brand, self.name, instance=self)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, validators=[validate_image_file])
    image_alt = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, instance=self)
        super().save(*args, **kwargs)


class StorageOption(models.Model):
    """Selectable storage capacity (128GB, 256GB, 1TB ...). Managed from the panel."""
    label = models.CharField(max_length=30, unique=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'label']

    def __str__(self):
        return self.label


class ColorOption(models.Model):
    """Selectable color (Black, Silver ...). Managed from the panel."""
    name = models.CharField(max_length=60, unique=True)
    hex_code = models.CharField(max_length=7, default='#111827', validators=[validate_hex_color])
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, validators=[validate_image_file])
    image_alt = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    show_on_home = models.BooleanField(default=True)
    is_bestseller_pick = models.BooleanField(default=False)
    home_sort_order = models.PositiveIntegerField(default=100)
    sales_count = models.PositiveIntegerField(default=0)

    ram = models.CharField(max_length=60, blank=True)
    screen_size = models.CharField(max_length=60, blank=True)
    battery_capacity = models.CharField(max_length=60, blank=True)
    operating_system = models.CharField(max_length=80, blank=True)
    processor = models.CharField(max_length=120, blank=True)
    camera = models.CharField(max_length=300, blank=True)
    connectivity = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=80, blank=True)
    warranty = models.CharField(max_length=120, blank=True)

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Product, self.name, instance=self, max_length=200)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def main_image_url(self):
        from django.templatetags.static import static
        if self.image:
            return self.image.url
        return static(PLACEHOLDER_IMAGE)

    @property
    def image_alt_text(self):
        return self.image_alt or self.name

    def get_active_variants(self):
        """Active variants; uses the prefetched list when the view provided one."""
        cached = getattr(self, 'active_variants_list', None)
        if cached is not None:
            return cached
        return list(self.variants.filter(is_active=True).select_related('storage', 'color'))

    @property
    def from_price(self):
        prices = [v.effective_price for v in self.get_active_variants()]
        return min(prices) if prices else None

    @property
    def list_price_for_from_price(self):
        """Original price of the variant that gives from_price (for strike-through display)."""
        variants = self.get_active_variants()
        if not variants:
            return None
        cheapest = min(variants, key=lambda v: v.effective_price)
        return cheapest.price if cheapest.has_discount else None

    @property
    def in_stock(self):
        return any(v.stock > 0 for v in self.get_active_variants())

    @property
    def total_stock(self):
        return sum(v.stock for v in self.get_active_variants())

    @property
    def has_discount(self):
        return any(v.has_discount for v in self.get_active_variants())

    @property
    def spec_rows(self):
        """(label, value) pairs of the specifications that actually have a value."""
        pairs = [
            ('Brand', self.brand.name),
            ('Model Number', self.model_number),
            ('Operating System', self.operating_system),
            ('Processor', self.processor),
            ('RAM', self.ram),
            ('Screen Size', self.screen_size),
            ('Battery Capacity', self.battery_capacity),
            ('Camera', self.camera),
            ('Connectivity', self.connectivity),
            ('Warranty', self.warranty),
        ]
        return [(label, value) for label, value in pairs if value]

    @property
    def storage_labels(self):
        seen = []
        for variant in self.get_active_variants():
            if variant.storage.label not in seen:
                seen.append(variant.storage.label)
        return seen

    @property
    def color_options(self):
        seen = {}
        for variant in self.get_active_variants():
            seen.setdefault(variant.color_id, variant.color)
        return list(seen.values())


class ProductVariant(models.Model):
    """One purchasable version of a product: a storage capacity + color with its own price and stock."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    storage = models.ForeignKey(StorageOption, on_delete=models.PROTECT, related_name='variants')
    color = models.ForeignKey(ColorOption, on_delete=models.PROTECT, related_name='variants')
    sku = models.CharField(max_length=60, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'storage__sort_order', 'color__sort_order', 'id']
        unique_together = [('product', 'storage', 'color')]

    def __str__(self):
        return f'{self.product.name} - {self.storage.label} - {self.color.name}'

    @property
    def has_discount(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def effective_price(self):
        return self.discount_price if self.has_discount else self.price

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def label(self):
        return f'{self.storage.label} / {self.color.name}'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='products/gallery/', validators=[validate_image_file])
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product.name} image {self.pk}'


def effective_price_expression(prefix=''):
    """SQL expression: discount price when it is lower than the price, else the price."""
    return Case(
        When(**{f'{prefix}discount_price__isnull': False,
                f'{prefix}discount_price__lt': F(f'{prefix}price')},
             then=F(f'{prefix}discount_price')),
        default=F(f'{prefix}price'),
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )
