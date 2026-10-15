import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from product_module.models import Brand, Category, ColorOption, Product, StorageOption
from site_module.models import AppearanceSetting, HomeSection, SiteSetting
from utils.testing import make_product, make_user


def product_post_data(brand, category, storage, color, **overrides):
    data = {
        'name': 'New Phone', 'slug': '', 'brand': brand.pk, 'category': category.pk,
        'short_description': 'Short', 'description': 'Long', 'image_alt': '', 'is_active': 'on',
        'show_on_home': 'on', 'home_sort_order': '100', 'sales_count': '0',
        'model_number': '', 'operating_system': '', 'processor': '', 'ram': '', 'screen_size': '',
        'battery_capacity': '', 'camera': '', 'connectivity': '', 'warranty': '',
        'meta_title': '', 'meta_description': '',
        'variants-TOTAL_FORMS': '1', 'variants-INITIAL_FORMS': '0', 'variants-MIN_NUM_FORMS': '1',
        'variants-MAX_NUM_FORMS': '1000',
        'variants-0-storage': storage.pk, 'variants-0-color': color.pk, 'variants-0-price': '100.00',
        'variants-0-stock': '3', 'variants-0-is_active': 'on', 'variants-0-sort_order': '100',
        'gallery-TOTAL_FORMS': '0', 'gallery-INITIAL_FORMS': '0', 'gallery-MIN_NUM_FORMS': '0',
        'gallery-MAX_NUM_FORMS': '1000',
    }
    data.update(overrides)
    return data


def png_bytes():
    buffer = BytesIO()
    Image.new('RGB', (20, 20), 'red').save(buffer, 'PNG')
    return buffer.getvalue()


class AccessControlTests(TestCase):
    def setUp(self):
        self.customer = make_user('customer@example.com')
        self.staff = make_user('staff@example.com', staff=True)
        self.product, _v = make_product()

    def test_anonymous_is_redirected_to_manager_login(self):
        response = self.client.get('/manage/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/manage/login/'))

    def test_customer_cannot_open_panel_pages(self):
        self.client.force_login(self.customer)
        for url in ['/manage/', '/manage/products/', '/manage/appearance/', '/manage/site/', '/manage/users/']:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_customer_cannot_run_manager_actions(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(f'/manage/products/{self.product.pk}/delete/').status_code, 403)
        self.assertEqual(self.client.post(f'/manage/products/{self.product.pk}/toggle/').status_code, 403)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_staff_can_open_dashboard_and_lists(self):
        self.client.force_login(self.staff)
        for url in ['/manage/', '/manage/products/', '/manage/categories/', '/manage/brands/', '/manage/storage/',
                    '/manage/colors/', '/manage/sections/', '/manage/menu/', '/manage/pages/',
                    '/manage/footer/', '/manage/footer-columns/', '/manage/social/', '/manage/appearance/',
                    '/manage/fonts/', '/manage/site/', '/manage/users/', '/manage/products/add/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_manager_login_rejects_customers_and_accepts_staff(self):
        response = self.client.post('/manage/login/', {'email': 'customer@example.com', 'password': 'S3cure-pass-123'})
        self.assertContains(response, 'does not have access')
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post('/manage/login/', {'email': 'staff@example.com', 'password': 'S3cure-pass-123'})
        self.assertRedirects(response, '/manage/')

    def test_django_admin_is_not_installed(self):
        self.assertEqual(self.client.get('/admin/').status_code, 404)


class ProductManagementTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff@example.com', staff=True)
        self.client.force_login(self.staff)
        self.brand = Brand.objects.create(name='Acme')
        self.category = Category.objects.create(name='Smartphones')
        self.storage = StorageOption.objects.create(label='128GB')
        self.color = ColorOption.objects.create(name='Black', hex_code='#000000')

    def test_create_product_with_variant(self):
        response = self.client.post('/manage/products/add/', product_post_data(
            self.brand, self.category, self.storage, self.color))
        self.assertRedirects(response, '/manage/products/')
        product = Product.objects.get(name='New Phone')
        self.assertEqual(product.slug, 'new-phone')
        self.assertEqual(product.variants.count(), 1)

    def test_product_needs_at_least_one_variant(self):
        data = product_post_data(self.brand, self.category, self.storage, self.color)
        data['variants-TOTAL_FORMS'] = '0'
        response = self.client.post('/manage/products/add/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name='New Phone').exists())

    def test_sale_price_must_be_lower(self):
        data = product_post_data(self.brand, self.category, self.storage, self.color,
                                 **{'variants-0-discount_price': '150.00'})
        response = self.client.post('/manage/products/add/', data)
        self.assertContains(response, 'lower than the regular price')

    def test_upload_rejects_non_image(self):
        data = product_post_data(self.brand, self.category, self.storage, self.color)
        data['image'] = SimpleUploadedFile('evil.php', b'<?php echo 1;', content_type='image/png')
        response = self.client.post('/manage/products/add/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name='New Phone').exists())

    def test_upload_accepts_png(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            data = product_post_data(self.brand, self.category, self.storage, self.color)
            data['image'] = SimpleUploadedFile('phone.png', png_bytes(), content_type='image/png')
            response = self.client.post('/manage/products/add/', data)
            self.assertRedirects(response, '/manage/products/')
            self.assertTrue(Product.objects.get(name='New Phone').image.name.endswith('.png'))

    def test_toggle_active(self):
        product, _v = make_product(brand=self.brand, category=self.category)
        self.client.post(f'/manage/products/{product.pk}/toggle/')
        product.refresh_from_db()
        self.assertFalse(product.is_active)

    def test_delete_product(self):
        product, _v = make_product(brand=self.brand, category=self.category)
        self.assertEqual(self.client.get(f'/manage/products/{product.pk}/delete/').status_code, 200)
        self.client.post(f'/manage/products/{product.pk}/delete/')
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_brand_with_products_cannot_be_deleted(self):
        make_product(brand=self.brand, category=self.category)
        self.client.post(f'/manage/brands/{self.brand.pk}/delete/')
        self.assertTrue(Brand.objects.filter(pk=self.brand.pk).exists())
        self.assertContains(self.client.get(f'/manage/brands/{self.brand.pk}/delete/'), 'cannot be deleted')

    def test_empty_brand_can_be_deleted(self):
        empty = Brand.objects.create(name='Empty')
        self.client.post(f'/manage/brands/{empty.pk}/delete/')
        self.assertFalse(Brand.objects.filter(pk=empty.pk).exists())

    def test_move_category_up_and_down(self):
        other = Category.objects.create(name='Tablets', sort_order=200)
        self.category.sort_order = 100
        self.category.save()
        self.client.post(f'/manage/categories/{other.pk}/move/up/')
        self.assertEqual([c.name for c in Category.objects.all()], ['Tablets', 'Smartphones'])

    def test_search_in_product_list(self):
        make_product(name='Findable Phone', brand=self.brand, category=self.category)
        make_product(name='Other Thing', brand=self.brand, category=self.category, storage='64GB')
        response = self.client.get('/manage/products/', {'q': 'Findable'})
        self.assertContains(response, 'Findable Phone')
        self.assertNotContains(response, 'Other Thing')


class AppearanceAndContentTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff@example.com', staff=True)
        self.client.force_login(self.staff)

    def appearance_data(self, **overrides):
        form_fields = AppearanceSetting._meta.get_fields()
        data = {}
        appearance = AppearanceSetting.load()
        for field in form_fields:
            if field.concrete and not field.primary_key and not field.is_relation:
                data[field.name] = getattr(appearance, field.name)
        data.update(overrides)
        return data

    def test_save_appearance_changes_storefront(self):
        response = self.client.post('/manage/appearance/', self.appearance_data(
            primary_color='#123456', font_size_body=19, action='save'))
        self.assertRedirects(response, '/manage/appearance/')
        self.assertContains(self.client.get('/'), '--c-primary:#123456')
        self.assertContains(self.client.get('/'), '--fs-body:19px')

    def test_out_of_range_size_is_rejected(self):
        response = self.client.post('/manage/appearance/', self.appearance_data(font_size_body=90, action='save'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AppearanceSetting.load().font_size_body, 16)

    def test_invalid_color_is_rejected(self):
        response = self.client.post('/manage/appearance/', self.appearance_data(primary_color='blue', action='save'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AppearanceSetting.load().primary_color, '#2563eb')

    def test_reset_appearance(self):
        settings = AppearanceSetting.load()
        settings.primary_color = '#abcdef'
        settings.save()
        self.client.post('/manage/appearance/', {'action': 'reset'})
        self.assertEqual(AppearanceSetting.load().primary_color, '#2563eb')

    def test_store_settings_and_reset(self):
        site = SiteSetting.load()
        site.store_name = 'Custom Shop'
        site.save()
        self.assertContains(self.client.get('/'), 'Custom Shop')
        self.client.post('/manage/site/', {'action': 'reset'})
        self.assertEqual(SiteSetting.load().store_name, 'TechStore')

    def test_create_section_and_toggle(self):
        response = self.client.post('/manage/sections/add/', {
            'internal_name': 'My block', 'section_type': 'custom', 'is_active': 'on', 'sort_order': '10',
            'title': 'Brand new block', 'items_count': '8', 'image_aspect_ratio': 'auto', 'image_fit': 'cover',
            'text_align': 'left', 'background_color': '#ffffff', 'text_color': '#111827',
            'items-TOTAL_FORMS': '0', 'items-INITIAL_FORMS': '0', 'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000'})
        self.assertRedirects(response, '/manage/sections/')
        section = HomeSection.objects.get(internal_name='My block')
        self.assertEqual(section.background_color, '')  # custom colors were not enabled
        self.assertContains(self.client.get('/'), 'Brand new block')
        self.client.post(f'/manage/sections/{section.pk}/toggle/')
        self.assertNotContains(self.client.get('/'), 'Brand new block')

    def test_users_list_hides_no_password_data(self):
        make_user('someone@example.com')
        response = self.client.get('/manage/users/')
        self.assertContains(response, 'someone@example.com')
        self.assertNotContains(response, 'pbkdf2')
