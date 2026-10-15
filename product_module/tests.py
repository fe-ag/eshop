from django.test import TestCase
from django.urls import reverse

from utils.testing import make_product

from . import services
from .models import Brand, Category, ColorOption, ProductVariant, StorageOption


class ProductPageTests(TestCase):
    def test_detail_shows_storage_and_color(self):
        product, _v = make_product(storage='256GB', color='Blue')
        response = self.client.get(product.get_absolute_url())
        self.assertContains(response, 'Storage Capacity')
        self.assertContains(response, '256GB')
        self.assertContains(response, 'Blue')

    def test_inactive_product_is_not_public(self):
        product, _v = make_product(active=False)
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)

    def test_product_without_image_still_renders(self):
        product, _v = make_product()
        self.assertContains(self.client.get(product.get_absolute_url()), 'placeholder')

    def test_inactive_brand_hides_products(self):
        product, _v = make_product()
        Brand.objects.filter(pk=product.brand_id).update(is_active=False)
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)

    def test_slug_is_unique(self):
        a, _ = make_product(name='Same Name')
        b, _ = make_product(name='Same Name', storage='64GB')
        self.assertNotEqual(a.slug, b.slug)


class ListAndFilterTests(TestCase):
    def setUp(self):
        self.cheap, self.cheap_v = make_product(name='Cheap Phone', price='100.00', storage='64GB', color='Black')
        self.mid, self.mid_v = make_product(name='Mid Phone', price='500.00', sale='450.00', storage='128GB', color='Blue')
        tablets = Category.objects.create(name='Tablets')
        self.tablet, self.tablet_v = make_product(name='Big Tablet', price='900.00', storage='256GB',
                                                  color='Blue', category=tablets, stock=0)

    def names(self, **params):
        response = self.client.get(reverse('product_list'), params)
        self.assertEqual(response.status_code, 200)
        return [p.name for p in response.context['products']]

    def test_search_by_name(self):
        self.assertEqual(self.names(q='Cheap'), ['Cheap Phone'])

    def test_filter_by_category(self):
        self.assertEqual(self.names(category=self.tablet.category_id), ['Big Tablet'])

    def test_filter_by_storage_and_color_same_variant(self):
        extra = ProductVariant.objects.create(
            product=self.cheap, storage=StorageOption.objects.get(label='128GB'),
            color=ColorOption.objects.get(name='Blue'), price='120.00', stock=2)
        self.assertEqual(self.names(storage=extra.storage_id, color=extra.color_id).count('Cheap Phone'), 1)
        # 64GB exists on Cheap Phone (Black) but never together with Blue
        self.assertNotIn('Cheap Phone', self.names(storage=self.cheap_v.storage_id, color=extra.color_id))

    def test_price_range_uses_sale_price(self):
        self.assertEqual(self.names(min_price='440', max_price='460'), ['Mid Phone'])

    def test_in_stock_filter(self):
        self.assertNotIn('Big Tablet', self.names(in_stock='1'))

    def test_sort_by_price(self):
        self.assertEqual(self.names(sort='price_asc'), ['Cheap Phone', 'Mid Phone', 'Big Tablet'])
        self.assertEqual(self.names(sort='price_desc'), ['Big Tablet', 'Mid Phone', 'Cheap Phone'])

    def test_invalid_parameters_are_ignored(self):
        self.assertEqual(len(self.names(category='abc', min_price='x', max_price='-5', storage='q')), 3)

    def test_no_results_message(self):
        response = self.client.get(reverse('product_list'), {'q': 'nothing-matches-this'})
        self.assertContains(response, 'No products found')

    def test_category_page(self):
        response = self.client.get(reverse('product_category', args=[self.tablet.category.slug]))
        self.assertEqual([p.name for p in response.context['products']], ['Big Tablet'])

    def test_best_sellers_use_real_sales_then_manager_picks(self):
        self.assertEqual(services.best_sellers(4), [])
        self.mid.is_bestseller_pick = True
        self.mid.save()
        self.assertEqual([p.name for p in services.best_sellers(4)], ['Mid Phone'])
        self.cheap.sales_count = 7
        self.cheap.save()
        self.assertEqual([p.name for p in services.best_sellers(4)], ['Cheap Phone'])
