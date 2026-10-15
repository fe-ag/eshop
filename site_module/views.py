from django.shortcuts import get_object_or_404, render

from .models import ContentPage


def content_page(request, slug):
    page = get_object_or_404(ContentPage, slug=slug, is_active=True)
    return render(request, 'site_module/content_page.html', {
        'page': page,
        'meta_title': page.meta_title or page.title,
        'meta_description': page.meta_description,
    })
