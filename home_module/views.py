from django.views.generic import TemplateView

from product_module import services
from site_module.models import HomeSection, SiteSetting


class HomeView(TemplateView):
    template_name = 'home_module/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sections = list(
            HomeSection.objects.filter(is_active=True).prefetch_related('items'))
        for section in sections:
            count = max(1, min(section.items_count or 8, 24))
            kind = section.section_type
            if kind == 'new_arrivals':
                section.products = services.new_arrivals(count)
            elif kind == 'best_sellers':
                section.products = services.best_sellers(count)
            elif kind == 'featured_products':
                section.products = services.featured_products(count)
            elif kind == 'featured_categories':
                section.categories = services.featured_categories(count)
            section.active_items = [item for item in section.items.all() if item.is_active]
        site = SiteSetting.load()
        context['sections'] = sections
        context['meta_title'] = site.default_meta_title
        context['meta_description'] = site.default_meta_description
        return context
