from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from site_module.models import SiteSetting

from . import services
from .models import Brand, Category, Product


class ProductListView(ListView):
    template_name = 'product_module/product_list.html'
    context_object_name = 'products'
    category = None
    brand = None

    def get_paginate_by(self, queryset):
        per_page = SiteSetting.load().products_per_page
        return max(1, min(per_page, 60))

    def get_queryset(self):
        slug_category = self.kwargs.get('category_slug')
        slug_brand = self.kwargs.get('brand_slug')
        if slug_category:
            self.category = get_object_or_404(Category, slug=slug_category, is_active=True)
        if slug_brand:
            self.brand = get_object_or_404(Brand, slug=slug_brand, is_active=True)
        return services.filter_products(self.request.GET, category=self.category, brand=self.brand)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        context.update(services.filter_options())
        context['sort_options'] = services.SORT_OPTIONS
        context['current'] = self.request.GET
        context['current_category'] = self.category
        context['current_brand'] = self.brand
        context['result_count'] = context['paginator'].count
        context['query_string'] = params.urlencode()
        context['has_filters'] = any(
            self.request.GET.get(key) for key in
            ('q', 'category', 'brand', 'storage', 'color', 'min_price', 'max_price', 'in_stock', 'featured'))
        title = 'All products'
        if self.category:
            title = self.category.name
        elif self.brand:
            title = self.brand.name
        elif self.request.GET.get('q'):
            title = f'Search results for "{self.request.GET.get("q").strip()[:60]}"'
        context['page_title'] = title
        context['meta_title'] = title
        return context


class ProductDetailView(DetailView):
    template_name = 'product_module/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return services.public_products().prefetch_related('gallery')

    def get_object(self, queryset=None):
        queryset = queryset if queryset is not None else self.get_queryset()
        try:
            return queryset.get(slug=self.kwargs['slug'])
        except Product.DoesNotExist:
            raise Http404('This product is not available.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        variants = product.get_active_variants()
        default_variant = next((v for v in variants if v.in_stock), variants[0] if variants else None)
        context['variants'] = variants
        context['default_variant'] = default_variant
        context['gallery'] = list(product.gallery.all())
        context['related_products'] = services.related_products(product)
        context['meta_title'] = product.meta_title or product.name
        context['meta_description'] = product.meta_description or product.short_description
        context['max_quantity'] = min(getattr(settings, 'CART_MAX_QUANTITY_PER_ITEM', 10), 99)
        return context
