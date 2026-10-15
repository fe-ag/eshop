from django.contrib import messages
from django.contrib.auth import login, logout
from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from account_module.forms import LoginForm
from account_module.models import User
from product_module.models import Brand, Category, Product, ProductVariant
from site_module.appearance import (
    COLOR_FIELDS, DEFAULT_PROFILE, FONT_STACKS, PRESETS, preset_payload,
)
from site_module.models import AppearanceSetting, CustomFont, HomeSection, SiteSetting

from .crud import ManagerPageMixin, safe_redirect_target
from .forms import AppearanceForm
from .mixins import is_manager, manager_required


class ManagerLoginView(View):
    template_name = 'manager_panel/login.html'

    def get(self, request):
        if is_manager(request.user):
            return redirect(safe_redirect_target(request, reverse('manage_dashboard')))
        return render(request, self.template_name, {'form': LoginForm(), 'next': request.GET.get('next', '')})

    def post(self, request):
        form = LoginForm(request, request.POST)
        if form.is_valid():
            user = form.user
            if not is_manager(user):
                form.add_error(None, 'This account does not have access to the management panel.')
            else:
                login(request, user)
                return redirect(safe_redirect_target(request, reverse('manage_dashboard')))
        return render(request, self.template_name, {'form': form, 'next': request.POST.get('next', '')})


@require_POST
def manager_logout(request):
    logout(request)
    messages.info(request, 'You have been signed out of the management panel.')
    return redirect('manage_login')


@manager_required
def dashboard(request):
    product_stats = Product.objects.aggregate(
        total=Count('id'),
        inactive=Count('id', filter=Q(is_active=False)),
    )
    available = ProductVariant.objects.filter(product=OuterRef('pk'), is_active=True, stock__gt=0)
    out_of_stock = Product.objects.filter(is_active=True).exclude(Exists(available)).count()
    context = {
        'nav_section': 'dashboard',
        'page_title': 'Dashboard',
        'stats': [
            {'label': 'Products', 'value': product_stats['total'], 'url': reverse('manage_product_list')},
            {'label': 'Customers', 'value': User.objects.filter(is_staff=False, is_superuser=False).count(),
             'url': reverse('manage_user_list')},
            {'label': 'Categories', 'value': Category.objects.count(), 'url': reverse('manage_category_list')},
            {'label': 'Brands', 'value': Brand.objects.count(), 'url': reverse('manage_brand_list')},
            {'label': 'Inactive products', 'value': product_stats['inactive'],
             'url': reverse('manage_product_list') + '?status=inactive'},
            {'label': 'Out of stock', 'value': out_of_stock, 'url': reverse('manage_product_list')},
        ],
        'latest_products': Product.objects.select_related('brand', 'category')[:6],
        'inactive_products': Product.objects.filter(is_active=False).select_related('brand')[:6],
        'active_sections': HomeSection.objects.filter(is_active=True).count(),
        'total_sections': HomeSection.objects.count(),
        'variant_count': ProductVariant.objects.filter(is_active=True).count(),
        'announcement_on': SiteSetting.load().announcement_is_active,
    }
    return render(request, 'manager_panel/dashboard.html', context)


class AppearanceView(ManagerPageMixin, View):
    template_name = 'manager_panel/appearance.html'
    nav_section = 'appearance'
    title = 'Appearance'

    def page(self, request, form, status=200):
        color_fields = [form[name] for name, _label, _var in COLOR_FIELDS]
        size_groups = [
            ('Text sizes', ['font_size_body', 'font_size_h1', 'font_size_h2', 'font_size_h3',
                            'font_size_button', 'font_size_menu', 'font_size_footer']),
            ('Product cards and images', ['card_image_height']),
            ('Layout', ['container_width', 'banner_max_width', 'hero_height', 'section_spacing',
                        'border_radius', 'card_padding', 'element_gap']),
        ]
        size_fields = [(title, [form[name] for name in names]) for title, names in size_groups]
        presets = {key: preset_payload(key) for key in PRESETS}
        context = self.panel_context(
            form=form,
            color_fields=color_fields,
            size_fields=size_fields,
            presets_json=presets,
            font_stacks_json=FONT_STACKS,
            preset_choices=[(key, value['label']) for key, value in PRESETS.items()],
            custom_font_count=CustomFont.objects.count(),
        )
        return render(request, self.template_name, context, status=status)

    def get(self, request, *args, **kwargs):
        return self.page(request, AppearanceForm(instance=AppearanceSetting.load()))

    def post(self, request, *args, **kwargs):
        appearance = AppearanceSetting.load()
        if request.POST.get('action') == 'reset':
            payload = preset_payload(DEFAULT_PROFILE)
            for key, value in payload.items():
                setattr(appearance, key, value)
            appearance.profile_name = DEFAULT_PROFILE
            appearance.card_aspect_ratio = '1:1'
            appearance.product_image_fit = 'contain'
            appearance.custom_body_font = None
            appearance.custom_heading_font = None
            appearance.save()
            messages.success(request, 'Appearance was reset to the default profile (Modern Blue).')
            return redirect('manage_appearance')
        form = AppearanceForm(request.POST, instance=appearance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appearance saved. The storefront now uses the new look.')
            return redirect('manage_appearance')
        messages.error(request, 'Please fix the errors below.')
        return self.page(request, form)


def permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)
