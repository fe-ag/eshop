from django.test import TestCase
from django.urls import reverse

from utils.testing import make_product, make_user

from .cart import CartService
from .models import Cart, CartItem


class GuestCartTests(TestCase):
    def setUp(self):
        self.product, self.variant = make_product(price='500.00', stock=3)

    def add(self, quantity=1, variant=None, **extra):
        data = {'variant_id': (variant or self.variant).pk, 'quantity': quantity}
        data.update(extra)
        return self.client.post(reverse('cart_add'), data)

    def test_guest_can_add_and_view(self):
        self.add(2)
        response = self.client.get(reverse('cart_page'))
        self.assertContains(response, 'Test Phone')
        self.assertEqual(self.client.session['cart'], {str(self.variant.pk): 2})

    def test_quantity_is_limited_by_stock(self):
        self.add(10)
        self.assertEqual(self.client.session['cart'][str(self.variant.pk)], 3)

    def test_invalid_quantity_is_rejected(self):
        self.add(-4)
        self.add('abc')
        self.assertFalse(self.client.session.get('cart'))

    def test_price_comes_from_database_not_from_request(self):
        self.add(1, price='1.00', unit_price='1.00')
        response = self.client.get(reverse('cart_page'))
        self.assertContains(response, '500.00')
        self.assertNotContains(response, '$1.00')

    def test_inactive_product_cannot_be_added(self):
        _p, inactive_variant = make_product(name='Hidden', active=False)
        self.add(1, variant=inactive_variant)
        self.assertFalse(self.client.session.get('cart'))

    def test_out_of_stock_cannot_be_added(self):
        _p, empty = make_product(name='Empty', stock=0, storage='256GB')
        self.add(1, variant=empty)
        self.assertFalse(self.client.session.get('cart'))

    def test_update_and_remove(self):
        self.add(1)
        self.client.post(reverse('cart_update'), {'variant_id': self.variant.pk, 'quantity': 2})
        self.assertEqual(self.client.session['cart'][str(self.variant.pk)], 2)
        self.client.post(reverse('cart_remove'), {'variant_id': self.variant.pk})
        self.assertFalse(self.client.session['cart'])

    def test_cart_endpoints_reject_get(self):
        self.assertEqual(self.client.get(reverse('cart_add')).status_code, 405)

    def test_checkout_requires_login(self):
        self.add(1)
        response = self.client.get(reverse('checkout_page'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('account_login'), response['Location'])
        self.assertIn('next=', response['Location'])


class UserCartTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.product, self.variant = make_product(stock=5)

    def test_guest_cart_is_merged_on_login(self):
        self.client.post(reverse('cart_add'), {'variant_id': self.variant.pk, 'quantity': 2})
        self.client.post(reverse('account_login'), {'email': self.user.email, 'password': 'S3cure-pass-123'})
        item = CartItem.objects.get(cart__user=self.user)
        self.assertEqual((item.variant_id, item.quantity), (self.variant.pk, 2))
        self.assertNotIn('cart', self.client.session)

    def test_logged_in_cart_is_stored_in_database(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add'), {'variant_id': self.variant.pk, 'quantity': 1})
        self.assertEqual(Cart.objects.get(user=self.user).items.count(), 1)

    def test_checkout_page_for_logged_in_user(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add'), {'variant_id': self.variant.pk, 'quantity': 1})
        response = self.client.get(reverse('checkout_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Online payment is not available')

    def test_stock_drop_adjusts_quantity_without_error(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add'), {'variant_id': self.variant.pk, 'quantity': 4})
        self.variant.stock = 1
        self.variant.save()
        response = self.client.get(reverse('cart_page'))
        self.assertContains(response, 'Only 1 available')

    def test_cart_service_total_uses_sale_price(self):
        _p, sale_variant = make_product(name='Sale Phone', price='100.00', sale='80.00', stock=5, storage='64GB')
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add'), {'variant_id': sale_variant.pk, 'quantity': 2})
        request = self.client.get(reverse('cart_page')).wsgi_request
        self.assertEqual(str(CartService(request).total()), '160.00')
