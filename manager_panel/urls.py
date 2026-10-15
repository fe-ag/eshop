from django.db.models import Prefetch
from django.urls import path

from account_module.models import User
from product_module.models import (
    Brand, Category, ColorOption, Product, ProductVariant, StorageOption,
)
from site_module.models import (
    ContentPage, CustomFont, FooterColumn, FooterSetting, HomeSection, NavLink, SiteSetting, SocialLink,
)

from . import forms, views
from .crud import ManageDeleteView, ManageFormView, ManageListView, ManageSingletonView, MoveOrderView, ToggleActiveView


def make_crud(prefix, base, model, form_class, label, plural, nav, columns, *, search=(), select=(),
              prefetch=(), filters=(), sorts=(), status_filter=True, move=False, move_scope=None,
              toggle=True, formsets=(), delete_warning='', intro='', add_label=None):
    """Build the list/add/edit/delete/toggle/move URLs of one managed model."""
    patterns = [
        path(f'{prefix}/', ManageListView.as_view(
            model=model, url_base=base, title=plural, nav_section=nav, columns=columns,
            search_fields=search, select_related=select, prefetch_related=prefetch, filters=filters,
            sort_choices=sorts, has_status_filter=status_filter, has_toggle=toggle, has_move=move,
            add_label=add_label or f'Add {label}', intro=intro,
            empty_text=f'No {plural.lower()} yet.'), name=f'manage_{base}_list'),
        path(f'{prefix}/add/', ManageFormView.as_view(
            model=model, form_class=form_class, url_base=base, object_label=label, nav_section=nav,
            formset_specs=formsets), name=f'manage_{base}_add'),
        path(f'{prefix}/<int:pk>/edit/', ManageFormView.as_view(
            model=model, form_class=form_class, url_base=base, object_label=label, nav_section=nav,
            formset_specs=formsets), name=f'manage_{base}_edit'),
        path(f'{prefix}/<int:pk>/delete/', ManageDeleteView.as_view(
            model=model, url_base=base, object_label=label, nav_section=nav,
            extra_warning=delete_warning), name=f'manage_{base}_delete'),
    ]
    if toggle:
        patterns.append(path(f'{prefix}/<int:pk>/toggle/', ToggleActiveView.as_view(
            model=model, url_base=base, nav_section=nav), name=f'manage_{base}_toggle'))
    if move:
        patterns.append(path(f'{prefix}/<int:pk>/move/<str:direction>/', MoveOrderView.as_view(
            model=model, url_base=base, nav_section=nav, scope_field=move_scope), name=f'manage_{base}_move'))
    return patterns


def money(value):
    return f'{value:.2f}' if value is not None else '-'


def user_guard(obj, request):
    if obj.pk == request.user.pk or obj.is_superuser or obj.is_staff:
        return 'Staff accounts and your own account cannot be disabled here.'
    return None


variant_prefetch = Prefetch(
    'variants',
    queryset=ProductVariant.objects.filter(is_active=True).select_related('storage', 'color'),
    to_attr='active_variants_list',
)

urlpatterns = [
    path('', views.dashboard, name='manage_dashboard'),
    path('login/', views.ManagerLoginView.as_view(), name='manage_login'),
    path('logout/', views.manager_logout, name='manage_logout'),
    path('appearance/', views.AppearanceView.as_view(), name='manage_appearance'),
    path('site/', ManageSingletonView.as_view(
        model=SiteSetting,
        form_class=forms.SiteSettingForm, url_name='manage_site', title='Store settings',
        nav_section='site'), name='manage_site'),
    path('footer/', ManageSingletonView.as_view(
        model=FooterSetting,
        form_class=forms.FooterSettingForm, url_name='manage_footer', title='Footer settings',
        nav_section='footer'), name='manage_footer'),
]

urlpatterns += make_crud(
    'products', 'product', Product, forms.ProductForm, 'product', 'Products', 'products',
    columns=[
        ('Image', lambda p: p.image, 'image'),
        ('Product', 'name'),
        ('Brand', 'brand.name'),
        ('Category', 'category.name'),
        ('From', lambda p: money(p.from_price)),
        ('Stock', 'total_stock'),
        ('Active', 'is_active', 'bool'),
        ('Featured', 'is_featured', 'bool'),
    ],
    search=['name', 'brand__name', 'model_number'], select=['brand', 'category'], prefetch=[variant_prefetch],
    filters=[
        {'param': 'category', 'label': 'Category', 'field': 'category_id',
         'options': lambda: Category.objects.values_list('id', 'name')},
        {'param': 'brand', 'label': 'Brand', 'field': 'brand_id',
         'options': lambda: Brand.objects.values_list('id', 'name')},
    ],
    sorts=[('newest', 'Newest first', ('-created_at', '-id')), ('oldest', 'Oldest first', ('created_at', 'id')),
           ('name', 'Name A-Z', ('name', 'id'))],
    formsets=[
        {'key': 'variants', 'class': forms.ProductVariantFormSet, 'title': 'Versions (storage, color, price, stock)',
         'help': 'Each row is one purchasable version. At least one is required. Untick "Active" to hide a version.'},
        {'key': 'gallery', 'class': forms.ProductImageFormSet, 'title': 'Gallery images',
         'help': 'Extra images shown on the product page. The main image is set above.'},
    ],
    delete_warning='Deleting a product also removes its versions and gallery images. '
                   'Consider deactivating it instead to keep the data.',
)
urlpatterns += make_crud(
    'categories', 'category', Category, forms.CategoryForm, 'category', 'Categories', 'categories',
    columns=[('Image', 'image', 'image'), ('Name', 'name'), ('Products', lambda c: c.products.count()),
             ('On home', 'show_on_home', 'bool'), ('Order', 'sort_order'), ('Active', 'is_active', 'bool')],
    search=['name'], move=True,
)
urlpatterns += make_crud(
    'brands', 'brand', Brand, forms.BrandForm, 'brand', 'Brands', 'brands',
    columns=[('Logo', 'logo', 'image'), ('Name', 'name'), ('Products', lambda b: b.products.count()),
             ('Order', 'sort_order'), ('Active', 'is_active', 'bool')],
    search=['name'], move=True,
)
urlpatterns += make_crud(
    'storage', 'storage', StorageOption, forms.StorageOptionForm, 'storage option', 'Storage options',
    'storage',
    columns=[('Capacity', 'label'), ('Used by versions', lambda s: s.variants.count()), ('Order', 'sort_order')],
    search=['label'], status_filter=False, toggle=False, move=True,
    intro='Capacities that can be assigned to product versions (128GB, 256GB, 1TB ...).',
)
urlpatterns += make_crud(
    'colors', 'color', ColorOption, forms.ColorOptionForm, 'color', 'Colors', 'colors',
    columns=[('Swatch', 'hex_code', 'color'), ('Name', 'name'), ('Code', 'hex_code'),
             ('Used by versions', lambda c: c.variants.count()), ('Order', 'sort_order')],
    search=['name'], status_filter=False, toggle=False, move=True,
    intro='Colors that can be assigned to product versions.',
)
urlpatterns += make_crud(
    'sections', 'section', HomeSection, forms.SectionForm, 'home section', 'Home page sections', 'sections',
    columns=[('Name', 'internal_name'), ('Type', 'get_section_type_display'), ('Title', 'title'),
             ('Order', 'sort_order'), ('Active', 'is_active', 'bool')],
    search=['internal_name', 'title'], move=True,
    formsets=[{'key': 'items', 'class': forms.SectionItemFormSet, 'title': 'Section items',
               'help': 'Used by "Shopping benefits" and "Custom content" sections (cards with icon, title and text).'}],
    intro='The home page shows active sections from top to bottom. Use the arrows to reorder them.',
)
urlpatterns += make_crud(
    'menu', 'navlink', NavLink, forms.NavLinkForm, 'menu link', 'Main menu links', 'menu',
    columns=[('Title', 'title'), ('Link', 'url'), ('Order', 'sort_order'), ('Active', 'is_active', 'bool')],
    search=['title', 'url'], move=True,
)
urlpatterns += make_crud(
    'footer-columns', 'footercol', FooterColumn, forms.FooterColumnForm, 'footer column', 'Footer columns',
    'footer_columns',
    columns=[('Title', 'title'), ('Links', lambda c: c.links.count()), ('Order', 'sort_order'),
             ('Active', 'is_active', 'bool')],
    search=['title'], move=True,
    formsets=[{'key': 'links', 'class': forms.FooterLinkFormSet, 'title': 'Links in this column', 'help': ''}],
)
urlpatterns += make_crud(
    'social', 'social', SocialLink, forms.SocialLinkForm, 'social link', 'Social links', 'social',
    columns=[('Platform', 'display_name'), ('Link', 'url'), ('Order', 'sort_order'), ('Active', 'is_active', 'bool')],
    search=['label', 'url'], move=True,
)
urlpatterns += make_crud(
    'pages', 'page', ContentPage, forms.ContentPageForm, 'page', 'Content pages', 'pages',
    columns=[('Title', 'title'), ('Address', lambda p: f'/pages/{p.slug}/'), ('Active', 'is_active', 'bool')],
    search=['title', 'slug'],
)
urlpatterns += make_crud(
    'fonts', 'font', CustomFont, forms.CustomFontForm, 'font', 'Custom fonts', 'fonts',
    columns=[('Name', 'name'), ('File', lambda f: f.file.name.rsplit('/', 1)[-1]), ('Active', 'is_active', 'bool')],
    search=['name'],
    intro='Upload fonts you are licensed to use, then select them on the Appearance page.',
)

# Customers: list, enable/disable only (no editing or deleting of accounts here)
urlpatterns += [
    path('users/', ManageListView.as_view(
        model=User, url_base='user', title='Customers', nav_section='users',
        columns=[('Name', lambda u: u.get_full_name() or '-'), ('Email', 'email'), ('Phone', 'phone'),
                 ('Location', lambda u: ', '.join(x for x in (u.city, u.country) if x) or '-'),
                 ('Staff', 'is_staff', 'bool'), ('Active', 'is_active', 'bool'),
                 ('Joined', lambda u: u.date_joined.strftime('%Y-%m-%d'))],
        search_fields=['email', 'first_name', 'last_name', 'phone'], can_add=False, can_edit=False,
        can_delete=False, toggle_guard=user_guard, empty_text='No customers yet.',
        sort_choices=[('newest', 'Newest first', ('-date_joined', '-id'))]), name='manage_user_list'),
    path('users/<int:pk>/toggle/', ToggleActiveView.as_view(
        model=User, url_base='user', nav_section='users', guard=user_guard), name='manage_user_toggle'),
]
