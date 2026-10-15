import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from product_module.models import Product, ProductVariant
from utils.testing import make_product

from .appearance import PRESETS, build_theme_css
from .models import AppearanceSetting, ContentPage, FooterColumn, FooterLink, FooterSetting, HomeSection, NavLink


class AppearanceCssTests(TestCase):
    def test_css_contains_saved_values(self):
        appearance = AppearanceSetting.load()
        appearance.primary_color = '#ff0000'
        appearance.font_size_body = 18
        appearance.save()
        css = build_theme_css(AppearanceSetting.load())
        self.assertIn('--c-primary:#ff0000', css)
        self.assertIn('--fs-body:18px', css)

    def test_invalid_stored_values_fall_back_to_safe_defaults(self):
        appearance = AppearanceSetting.load()
        appearance.primary_color = 'red;}</style><script>'
        appearance.font_size_body = 999
        css = build_theme_css(appearance)
        self.assertNotIn('<script>', css)
        self.assertIn('--fs-body:22px', css)

    def test_all_presets_are_complete(self):
        base = set(PRESETS['modern_blue']['values'])
        for key, preset in PRESETS.items():
            self.assertEqual(set(preset['values']), base, key)

    def test_pages_include_theme_variables(self):
        response = self.client.get(reverse('home_page'))
        self.assertContains(response, '--c-primary:')


class HomePageTests(TestCase):
    def test_empty_site_renders(self):
        self.assertEqual(self.client.get(reverse('home_page')).status_code, 200)

    def test_inactive_section_is_hidden_and_order_is_respected(self):
        HomeSection.objects.create(internal_name='B', section_type='custom', title='Second Block', sort_order=20)
        HomeSection.objects.create(internal_name='A', section_type='custom', title='First Block', sort_order=10)
        HomeSection.objects.create(internal_name='C', section_type='custom', title='Hidden Block',
                                   sort_order=5, is_active=False)
        html = self.client.get(reverse('home_page')).content.decode()
        self.assertNotIn('Hidden Block', html)
        self.assertLess(html.index('First Block'), html.index('Second Block'))

    def test_new_arrivals_and_best_sellers_sections(self):
        product, _v = make_product(name='Shiny Phone', is_bestseller_pick=True)
        HomeSection.objects.create(internal_name='N', section_type='new_arrivals', title='New stuff')
        HomeSection.objects.create(internal_name='S', section_type='best_sellers', title='Top stuff')
        response = self.client.get(reverse('home_page'))
        self.assertContains(response, 'New stuff')
        self.assertContains(response, 'Top stuff')
        self.assertContains(response, 'Shiny Phone')

    def test_section_with_missing_image_file_does_not_break(self):
        section = HomeSection.objects.create(internal_name='H', section_type='hero', title='Hello')
        section.image.name = 'sections/does-not-exist.jpg'
        section.save()
        self.assertEqual(self.client.get(reverse('home_page')).status_code, 200)


class FooterAndPagesTests(TestCase):
    def test_footer_is_rendered_from_database(self):
        column = FooterColumn.objects.create(title='Help Column')
        FooterLink.objects.create(column=column, title='FAQ Link', url='/pages/faq/')
        footer = FooterSetting.load()
        footer.copyright_text = 'Copyright {year} Example'
        footer.save()
        response = self.client.get(reverse('home_page'))
        self.assertContains(response, 'Help Column')
        self.assertContains(response, 'FAQ Link')
        self.assertContains(response, 'Copyright 20')

    def test_hidden_footer_part_is_not_rendered(self):
        column = FooterColumn.objects.create(title='Secret Column')
        FooterLink.objects.create(column=column, title='x', url='/x/')
        footer = FooterSetting.load()
        footer.show_links = False
        footer.save()
        self.assertNotContains(self.client.get(reverse('home_page')), 'Secret Column')

    def test_menu_links(self):
        NavLink.objects.create(title='Deals Link', url='/products/')
        NavLink.objects.create(title='Off Link', url='/products/', is_active=False)
        response = self.client.get(reverse('home_page'))
        self.assertContains(response, 'Deals Link')
        self.assertNotContains(response, 'Off Link')

    def test_content_page_and_inactive_page(self):
        ContentPage.objects.create(title='About', slug='about', body='Hello <b>there</b>')
        ContentPage.objects.create(title='Old', slug='old', body='x', is_active=False)
        response = self.client.get(reverse('content_page', args=['about']))
        self.assertContains(response, 'Hello &lt;b&gt;there&lt;/b&gt;')
        self.assertEqual(self.client.get(reverse('content_page', args=['old'])).status_code, 404)


class SeedCommandTests(TestCase):
    def test_seed_is_repeatable_and_creates_no_duplicates(self):
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                call_command('seed_demo_data', verbosity=0)
                first = (Product.objects.count(), ProductVariant.objects.count(), HomeSection.objects.count())
                call_command('seed_demo_data', verbosity=0)
                second = (Product.objects.count(), ProductVariant.objects.count(), HomeSection.objects.count())
                self.assertEqual(first, second)
                self.assertEqual(first[0], 8)
                self.assertTrue(Product.objects.filter(category__name='Tablets').exists())
                self.assertTrue(Product.objects.filter(category__name='Smartphones').exists())
                response = self.client.get(reverse('home_page'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Best sellers')
