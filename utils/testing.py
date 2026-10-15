"""Factories shared by the test suites."""
from decimal import Decimal

from account_module.models import User
from product_module.models import Brand, Category, ColorOption, Product, ProductVariant, StorageOption


def make_product(name='Test Phone', price='500.00', stock=5, sale=None, active=True, brand=None, category=None,
                 storage='128GB', color='Black', **extra):
    brand = brand or Brand.objects.get_or_create(name='TestBrand')[0]
    category = category or Category.objects.get_or_create(name='Smartphones')[0]
    product = Product.objects.create(name=name, brand=brand, category=category, is_active=active, **extra)
    storage_option = StorageOption.objects.get_or_create(label=storage)[0]
    color_option = ColorOption.objects.get_or_create(name=color)[0]
    variant = ProductVariant.objects.create(
        product=product, storage=storage_option, color=color_option, price=Decimal(price),
        discount_price=Decimal(sale) if sale else None, stock=stock)
    return product, variant


def make_user(email='customer@example.com', password='S3cure-pass-123', staff=False, **extra):
    user = User(username=email, email=email, is_staff=staff, **extra)
    user.set_password(password)
    user.save()
    return user


REGISTER_DATA = {
    'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@example.com',
    'password': 'S3cure-pass-123', 'confirm_password': 'S3cure-pass-123', 'phone': '+1 555 0100',
    'country': 'Testland', 'state': 'Test State', 'city': 'Test City', 'street_address': '1 Test Road',
    'postal_code': '12345',
}
