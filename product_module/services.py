"""Queries shared by the storefront: public product lists, filters, home page sections."""
from decimal import Decimal, InvalidOperation

from django.db.models import Exists, Min, OuterRef, Prefetch, Q

from .models import Brand, Category, ColorOption, Product, ProductVariant, StorageOption, effective_price_expression


def public_products():
    """Products visible in the shop (active product, brand and category) with variants prefetched."""
    return (
        Product.objects.filter(is_active=True, brand__is_active=True, category__is_active=True)
        .select_related('brand', 'category')
        .prefetch_related(Prefetch(
            'variants',
            queryset=ProductVariant.objects.filter(is_active=True).select_related('storage', 'color'),
            to_attr='active_variants_list',
        ))
    )


def new_arrivals(limit):
    return list(public_products().filter(show_on_home=True).order_by('home_sort_order', '-created_at', '-id')[:limit])


def best_sellers(limit):
    """Real sales first (sales_count > 0). Falls back to the products the manager picked."""
    sold = list(public_products().filter(sales_count__gt=0).order_by('-sales_count', '-created_at')[:limit])
    if sold:
        return sold
    return list(public_products().filter(is_bestseller_pick=True).order_by('home_sort_order', '-created_at')[:limit])


def featured_products(limit):
    return list(public_products().filter(is_featured=True).order_by('home_sort_order', '-created_at')[:limit])


def featured_categories(limit):
    return list(Category.objects.filter(is_active=True, show_on_home=True)[:limit])


def related_products(product, limit=4):
    return list(public_products().filter(category=product.category).exclude(pk=product.pk)[:limit])


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _decimal(value):
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None
    if number.is_nan() or number.is_infinite() or number < 0:
        return None
    return number


SORT_OPTIONS = [
    ('newest', 'Newest'),
    ('price_asc', 'Price: low to high'),
    ('price_desc', 'Price: high to low'),
    ('name', 'Name A-Z'),
]


def filter_products(params, category=None, brand=None):
    """Apply the storefront search/filter parameters (a QueryDict-like mapping)."""
    queryset = public_products()
    if category is not None:
        queryset = queryset.filter(category=category)
    if brand is not None:
        queryset = queryset.filter(brand=brand)

    query = (params.get('q') or '').strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query) | Q(category__name__icontains=query)
            | Q(short_description__icontains=query) | Q(model_number__icontains=query)
        )

    category_id = _int(params.get('category'))
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    brand_id = _int(params.get('brand'))
    if brand_id:
        queryset = queryset.filter(brand_id=brand_id)
    if params.get('featured') == '1':
        queryset = queryset.filter(is_featured=True)

    # Variant-level filters must all match the SAME variant (e.g. 256GB *and* Blue).
    variant_filter = ProductVariant.objects.filter(product=OuterRef('pk'), is_active=True)
    use_variant_filter = False
    storage_id = _int(params.get('storage'))
    if storage_id:
        variant_filter = variant_filter.filter(storage_id=storage_id)
        use_variant_filter = True
    color_id = _int(params.get('color'))
    if color_id:
        variant_filter = variant_filter.filter(color_id=color_id)
        use_variant_filter = True
    if params.get('in_stock') == '1':
        variant_filter = variant_filter.filter(stock__gt=0)
        use_variant_filter = True
    min_price = _decimal(params.get('min_price'))
    max_price = _decimal(params.get('max_price'))
    if min_price is not None or max_price is not None:
        variant_filter = variant_filter.annotate(eff_price=effective_price_expression())
        if min_price is not None:
            variant_filter = variant_filter.filter(eff_price__gte=min_price)
        if max_price is not None:
            variant_filter = variant_filter.filter(eff_price__lte=max_price)
        use_variant_filter = True
    if use_variant_filter:
        queryset = queryset.filter(Exists(variant_filter))

    sort = params.get('sort') or 'newest'
    if sort in ('price_asc', 'price_desc'):
        queryset = queryset.annotate(
            sort_price=Min(effective_price_expression('variants__'), filter=Q(variants__is_active=True)))
        queryset = queryset.order_by('sort_price' if sort == 'price_asc' else '-sort_price', '-id')
    elif sort == 'name':
        queryset = queryset.order_by('name', '-id')
    else:
        queryset = queryset.order_by('-created_at', '-id')
    return queryset


def filter_options():
    """Choices shown in the filter sidebar (only things that really exist in active products)."""
    active_variants = ProductVariant.objects.filter(
        is_active=True, product__is_active=True, product__brand__is_active=True,
        product__category__is_active=True)
    return {
        'categories': Category.objects.filter(is_active=True),
        'brands': Brand.objects.filter(is_active=True, products__is_active=True).distinct(),
        'storages': StorageOption.objects.filter(variants__in=active_variants).distinct(),
        'colors': ColorOption.objects.filter(variants__in=active_variants).distinct(),
    }
