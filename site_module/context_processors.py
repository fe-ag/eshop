from django.db.models import Prefetch
from django.utils import timezone

from product_module.models import Category

from .appearance import build_theme_css
from .models import (
    AppearanceSetting, FooterColumn, FooterLink, FooterSetting, NavLink, SiteSetting, SocialLink,
)


def site_context(request):
    """Settings every page needs: branding, theme CSS, menu and footer."""
    site = SiteSetting.load()
    if request.path.startswith('/manage/'):
        return {'site': site}

    appearance = AppearanceSetting.load()
    footer = FooterSetting.load()
    nav_links = list(NavLink.objects.filter(is_active=True))
    menu_categories = list(Category.objects.filter(is_active=True))
    social_links = list(SocialLink.objects.filter(is_active=True)) if footer.show_social else []

    blocks = []
    if footer.show_logo or footer.title or (footer.show_description and footer.description):
        blocks.append({'type': 'about', 'order': footer.about_order})
    if footer.show_links:
        columns = FooterColumn.objects.filter(is_active=True).prefetch_related(
            Prefetch('links', queryset=FooterLink.objects.filter(is_active=True)))
        for column in columns:
            links = list(column.links.all())
            if links:
                blocks.append({'type': 'links', 'order': column.sort_order, 'column': column, 'links': links})
    has_contact = any([site.contact_email, site.contact_phone, site.address])
    if footer.show_contact and has_contact:
        blocks.append({'type': 'contact', 'order': footer.contact_order})
    if footer.show_social and social_links:
        blocks.append({'type': 'social', 'order': footer.social_order})
    blocks.sort(key=lambda block: block['order'])

    copyright_text = footer.copyright_text.replace('{year}', str(timezone.now().year))

    return {
        'site': site,
        'theme_css': build_theme_css(appearance),
        'nav_links': nav_links,
        'menu_categories': menu_categories,
        'footer': footer,
        'footer_blocks': blocks,
        'social_links': social_links,
        'footer_copyright': copyright_text,
    }
