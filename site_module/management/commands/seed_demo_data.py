"""
Creates sample content: brands, categories, storage/color options, 8 sample products with versions
and images, home page sections, menu, footer and content pages.

Safe to run repeatedly: every record is looked up by a stable key (slug / name / internal name) and
existing records are never modified or duplicated, so edits made in /manage/ are preserved.
All prices and specifications are SAMPLE values; change or delete them from the panel.
"""
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from product_module.models import (
    Brand, Category, ColorOption, Product, ProductImage, ProductVariant, StorageOption,
)
from site_module.models import (
    AppearanceSetting, ContentPage, FooterColumn, FooterLink, FooterSetting, HomeSection, NavLink,
    SectionItem, SiteSetting, SocialLink,
)

SAMPLE_DIR = Path(settings.BASE_DIR) / 'sample_media'

STORAGES = [('64GB', 10), ('128GB', 20), ('256GB', 30), ('512GB', 40), ('1TB', 50)]
COLORS = [
    ('Black', '#111111'), ('Silver', '#c0c0c0'), ('Blue', '#4f7fd6'), ('White', '#f5f5f5'),
    ('Titanium Gray', '#8a8a86'), ('Navy', '#1f2a44'), ('Lavender', '#b8a9e8'),
    ('Purple', '#7a5fc4'), ('Graphite', '#3a3a3c'),
]

SAMPLE_NOTE = 'Sample product shown for demonstration. Replace this text from the manager panel.'

# slug-able name, brand, category, short description, specs, flags, variants (storage, color, price, sale, stock)
PRODUCTS = [
    {
        'name': 'Apple iPhone 16', 'brand': 'Apple', 'category': 'Smartphones', 'image': 'apple-iphone-16',
        'short': 'Everyday flagship with a bright display and a dual camera system.',
        'specs': {'operating_system': 'iOS', 'ram': '8GB', 'screen_size': '6.1 inch', 'processor': 'Sample chip',
                  'camera': 'Dual rear camera, front camera', 'connectivity': '5G, Wi-Fi, Bluetooth, USB-C'},
        'flags': {'is_featured': True, 'is_bestseller_pick': True},
        'variants': [('128GB', 'Black', '799.00', None, 25), ('128GB', 'Blue', '799.00', None, 12),
                     ('256GB', 'Blue', '899.00', '859.00', 8), ('512GB', 'White', '1099.00', None, 0)],
    },
    {
        'name': 'Apple iPhone 16 Pro', 'brand': 'Apple', 'category': 'Smartphones', 'image': 'apple-iphone-16-pro',
        'short': 'Pro-level performance with a triple camera system.',
        'specs': {'operating_system': 'iOS', 'ram': '8GB', 'screen_size': '6.3 inch', 'processor': 'Sample chip',
                  'camera': 'Triple rear camera, front camera', 'connectivity': '5G, Wi-Fi, Bluetooth, USB-C'},
        'flags': {'is_featured': True, 'is_bestseller_pick': True},
        'variants': [('256GB', 'Titanium Gray', '1099.00', None, 10), ('512GB', 'Titanium Gray', '1299.00', None, 6),
                     ('1TB', 'Black', '1499.00', '1449.00', 3)],
    },
    {
        'name': 'Samsung Galaxy S25', 'brand': 'Samsung', 'category': 'Smartphones', 'image': 'samsung-galaxy-s25',
        'short': 'Compact Android flagship with a vivid AMOLED display.',
        'specs': {'operating_system': 'Android', 'ram': '12GB', 'screen_size': '6.2 inch', 'processor': 'Sample chip',
                  'camera': 'Triple rear camera, front camera', 'connectivity': '5G, Wi-Fi, Bluetooth, USB-C'},
        'flags': {'is_featured': True, 'is_bestseller_pick': True},
        'variants': [('128GB', 'Navy', '799.00', '749.00', 18), ('256GB', 'Navy', '859.00', None, 9),
                     ('256GB', 'Silver', '859.00', None, 5)],
    },
    {
        'name': 'Samsung Galaxy A56', 'brand': 'Samsung', 'category': 'Smartphones', 'image': 'samsung-galaxy-a56',
        'short': 'Great value mid-range phone with a big battery.',
        'specs': {'operating_system': 'Android', 'ram': '8GB', 'screen_size': '6.7 inch', 'processor': 'Sample chip',
                  'camera': 'Triple rear camera, front camera', 'battery_capacity': '5000 mAh',
                  'connectivity': '5G, Wi-Fi, Bluetooth, USB-C'},
        'flags': {'is_bestseller_pick': True},
        'variants': [('128GB', 'Lavender', '449.00', None, 30), ('256GB', 'Black', '499.00', '469.00', 14)],
    },
    {
        'name': 'Apple iPad Air', 'brand': 'Apple', 'category': 'Tablets', 'image': 'apple-ipad-air',
        'short': 'Light and powerful tablet for work, school and play.',
        'specs': {'operating_system': 'iPadOS', 'ram': '8GB', 'screen_size': '11 inch', 'processor': 'Sample chip',
                  'camera': 'Rear and front camera', 'connectivity': 'Wi-Fi, Bluetooth, USB-C'},
        'flags': {'is_featured': True},
        'variants': [('128GB', 'Purple', '599.00', None, 15), ('256GB', 'Purple', '699.00', '669.00', 7),
                     ('256GB', 'Silver', '699.00', None, 0)],
    },
    {
        'name': 'Apple iPad Pro', 'brand': 'Apple', 'category': 'Tablets', 'image': 'apple-ipad-pro',
        'short': 'The most capable tablet with an ultra-thin design.',
        'specs': {'operating_system': 'iPadOS', 'ram': '16GB', 'screen_size': '13 inch', 'processor': 'Sample chip',
                  'camera': 'Rear and front camera', 'connectivity': 'Wi-Fi, Bluetooth, Thunderbolt / USB-C'},
        'flags': {'is_bestseller_pick': False},
        'variants': [('256GB', 'Black', '1099.00', None, 6), ('512GB', 'Black', '1299.00', None, 4),
                     ('1TB', 'Silver', '1699.00', None, 2)],
    },
    {
        'name': 'Samsung Galaxy Tab S10', 'brand': 'Samsung', 'category': 'Tablets', 'image': 'samsung-galaxy-tab-s10',
        'short': 'Premium Android tablet with a large AMOLED screen and stylus.',
        'specs': {'operating_system': 'Android', 'ram': '12GB', 'screen_size': '12.4 inch', 'processor': 'Sample chip',
                  'camera': 'Rear and front camera', 'battery_capacity': '10090 mAh',
                  'connectivity': 'Wi-Fi, Bluetooth, USB-C'},
        'flags': {'is_featured': True},
        'variants': [('256GB', 'Graphite', '999.00', '949.00', 9), ('512GB', 'Graphite', '1119.00', None, 5)],
    },
    {
        'name': 'Samsung Galaxy Tab A9', 'brand': 'Samsung', 'category': 'Tablets', 'image': 'samsung-galaxy-tab-a9',
        'short': 'Affordable family tablet for streaming, reading and learning.',
        'specs': {'operating_system': 'Android', 'ram': '4GB', 'screen_size': '8.7 inch', 'processor': 'Sample chip',
                  'camera': 'Rear and front camera', 'battery_capacity': '5100 mAh',
                  'connectivity': 'Wi-Fi, Bluetooth, USB-C'},
        'flags': {},
        'variants': [('64GB', 'Silver', '149.00', None, 40), ('128GB', 'Graphite', '189.00', '169.00', 22)],
    },
]


def attach(instance, field_name, relative_path):
    """Save a sample image into the media folder, only when the field is still empty."""
    if getattr(instance, field_name):
        return
    path = SAMPLE_DIR / relative_path
    if not path.exists():
        return
    with path.open('rb') as handle:
        getattr(instance, field_name).save(path.name, File(handle), save=True)


class Command(BaseCommand):
    help = 'Create sample products, sections, footer and pages (safe to run more than once).'

    @transaction.atomic
    def handle(self, *args, **options):
        counts = {'created': 0}

        def made(created):
            if created:
                counts['created'] += 1

        site = SiteSetting.load()
        if not site.contact_email:
            site.contact_email = 'support@example.com'
            site.contact_phone = '+1 555 0100'
            site.address = '123 Sample Street\nSample City'
            site.save()
        AppearanceSetting.load()
        FooterSetting.load()

        brands = {}
        for index, (name, desc) in enumerate([
            ('Apple', 'Premium smartphones and tablets.'), ('Samsung', 'Android phones and tablets for everyone.')]):
            brand, created = Brand.objects.get_or_create(
                name=name, defaults={'description': desc, 'sort_order': (index + 1) * 10, 'logo_alt': f'{name} logo'})
            made(created)
            brands[name] = brand

        categories = {}
        for index, (name, slug, desc) in enumerate([
            ('Smartphones', 'smartphones', 'The latest phones from top brands.'),
            ('Tablets', 'tablets', 'Tablets for work, study and entertainment.')]):
            category, created = Category.objects.get_or_create(
                name=name, defaults={'slug': slug, 'description': desc, 'sort_order': (index + 1) * 10,
                                     'image_alt': name})
            made(created)
            attach(category, 'image', f'categories/{slug}.jpg')
            categories[name] = category

        storages = {}
        for label, order in STORAGES:
            storages[label], created = StorageOption.objects.get_or_create(label=label, defaults={'sort_order': order})
            made(created)
        colors = {}
        for index, (name, hex_code) in enumerate(COLORS):
            colors[name], created = ColorOption.objects.get_or_create(
                name=name, defaults={'hex_code': hex_code, 'sort_order': (index + 1) * 10})
            made(created)

        for index, spec in enumerate(PRODUCTS):
            product, created = Product.objects.get_or_create(
                name=spec['name'],
                defaults=dict(
                    brand=brands[spec['brand']], category=categories[spec['category']],
                    short_description=spec['short'], description=f"{spec['short']}\n\n{SAMPLE_NOTE}",
                    image_alt=spec['name'], home_sort_order=(index + 1) * 10,
                    model_number=f'SAMPLE-{index + 1:03d}', warranty='12 months (sample)',
                    meta_title=spec['name'], meta_description=spec['short'],
                    **spec['flags'], **spec['specs']),
            )
            made(created)
            if not created:
                continue
            attach(product, 'image', f"products/{spec['image']}.jpg")
            path_back = SAMPLE_DIR / f"products/{spec['image']}-back.jpg"
            if path_back.exists():
                gallery = ProductImage(product=product, alt_text=f"{spec['name']} - back view", sort_order=10)
                with path_back.open('rb') as handle:
                    gallery.image.save(path_back.name, File(handle), save=True)
            for position, (storage, color, price, sale, stock) in enumerate(spec['variants'], start=1):
                ProductVariant.objects.get_or_create(
                    product=product, storage=storages[storage], color=colors[color],
                    defaults={'price': Decimal(price), 'discount_price': Decimal(sale) if sale else None,
                              'stock': stock, 'sku': f'SMP{index + 1:02d}-{position}', 'sort_order': position * 10})

        # ---- home page sections ------------------------------------------------------------------
        def section(internal_name, **fields):
            obj, created = HomeSection.objects.get_or_create(internal_name=internal_name, defaults=fields)
            made(created)
            return obj, created

        hero, created = section(
            'Home - Hero', section_type='hero', sort_order=10,
            title='Find your next phone or tablet', subtitle='Top brands, clear prices and fast delivery.',
            button_text='Shop now', button_url='/products/', image_alt='Phones and tablets', text_align='left')
        if created:
            attach(hero, 'image', 'banners/hero.jpg')
            attach(hero, 'mobile_image', 'banners/hero-mobile.jpg')
        section('Home - Featured categories', section_type='featured_categories', sort_order=20,
                title='Shop by category', subtitle='Choose what you are looking for.', items_count=6,
                image_aspect_ratio='4:3')
        section('Home - New arrivals', section_type='new_arrivals', sort_order=30, title='New arrivals',
                subtitle='The newest products in our store.', button_text='View all', button_url='/products/',
                items_count=8)
        section('Home - Best sellers', section_type='best_sellers', sort_order=40, title='Best sellers',
                subtitle='Our most popular picks.', items_count=4)
        promo, created = section(
            'Home - Promo', section_type='promo', sort_order=50, title='Upgrade and save',
            subtitle='Selected versions are on sale.', body='Look for the Sale badge on product cards.',
            button_text='See deals', button_url='/products/?featured=1', image_alt='Smartphone back view',
            background_color='#fff7ed', text_color='#431407')
        if created:
            attach(promo, 'image', 'banners/promo.jpg')
        section('Home - Featured products', section_type='featured_products', sort_order=60,
                title='Featured products', subtitle='Hand-picked by our team.', items_count=4)
        benefits, created = section('Home - Benefits', section_type='benefits', sort_order=70,
                                    title='Why shop with us')
        if created:
            for position, (icon, title, text) in enumerate([
                ('\U0001F69A', 'Fast delivery', 'Quick and tracked shipping.'),
                ('\U0001F6E1', 'Warranty included', 'Every device comes with a warranty.'),
                ('\U0001F4B3', 'Secure shopping', 'Your account and data are protected.'),
                ('\U0001F4AC', 'Friendly support', 'We are here to help you choose.')], start=1):
                SectionItem.objects.create(section=benefits, icon=icon, title=title, text=text,
                                           sort_order=position * 10)
        about, created = section(
            'Home - About', section_type='about', sort_order=80, title='About our store',
            body='We sell carefully selected smartphones and tablets from trusted brands.\n\n'
                 'Edit this text, the image and the button from the manager panel.',
            button_text='Learn more', button_url='/pages/about-us/', image_alt='Tablet and phone')
        if created:
            attach(about, 'image', 'banners/about.jpg')

        # ---- menu, pages, footer -----------------------------------------------------------------
        for position, (title, url) in enumerate([('Deals', '/products/?featured=1'), ('About', '/pages/about-us/')], 1):
            _obj, created = NavLink.objects.get_or_create(title=title, defaults={'url': url, 'sort_order': position * 10})
            made(created)

        pages = [
            ('About Us', 'about-us', 'We are a sample store selling smartphones and tablets.\n\n'
                                     'Edit this page in the manager panel under Content pages.'),
            ('Shipping & Returns', 'shipping-returns', 'Describe your delivery times and return policy here.'),
            ('Contact', 'contact', 'Write how customers can reach you. Contact details from Store settings '
                                   'are also shown in the footer.'),
        ]
        for title, slug, body in pages:
            _obj, created = ContentPage.objects.get_or_create(slug=slug, defaults={'title': title, 'body': body})
            made(created)

        footer = FooterSetting.load()
        if not footer.title and not footer.description:
            footer.title = site.store_name
            footer.description = site.tagline
            footer.save()
        shop, created = FooterColumn.objects.get_or_create(title='Shop', defaults={'sort_order': 30})
        if created:
            made(True)
            for position, (title, url) in enumerate([('All products', '/products/'), ('Smartphones', '/products/category/smartphones/'),
                                                     ('Tablets', '/products/category/tablets/')], 1):
                FooterLink.objects.create(column=shop, title=title, url=url, sort_order=position * 10)
        info, created = FooterColumn.objects.get_or_create(title='Information', defaults={'sort_order': 40})
        if created:
            made(True)
            for position, (title, url) in enumerate([('About Us', '/pages/about-us/'),
                                                     ('Shipping & Returns', '/pages/shipping-returns/'),
                                                     ('Contact', '/pages/contact/')], 1):
                FooterLink.objects.create(column=info, title=title, url=url, sort_order=position * 10)
        for position, (platform, url) in enumerate([('instagram', 'https://www.instagram.com/'),
                                                    ('youtube', 'https://www.youtube.com/')], 1):
            _obj, created = SocialLink.objects.get_or_create(platform=platform, defaults={'url': url, 'sort_order': position * 10})
            made(created)

        self.stdout.write(self.style.SUCCESS(
            f'Sample data ready ({counts["created"]} new records). Existing records were left untouched.'))
